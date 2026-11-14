import os
import re
import shutil
import threading
from datetime import datetime
from docx import Document
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from core.agents import AgentOrchestrator
from data.database import GlossaryManager
from core.logging_helper import AppLogger

logger = AppLogger.get_instance()

# ── Chunk validation constants ──────────────────────────────────────────────
_MIN_LENGTH_RATIO = 0.30          # translated length must be ≥30% of source length
_MIN_ARABIC_RATIO = 0.30          # Arabic output needs ≥30% Arabic letters among all alphabetic chars
_REFUSAL_CHECK_CHARS = 120        # only inspect the first N characters for refusal phrases
_MAX_VALIDATION_ATTEMPTS = 2      # 1 initial + 1 extra validation retry (HTTP retries are in agents.py)


def _apply_rtl_to_paragraph(paragraph):
    """Configure a python-docx paragraph for Right-to-Left (Arabic) display."""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = paragraph._p.get_or_add_pPr()
    if pPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bidi") is None:
        pPr.append(OxmlElement("w:bidi"))


def _filter_glossary_for_chunk(glossary_manager, all_terms, chunk_text):
    """
    Filter glossary terms so only terms actually appearing in the current chunk
    are injected into the prompt. This speeds up local LLM prompt evaluation
    and dramatically improves glossary adherence on large glossaries.
    """
    if not all_terms:
        return ""
    chunk_lower = chunk_text.lower()
    matched = [
        t for t in all_terms
        if t.get("source") and t["source"].lower() in chunk_lower
    ]
    if not matched:
        return ""
    return glossary_manager.format_for_prompt(matched)


class TranslationEngine(threading.Thread):
    def __init__(self, input_file, output_dir, archive_dir, config_manager,
                 progress_callback, error_callback, completion_callback=None, persona="You are an elite translator."):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.archive_dir = archive_dir
        self.config_manager = config_manager
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        self.completion_callback = completion_callback
        self._stop_event = threading.Event()
        self.persona = persona

    def _split_long_paragraph(self, paragraph_text, words_per_chunk=400):
        """Split a single oversized paragraph at sentence boundaries."""
        words = paragraph_text.split()
        if not words:
            return []
        chunks = []
        current_chunk_words = []
        current_word_count = 0
        for word in words:
            current_chunk_words.append(word)
            current_word_count += 1
            if current_word_count >= words_per_chunk:
                last_punctuation_idx = -1
                for i in range(len(current_chunk_words) - 1, -1, -1):
                    if re.search(r'[.!?؟؛…]', current_chunk_words[i]):
                        last_punctuation_idx = i
                        break
                if last_punctuation_idx != -1:
                    split_at = last_punctuation_idx + 1
                    chunks.append(" ".join(current_chunk_words[:split_at]))
                    current_chunk_words = current_chunk_words[split_at:]
                    current_word_count = len(current_chunk_words)
                else:
                    chunks.append(" ".join(current_chunk_words))
                    current_chunk_words = []
                    current_word_count = 0
        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))
        return chunks

    def _split_into_word_chunks(self, text, words_per_chunk=400):
        """Split text into word-bounded chunks while preserving paragraph breaks."""
        if not text or not text.strip():
            return []

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p.strip() for p in re.split(r'\n+', normalized) if p.strip()]
        if not paragraphs:
            return []

        chunks = []
        current_paragraphs = []
        current_word_count = 0

        for para in paragraphs:
            para_words = para.split()
            para_word_len = len(para_words)

            # If a single paragraph is larger than words_per_chunk, flush current and split it
            if para_word_len >= words_per_chunk:
                if current_paragraphs:
                    chunks.append("\n\n".join(current_paragraphs))
                    current_paragraphs = []
                    current_word_count = 0
                chunks.extend(self._split_long_paragraph(para, words_per_chunk))
                continue

            if current_word_count + para_word_len > words_per_chunk and current_paragraphs:
                chunks.append("\n\n".join(current_paragraphs))
                current_paragraphs = [para]
                current_word_count = para_word_len
            else:
                current_paragraphs.append(para)
                current_word_count += para_word_len

        if current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs))

        return chunks

    def run(self):
        agent_orchestrator = None
        try:
            # Robust path resolution using unified helper
            from ui.asset_path import data_dir
            db_path = os.path.join(data_dir(), "glossary.db")

            glossary_manager = GlossaryManager(db_path)
            all_terms = glossary_manager.get_all_terms()

            if self.output_dir and not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            if self.archive_dir and not os.path.exists(self.archive_dir):
                os.makedirs(self.archive_dir, exist_ok=True)

            # Robust file reading: UTF-8-sig (BOM) → UTF-8 → CP1256 (Arabic Windows)
            content = None
            encoding_used = None
            for enc in ("utf-8-sig", "utf-8", "cp1256"):
                try:
                    with open(self.input_file, 'r', encoding=enc) as f:
                        content = f.read()
                    encoding_used = enc
                    break
                except UnicodeDecodeError:
                    continue
            if content is None:
                warning = (
                    "All encodings failed (UTF-8-sig, UTF-8, CP1256). "
                    "The file may be binary or use an unsupported encoding."
                )
                logger.error(warning)
                try:
                    self.error_callback(f"File read error: {warning}")
                except Exception:
                    pass
                return  # do not crash
            if encoding_used == "cp1256":
                logger.warning("File read using CP1256 (Arabic Windows) fallback — original may have BOM or UTF-8 issues")
            logger.info(f"File read successfully with encoding={encoding_used}")

            chunks = self._split_into_word_chunks(content)
            total_chunks = len(chunks)
            if total_chunks == 0:
                self.error_callback("Source file is empty.")
                return

            logger.info(f"Starting translation: {self.input_file} ({len(content)} chars, {total_chunks} chunks)")
            agent_orchestrator = AgentOrchestrator(self.config_manager)
            target_lang = (self.config_manager.get("target_lang") or "ar").strip().lower()

            # ── Stage 0: Run Style & Voice Profiler ONCE on the opening sample ──
            tone_info = {"instruction": ""}
            if not self._stop_event.is_set():
                try:
                    self.progress_callback(0, total_chunks, "Analyzing document style & narrative voice...")
                    style_blueprint = agent_orchestrator.run_style_profiler_agent(content[:1800], self.persona)
                    tone_info = {"instruction": style_blueprint}
                except Exception as style_err:
                    logger.warning(f"Style profiler skipped (continuing with default persona): {style_err}")

            translated_parts = []
            prev_context = ""
            failed_chunk_count = 0

            for idx, chunk in enumerate(chunks):
                if self._stop_event.is_set():
                    break

                current_idx = idx + 1
                # Smart per-chunk glossary filtering (only inject terms present in this chunk)
                chunk_glossary_rules = _filter_glossary_for_chunk(glossary_manager, all_terms, chunk)

                final_chunk = None
                validated = False
                reason = "unknown"

                for attempt in range(_MAX_VALIDATION_ATTEMPTS):
                    if self._stop_event.is_set():
                        break

                    retry_suffix = f" (retry {attempt})" if attempt > 0 else "..."

                    self.progress_callback(
                        current_idx, total_chunks,
                        f"Chunk {current_idx}/{total_chunks}: Drafting{retry_suffix}"
                    )
                    draft = agent_orchestrator.run_drafting_agent(
                        chunk, prev_context, chunk_glossary_rules, tone_info, self.persona
                    )
                    if self._stop_event.is_set():
                        break

                    self.progress_callback(
                        current_idx, total_chunks,
                        f"Chunk {current_idx}/{total_chunks}: Critiquing & Verifying{retry_suffix}"
                    )
                    criticized = agent_orchestrator.run_critic_agent(
                        draft, source_text=chunk, glossary_rules=chunk_glossary_rules, tone_info=tone_info
                    )
                    if self._stop_event.is_set():
                        break

                    self.progress_callback(
                        current_idx, total_chunks,
                        f"Chunk {current_idx}/{total_chunks}: Cultural & Voice Polish{retry_suffix}"
                    )
                    final_chunk = agent_orchestrator.run_cultural_expert_agent(
                        criticized, source_text=chunk, glossary_rules=chunk_glossary_rules, tone_info=tone_info
                    )

                    is_valid, reason = self._validate_chunk(chunk, final_chunk, target_lang)
                    if is_valid:
                        validated = True
                        break

                    # Smart stage-level recovery: if Agent 3 failed validation but Agent 2 or Agent 1 is valid,
                    # recover immediately without wasting another 3-agent round-trip!
                    crit_valid, _ = self._validate_chunk(chunk, criticized, target_lang)
                    if crit_valid:
                        logger.info(f"Chunk {current_idx}: recovered valid output from Critic stage")
                        final_chunk = criticized
                        validated = True
                        break

                    draft_valid, _ = self._validate_chunk(chunk, draft, target_lang)
                    if draft_valid:
                        logger.info(f"Chunk {current_idx}: recovered valid output from Draft stage")
                        final_chunk = draft
                        validated = True
                        break

                    logger.warning(f"Chunk {current_idx} failed validation on attempt {attempt + 1}: {reason}")

                if self._stop_event.is_set():
                    break

                if not validated:
                    failed_chunk_count += 1
                    logger.error(f"Chunk {current_idx} failed after all attempts: {reason}")
                    marker = f"[UNTRANSLATED CHUNK {current_idx}]"
                    translated_parts.append(f"{marker}\n{chunk}")
                    self.progress_callback(
                        current_idx, total_chunks,
                        f"⚠️ Chunk {current_idx}: validation failed after all attempts ({reason})"
                    )
                elif final_chunk is not None:
                    translated_parts.append(final_chunk)
                    sentences = re.split(r'(?<=[.!?؟؛])\s+', final_chunk)
                    prev_context = " ".join(sentences[-2:]) if len(sentences) > 1 else final_chunk[-300:]

            if not self._stop_event.is_set():
                # 1. Resolve output directory (respect configured output_dir, fallback to source folder)
                target_out_dir = self.output_dir if self.output_dir else os.path.dirname(self.input_file)
                os.makedirs(target_out_dir, exist_ok=True)

                base_name, _ = os.path.splitext(os.path.basename(self.input_file))
                output_filename = f"{base_name}_translated.docx"
                output_path = os.path.abspath(os.path.join(target_out_dir, output_filename))

                # 2. Write the translated content to a Word Document (preserving paragraphs and RTL for Arabic)
                doc = Document()
                is_rtl = (target_lang == "ar")
                for part in translated_parts:
                    for para_line in part.splitlines():
                        cleaned = para_line.strip()
                        if cleaned:
                            p = doc.add_paragraph(cleaned)
                            if is_rtl:
                                _apply_rtl_to_paragraph(p)
                doc.save(output_path)

                # 3. Archive the original file safely to prevent re-processing
                if self.archive_dir:
                    os.makedirs(self.archive_dir, exist_ok=True)
                    archive_dest = os.path.join(self.archive_dir, os.path.basename(self.input_file))
                    if os.path.exists(archive_dest):
                        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        archive_dest = os.path.join(self.archive_dir, f"{base_name}_{stamp}.txt")
                    shutil.move(self.input_file, archive_dest)

                # 4. Terminal Logging (Absolute Path)
                logger.info(f"Translation successful: {output_filename} ({len(translated_parts)} chunks)")
                print(f"✅ Translation successful! File saved to: {output_path}")
                if failed_chunk_count > 0:
                    logger.warning(f"Translation completed with {failed_chunk_count} failed chunk(s)")

                # 5. UI Notification via callbacks
                if failed_chunk_count > 0:
                    self.progress_callback(
                        total_chunks, total_chunks,
                        f"⚠️ Complete! {failed_chunk_count} chunk(s) could not be translated"
                    )
                else:
                    self.progress_callback(
                        total_chunks, total_chunks,
                        f"✅ Complete! Saved as {os.path.basename(output_path)}"
                    )

                if self.completion_callback:
                    self.completion_callback(output_path)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Engine failed (source file kept in place): {error_msg}")
            self.error_callback(f"Engine Error: {error_msg}")
        finally:
            if agent_orchestrator is not None:
                agent_orchestrator.close()

    def stop(self):
        self._stop_event.set()

    # ── Chunk validation ────────────────────────────────────────────

    def _validate_chunk(self, original_chunk, translated, target_lang=None):
        """Return (is_valid, reason) tuple.

        Checks for:
          1. Empty output
          2. Output far shorter than the input (MIN_LENGTH_RATIO threshold)
          3. Arabic output needs sufficient Arabic letters when target is 'ar'
          4. Refusal/summary phrases in first 120 chars (ignoring source phrases)
        """
        if not translated or not translated.strip():
            return False, "Empty translation output"

        # Length check
        ratio = len(translated) / len(original_chunk) if len(original_chunk) > 0 else 0
        if ratio < _MIN_LENGTH_RATIO:
            return False, f"Output too short (length ratio {ratio:.2%} < {_MIN_LENGTH_RATIO:.0%})"

        # Arabic letter proportion check (target language 'ar')
        if target_lang == 'ar':
            letters = [c for c in translated if c.isalpha()]
            if letters:
                arabic_letters = sum(1 for c in letters if '\u0600' <= c <= '\u06FF')
                arabic_ratio = arabic_letters / len(letters)
                if arabic_ratio < _MIN_ARABIC_RATIO:
                    return False, f"Arabic letter proportion too low ({arabic_ratio:.2%} < {_MIN_ARABIC_RATIO:.0%})"

        # Refusal / summary detection — only first 120 chars, skip phrases in source
        check_text = translated[:_REFUSAL_CHECK_CHARS].lower()
        source_lower = original_chunk.lower()
        refusal_phrases = [
            "i can't", "i cannot", "i'm unable", "i apologize",
            "i'm sorry", "i am sorry", "as an ai", "as an assistant",
            "please rephrase", "please provide",
            "this document contains", "this text contains",
            "the following", "here is a summary",
        ]
        for phrase in refusal_phrases:
            if phrase in check_text and phrase not in source_lower:
                return False, f"Refusal/summary pattern detected ('{phrase}')"

        return True, ""
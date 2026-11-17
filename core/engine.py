import os
import re
import shutil
import threading
from datetime import datetime
from docx import Document
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from core.agents import AgentOrchestrator, OutputTruncatedError
from core.text_utils import (
    build_style_sample, validate_chunk, chunk_hash, load_progress, append_progress,
)
from data.database import GlossaryManager
from core.logging_helper import AppLogger

logger = AppLogger.get_instance()

# ── Run constants ───────────────────────────────────────────────────────────
_MAX_ATTEMPTS = 3            # full 3-agent attempts per chunk (temperature is raised on each retry)
_RETRY_TEMP_STEP = 0.15      # temperature added per retry
_MAX_SPLIT_DEPTH = 3         # a failing chunk is split in half up to this many times


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


def _tail_context(text):
    """Last two sentences of a translated chunk, used as continuity context for the next chunk."""
    sentences = re.split(r'(?<=[.!?؟؛])\s+', text)
    return " ".join(sentences[-2:]) if len(sentences) > 1 else text[-300:]


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

    # ── Chunk translation with retry → split fallback ───────────────────────
    def _split_in_half(self, chunk):
        """Split a chunk into two smaller pieces (at a paragraph boundary, else a sentence boundary)."""
        paras = [p for p in chunk.split("\n\n") if p.strip()]
        if len(paras) >= 2:
            total = sum(len(p.split()) for p in paras)
            acc = 0
            for i, para in enumerate(paras[:-1]):
                acc += len(para.split())
                if acc >= total / 2:
                    return ["\n\n".join(paras[:i + 1]), "\n\n".join(paras[i + 1:])]
            return ["\n\n".join(paras[:-1]), paras[-1]]
        words = chunk.split()
        if len(words) < 40:
            return None
        parts = self._split_long_paragraph(chunk, words_per_chunk=max(20, len(words) // 2))
        return parts if len(parts) >= 2 else None

    def _dump_debug(self, out_dir, base_name, label, attempt, text, debug_files):
        """Save what the model produced on a failed attempt (only when there is something to save)."""
        if not text:
            return
        try:
            path = os.path.join(out_dir, f"{base_name}.debug.chunk{label}.attempt{attempt}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            debug_files.append(path)
        except OSError:
            pass

    def _translate_chunk(self, agent, chunk, label, total_chunks, progress_idx, prev_context,
                         glossary_manager, all_terms, tone_info, target_lang,
                         out_dir, base_name, debug_files, depth=0):
        """Translate one chunk. Returns (text, "") on success or (None, reason) on failure.

        Strategy: up to _MAX_ATTEMPTS full passes (temperature raised on each retry); if all fail, split the
        chunk in half and translate each half the same way (recursively). Nothing is ever skipped.
        """
        glossary_rules = _filter_glossary_for_chunk(glossary_manager, all_terms, chunk)
        reason = "unknown"

        for attempt in range(_MAX_ATTEMPTS):
            if self._stop_event.is_set():
                return None, "stopped"
            agent.temperature_offset = _RETRY_TEMP_STEP * attempt
            suffix = f" (retry {attempt})" if attempt > 0 else "..."
            prefix = f"Chunk {label}/{total_chunks}"
            try:
                self.progress_callback(progress_idx, total_chunks, f"{prefix}: Drafting{suffix}")
                draft = agent.run_drafting_agent(chunk, prev_context, glossary_rules, tone_info, self.persona)
                if self._stop_event.is_set():
                    return None, "stopped"

                self.progress_callback(progress_idx, total_chunks, f"{prefix}: Critiquing & Verifying{suffix}")
                criticized = agent.run_critic_agent(
                    draft, source_text=chunk, glossary_rules=glossary_rules, tone_info=tone_info)
                if self._stop_event.is_set():
                    return None, "stopped"

                self.progress_callback(progress_idx, total_chunks, f"{prefix}: Cultural & Voice Polish{suffix}")
                final = agent.run_cultural_expert_agent(
                    criticized, source_text=chunk, glossary_rules=glossary_rules, tone_info=tone_info)
            except OutputTruncatedError as e:
                reason = f"Output truncated: {e}"
                logger.warning(f"Chunk {label} attempt {attempt + 1}: {reason}")
                self._dump_debug(out_dir, base_name, label, attempt + 1, getattr(e, "partial", ""), debug_files)
                continue
            except RuntimeError as e:
                # timeouts / connection loss / refusals that already used their HTTP retries
                reason = str(e)
                logger.warning(f"Chunk {label} attempt {attempt + 1}: {reason}")
                continue

            ok, reason = self._validate_chunk(chunk, final, target_lang)
            if ok:
                agent.temperature_offset = 0.0
                return final, ""
            # Stage-level recovery: an earlier stage may be valid even if the last one is not
            for name, candidate in (("Critic", criticized), ("Draft", draft)):
                if self._validate_chunk(chunk, candidate, target_lang)[0]:
                    logger.info(f"Chunk {label}: recovered valid output from {name} stage")
                    agent.temperature_offset = 0.0
                    return candidate, ""
            logger.warning(f"Chunk {label} failed validation on attempt {attempt + 1}: {reason}")
            self._dump_debug(out_dir, base_name, label, attempt + 1, final, debug_files)

        agent.temperature_offset = 0.0

        # All full attempts failed → translate it in smaller pieces
        if depth < _MAX_SPLIT_DEPTH:
            halves = self._split_in_half(chunk)
            if halves:
                logger.warning(f"Chunk {label}: splitting into {len(halves)} parts after failure ({reason})")
                self.progress_callback(
                    progress_idx, total_chunks,
                    f"Chunk {label}/{total_chunks}: failed ({reason[:80]}) — retrying in smaller parts")
                texts = []
                ctx = prev_context
                for n, half in enumerate(halves, 1):
                    text, sub_reason = self._translate_chunk(
                        agent, half, f"{label}.{n}", total_chunks, progress_idx, ctx,
                        glossary_manager, all_terms, tone_info, target_lang,
                        out_dir, base_name, debug_files, depth + 1)
                    if text is None:
                        return None, sub_reason
                    texts.append(text)
                    ctx = _tail_context(text)
                return "\n\n".join(texts), ""
        return None, reason

    # ── Output ──────────────────────────────────────────────────────────────
    @staticmethod
    def _write_docx(parts, output_path, is_rtl):
        """Write translated parts to a Word document (paragraphs preserved, RTL for Arabic)."""
        doc = Document()
        for part in parts:
            for para_line in part.splitlines():
                cleaned = para_line.strip()
                if not cleaned:
                    continue
                p = doc.add_paragraph(cleaned)
                if cleaned == "* * *":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif is_rtl:
                    _apply_rtl_to_paragraph(p)
        doc.save(output_path)

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
            src_lang = (self.config_manager.get("source_lang") or "en").strip().lower()
            target_lang = (self.config_manager.get("target_lang") or "ar").strip().lower()
            is_rtl = (target_lang == "ar")

            # ── Output / progress locations ─────────────────────────────────
            target_out_dir = self.output_dir if self.output_dir else os.path.dirname(self.input_file)
            os.makedirs(target_out_dir, exist_ok=True)
            base_name, _ = os.path.splitext(os.path.basename(self.input_file))
            output_path = os.path.abspath(os.path.join(target_out_dir, f"{base_name}_translated.docx"))
            partial_path = os.path.abspath(os.path.join(target_out_dir, f"{base_name}_PARTIAL.docx"))
            progress_path = os.path.join(target_out_dir, f"{base_name}.progress.jsonl")

            # Progress from an earlier interrupted run of the same file (chunks are matched by hash,
            # so a changed source simply re-translates the changed chunks).
            done = load_progress(progress_path)
            resumed = sum(1 for i, c in enumerate(chunks)
                          if done.get(i, {}).get("validated") and done[i].get("hash") == chunk_hash(c))
            if resumed:
                logger.info(f"Resuming: {resumed}/{total_chunks} chunks already translated")

            # ── Stage 0: Style & Voice Profiler (ONCE; reused on resume for consistency) ──
            tone_info = {"instruction": ""}
            if not self._stop_event.is_set():
                style_sample = build_style_sample(content)
                saved_style = done.get(-1)
                if saved_style and saved_style.get("hash") == chunk_hash(style_sample):
                    tone_info = {"instruction": saved_style["text"]}
                else:
                    try:
                        self.progress_callback(0, total_chunks, "Analyzing document style & narrative voice...")
                        style_blueprint = agent_orchestrator.run_style_profiler_agent(style_sample, self.persona)
                        tone_info = {"instruction": style_blueprint}
                        append_progress(progress_path, -1, style_sample, style_blueprint, True)
                    except Exception as style_err:
                        logger.warning(f"Style profiler skipped (continuing with default persona): {style_err}")

            translated_parts = []
            prev_context = ""
            debug_files = []
            ok_count = 0
            failure = None          # (chunk number, reason) when a chunk cannot be translated
            current_idx = 0

            for idx, chunk in enumerate(chunks):
                if self._stop_event.is_set():
                    break

                current_idx = idx + 1

                # Already translated in an earlier run → reuse
                rec = done.get(idx)
                if rec and rec.get("validated") and rec.get("hash") == chunk_hash(chunk):
                    translated_parts.append(rec["text"])
                    prev_context = _tail_context(rec["text"])
                    ok_count += 1
                    self.progress_callback(current_idx, total_chunks,
                                           f"Chunk {current_idx}/{total_chunks}: reused from previous run")
                    continue

                text, reason = self._translate_chunk(
                    agent_orchestrator, chunk, str(current_idx), total_chunks, current_idx, prev_context,
                    glossary_manager, all_terms, tone_info, target_lang,
                    target_out_dir, base_name, debug_files)

                # A chunk that finished and validated is always kept, even if Stop was pressed meanwhile
                if text is not None:
                    ok_count += 1
                    translated_parts.append(text)
                    append_progress(progress_path, idx, chunk, text, True)
                    prev_context = _tail_context(text)
                    continue

                if self._stop_event.is_set():
                    break

                # Could not be translated even after retries and splitting: stop here instead of
                # skipping it, so the document never silently contains an untranslated gap.
                failure = (current_idx, reason)
                logger.error(f"Chunk {current_idx} could not be translated after retries and splitting: {reason}")
                break

            # ── Stopped by the user, or a chunk could not be translated: keep what we have ──
            if self._stop_event.is_set() or failure:
                saved_partial = False
                if ok_count > 0:
                    self._write_docx(translated_parts, partial_path, is_rtl)
                    saved_partial = True
                    logger.info(f"Partial output saved: {partial_path}")
                partial_note = (f" Partial output saved as {os.path.basename(partial_path)}; "
                                f"run the same file again to continue from this point." if saved_partial else "")
                if failure:
                    self.error_callback(
                        f"Chunk {failure[0]} could not be translated even after {_MAX_ATTEMPTS} attempts and "
                        f"splitting it into smaller parts. Reason: {failure[1]}.{partial_note} "
                        f"(Check the *.debug.* files next to the output for what the model produced.)"
                    )
                else:
                    self.progress_callback(current_idx, total_chunks, f"⏹ Stopped.{partial_note}")
                return

            # ── Finished: every chunk translated ────────────────────────────
            self._write_docx(translated_parts, output_path, is_rtl)
            for leftover in [partial_path] + debug_files:
                try:
                    if os.path.exists(leftover):
                        os.remove(leftover)
                except OSError:
                    pass

            if self.archive_dir:
                os.makedirs(self.archive_dir, exist_ok=True)
                archive_dest = os.path.join(self.archive_dir, os.path.basename(self.input_file))
                if os.path.exists(archive_dest):
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_dest = os.path.join(self.archive_dir, f"{base_name}_{stamp}.txt")
                shutil.move(self.input_file, archive_dest)
            try:
                os.remove(progress_path)
            except OSError:
                pass

            logger.info(f"Translation successful: {os.path.basename(output_path)} ({len(translated_parts)} chunks)")
            self.progress_callback(total_chunks, total_chunks, f"✅ Complete! Saved as {os.path.basename(output_path)}")
            if self.completion_callback:
                self.completion_callback(output_path)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Engine failed (source file kept in place; progress file allows resuming): {error_msg}")
            self.error_callback(f"Engine Error: {error_msg}")
        finally:
            if agent_orchestrator is not None:
                agent_orchestrator.close()

    def stop(self):
        self._stop_event.set()

    # ── Chunk validation ────────────────────────────────────────────────────
    def _validate_chunk(self, original_chunk, translated, target_lang=None):
        """Return (is_valid, reason). Direction-aware; see core/text_utils.validate_chunk."""
        src_lang = (self.config_manager.get("source_lang") or "en").strip().lower()
        tgt_lang = (target_lang or self.config_manager.get("target_lang") or "ar").strip().lower()
        return validate_chunk(original_chunk, translated, src_lang, tgt_lang)

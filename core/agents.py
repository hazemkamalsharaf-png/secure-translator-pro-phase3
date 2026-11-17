import time
import requests
import google.generativeai as genai
from core.logging_helper import AppLogger
from core.text_utils import extract_translation, strip_markdown, strip_thinking

logger = AppLogger.get_instance()

LANG_NAMES = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}




# ── Language-pair guidance (injected into every translation agent) ──────────
_GUIDANCE_AR_EN = (
    "ARABIC -> ENGLISH GUIDANCE\n"
    "- REGISTER: Write modern literary English: clear, natural, restrained. Match the intensity of the "
    "source; do NOT make it more ornate, solemn or archaic than the Arabic is. Do not use thee/thou/thy, "
    "hath/doth, unto, wroth, lo, behold, or capitalized pronouns for gods or narrator (He/Him/His/Himself), "
    "unless the source itself is deliberately archaic.\n"
    "- SYNTAX: Arabic chains clauses with و / ف / ثم and long participial phrases. Re-cut them into natural "
    "English sentences (split or merge as English needs) WITHOUT dropping any clause or detail. Do not copy "
    "Arabic repetition or rhetorical parallelism unless it is clearly deliberate.\n"
    "- AMBIGUOUS WORDS: Arabic is usually written without short vowels. Before choosing a reading, check "
    "grammar and context (e.g. نست = 'she forgot', never a name; برد = cold or hail depending on context). "
    "A verb is never a proper noun. NEVER invent a character, place or name: a word is a name only if the "
    "glossary lists it or the source clearly uses it as one.\n"
    "- NAMES: Well-known historical or mythological names use their standard English form. Every other name "
    "follows the glossary, otherwise one consistent transliteration used everywhere.\n"
    "- ADDRESS & TERMS: Render honorifics and forms of address consistently and plainly. Pick ONE English "
    "equivalent for each recurring term and keep it for the whole text; the glossary comes first.\n"
    "- DIALOGUE: Use straight double quotation marks for speech; do not start dialogue lines with dashes."
)

_GUIDANCE_EN_AR = (
    "ENGLISH -> ARABIC GUIDANCE\n"
    "- REGISTER: Fluent literary Modern Standard Arabic matching the intensity of the source. Avoid calques "
    "of English syntax (long passive chains, literal prepositions); use natural Arabic word order and connectors.\n"
    "- PUNCTUATION: Arabic punctuation (، ؛ ؟) and one consistent quotation style.\n"
    "- NAMES & TERMS: Follow the glossary; otherwise one consistent Arabic spelling per name and one Arabic "
    "equivalent per recurring term.\n"
    "- IDIOMS: Render meaning and tone, not word-for-word.\n"
    "- Add tashkeel only where it prevents real ambiguity."
)

_GUIDANCE_GENERIC = (
    "GENERAL GUIDANCE\n"
    "- Translate for meaning, tone and register; the result must read like prose originally written in the "
    "target language, never like a literal rendering.\n"
    "- One consistent rendering per recurring term and per name; the glossary comes first.\n"
    "- Match the intensity of the source; do not embellish."
)

_OUTPUT_CONTRACT = (
    "OUTPUT CONTRACT: Put the complete translation inside <translation> and </translation> tags and write "
    "nothing outside them. Plain text only: no markdown, no asterisks, no '#' headings, no bullet lists, no "
    "notes. Titles and headings stay as plain separate lines."
)


class AgentOrchestrator:
    def __init__(self, config_manager):
        """
        config_manager: An instance of ConfigManager
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.engine_mode = self.config.get("engine_mode", "local")
        # Persistent HTTP session for local LLM connection pooling (Keep-Alive)
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._configured_gemini_key = None
        # Added to every call's temperature. The engine raises it on retries so a failing chunk is not
        # re-run with the exact same settings (which tends to fail the exact same way).
        self.temperature_offset = 0.0

    # ── Language helpers ────────────────────────────────────────────────────
    def _get_lang_code(self, key, default_code):
        return (self.config.get(key) or default_code).strip().lower()

    def _get_lang_name(self, key, default_code):
        code = self._get_lang_code(key, default_code)
        return LANG_NAMES.get(code, code)

    def _get_source_lang_name(self):
        return self._get_lang_name("source_lang", "en")

    def _get_target_lang_name(self):
        return self._get_lang_name("target_lang", "ar")

    def _pair_guidance(self):
        pair = (self._get_lang_code("source_lang", "en"), self._get_lang_code("target_lang", "ar"))
        if pair == ("ar", "en"):
            return _GUIDANCE_AR_EN
        if pair == ("en", "ar"):
            return _GUIDANCE_EN_AR
        return _GUIDANCE_GENERIC

    @staticmethod
    def _finalize(raw):
        """Raw model output -> clean plain text (tags, <think> blocks and markdown removed)."""
        return strip_markdown(extract_translation(raw))

    # ── LLM transport ───────────────────────────────────────────────────────
    def _call_llm(self, system_prompt, user_prompt, temperature=0.3):
        temperature = min(1.0, temperature + self.temperature_offset)
        if hasattr(self.config_manager, "get_config"):
            self.config = self.config_manager.get_config()
        self.engine_mode = self.config.get("engine_mode", "local")
        if self.engine_mode == "cloud":
            return self._call_cloud_gemini(system_prompt, user_prompt, temperature=temperature)
        return self._call_local(system_prompt, user_prompt, temperature=temperature)

    def _call_local(self, system_prompt, user_prompt, temperature=0.3):
        # Verify response validity before processing
        settings = self.config.get("local_settings", {})

        base_url = settings.get("base_url", "http://localhost:1234/v1").strip().rstrip('/')
        url = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
        model = settings.get("model_name", "local-model")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "top_p": 0.9,
            "stream": False,
        }
        # Hard cap on generated tokens: a 400-word chunk needs ~1,000 output tokens, so 4096 leaves a wide
        # margin while stopping a runaway generation (repetition loop / endless reasoning). Set
        # "max_tokens" in local_settings to change it (0 disables the cap).
        max_tokens = settings.get("max_tokens", 12000)
        if max_tokens:
            payload["max_tokens"] = int(max_tokens)

        timeout = int(settings.get("timeout", 600))
        max_retries = int(settings.get("max_retries", 2))

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"LLM request attempt {attempt + 1}/{max_retries + 1} → {url} "
                    f"(model={model}, timeout={timeout}s)"
                )
                response = self.session.post(url, json=payload, timeout=timeout)

                try:
                    data = response.json()
                except ValueError:
                    raise RuntimeError(f"Local LLM Error: Received non-JSON response. Status: {response.status_code}")

                if response.status_code == 200:
                    if 'choices' in data and data['choices']:
                        choice = data['choices'][0]
                        message = choice.get('message', {})
                        if choice.get('finish_reason') == 'length':
                            err = OutputTruncatedError(
                                "Model output was cut off (token limit reached). Increase the context "
                                "length / max_tokens in LM Studio or reduce the chunk size."
                            )
                            # Keep what the model produced so the engine can dump it for diagnosis
                            # (endless reasoning vs. a repetition loop look very different).
                            reasoning = message.get('reasoning_content') or ""
                            err.partial = (f"[REASONING]\n{reasoning}\n\n" if reasoning else "") + \
                                          f"[CONTENT]\n{message.get('content') or ''}"
                            raise err
                        return (message.get('content') or "").strip()
                    elif 'error' in data:
                        logger.error(f"LM Studio error detail: {data['error']}")
                        raise RuntimeError(f"LM Studio Refused the prompt: {data['error']}")
                    else:
                        raise RuntimeError("Received a 200 OK, but no 'choices' or 'error' key found in JSON.")
                else:
                    error_msg = data.get('error', response.text)
                    raise RuntimeError(f"Local LLM Error ({response.status_code}): {error_msg}")

            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {timeout}s"
                if attempt < max_retries:
                    logger.warning(f"Timeout — retrying ({attempt + 1}/{max_retries})...")
                    continue
                raise RuntimeError(f"LLM request timed out: {last_error}. Try increasing the timeout in settings.")
            except requests.exceptions.ConnectionError:
                last_error = "Connection failed — is LM Studio running?"
                if attempt < max_retries:
                    logger.warning(f"Connection error — retrying ({attempt + 1}/{max_retries})...")
                    continue
                raise RuntimeError(f"Cannot connect to LLM server: {last_error}. Ensure LM Studio server is running.")
            except RuntimeError:
                # Non-retryable (LM Studio refusal, truncated output, bad JSON)
                raise

        raise RuntimeError(f"LLM request failed after {max_retries + 1} attempts: {last_error}")

    def _call_cloud_gemini(self, system_prompt, user_prompt, temperature=0.3):
        settings = self.config.get("cloud_settings", {})
        api_key = settings.get("api_key")
        if not api_key:
            raise RuntimeError("Cloud API Key is missing in Settings.")

        model_name = settings.get("model_name") or "gemini-2.5-flash"
        max_retries = int(settings.get("max_retries", 2))
        provider = settings.get("provider", "gemini")
        logger.debug(f"Cloud LLM request (provider={provider}, model={model_name})")

        if self._configured_gemini_key != api_key:
            genai.configure(api_key=api_key)
            self._configured_gemini_key = api_key

        for attempt in range(max_retries + 1):
            try:
                # The system prompt is sent as a real system instruction (it used to be pasted
                # in front of the user prompt). Creating the model object is cheap — no network call.
                try:
                    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                    prompt = user_prompt
                except TypeError:  # very old SDK without system_instruction
                    model = genai.GenerativeModel(model_name)
                    prompt = f"{system_prompt}\n\n{user_prompt}"

                response = model.generate_content(prompt, generation_config={"temperature": temperature})

                cand = response.candidates[0] if getattr(response, "candidates", None) else None
                if cand is not None and "MAX_TOKENS" in str(getattr(cand, "finish_reason", "")):
                    raise OutputTruncatedError("Gemini output was cut off (MAX_TOKENS).")
                try:
                    text = response.text
                except ValueError:
                    fb = getattr(response, "prompt_feedback", None)
                    raise RuntimeError(f"Gemini returned no text (blocked by a safety filter or empty). {fb or ''}")
                logger.info(f"Cloud LLM response received (model={model_name})")
                return text.strip()

            except OutputTruncatedError:
                raise
            except Exception as e:
                msg = str(e)
                transient = any(k in msg for k in (
                    "429", "500", "502", "503", "504", "timed out", "Deadline", "UNAVAILABLE", "ResourceExhausted"))
                if transient and attempt < max_retries:
                    wait = 2 * (attempt + 1)
                    logger.warning(f"Gemini transient error, retrying in {wait}s ({attempt + 1}/{max_retries}): {msg[:120]}")
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"Gemini API Error (model={model_name}): {msg}")

    # ── Agent 0: Document Style & Voice Profiler (runs ONCE per file) ───────
    def run_style_profiler_agent(self, sample_text, custom_persona=""):
        """
        Analyzes a multi-point sample of the document ONCE before chunk translation starts
        (use text_utils.build_style_sample). Returns a compact Style & Voice Blueprint that is
        injected into every later agent prompt for consistency.
        """
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()

        system_prompt = (
            "You are a senior literary analyst and translation director.\n"
            f"The user gives you {src_lang} excerpts taken from different parts of ONE book. Write a compact "
            f"Style & Voice Blueprint to guide a {src_lang}-to-{tgt_lang} translation team.\n"
            "Output EXACTLY 5 bullet points, in English, each starting with '- ':\n"
            "1. Genre & register of the MAIN narrative. A solemn prologue, epigraph or title block must not "
            "define the whole book: if the rest is plainer, describe the main text and mention the opening "
            "only as an exception.\n"
            "2. Narrative POV & tense.\n"
            "3. Pacing & sentence rhythm.\n"
            "4. Dialogue vs narration: how characters speak (formality, humour, differences between speakers).\n"
            f"5. TARGET REGISTER: in plain words, what the {tgt_lang} translation should sound like, and what "
            "it must avoid (for example: 'plain modern literary English; no archaic or biblical wording').\n"
            "Do NOT translate the excerpts. No markdown other than the leading '- '."
        )
        user_prompt = (
            f"[USER PERSONA / NOTES]\n{custom_persona if custom_persona else 'Standard literary fidelity.'}\n\n"
            f"[EXCERPTS ({src_lang})]\n---\n{sample_text[:6500]}\n---\n"
            "Write the 5-point Style & Voice Blueprint now:"
        )
        logger.debug(f"Style profiler agent analyzing {len(sample_text[:6500])} chars")
        blueprint = strip_thinking(self._call_llm(system_prompt, user_prompt, temperature=0.2))
        logger.info("Style profiler agent generated document blueprint")
        return f"DOCUMENT STYLE & VOICE BLUEPRINT:\n{blueprint}"

    # ── Agent 1: Literary Drafting Agent ────────────────────────────────────
    def run_drafting_agent(self, text, context, glossary_rules, tone_info, custom_persona):
        # Ensure previous context is correctly passed for translation continuity
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"{custom_persona}\n"
            f"{tone_instruction}\n\n"
            f"{self._pair_guidance()}\n\n"
            "TRANSLATION PROTOCOL\n"
            f"- Translate the source from {src_lang} into {tgt_lang}.\n"
            "- Every sentence of the source must appear in the translation: no summarizing, no omissions, "
            "no additions, no commentary.\n"
            "- Keep the order of the text and the paragraph breaks (one source paragraph -> one translated "
            "paragraph). Headings and titles stay as separate plain lines.\n"
            "- Match the register and intensity of the source; do not embellish.\n"
            f"- Mandatory glossary (use exactly these renderings): {glossary_rules if glossary_rules else 'None'}\n\n"
            f"{_OUTPUT_CONTRACT}"
        )
        user_prompt = (
            "[PREVIOUS TRANSLATED TEXT — for continuity of names, pronouns and tone only. "
            f"Do NOT translate or repeat it]\n{context if context else 'None (this is the start).'}\n\n"
            f"[SOURCE TEXT ({src_lang}) — TRANSLATE THIS]\n---\n{text}\n---\n"
            f"Translate the whole source text into {tgt_lang} now."
        )
        logger.debug(f"Drafting agent ({src_lang} -> {tgt_lang}): {len(text)} chars")
        result = self._finalize(self._call_llm(system_prompt, user_prompt, temperature=0.3))
        logger.info(f"Drafting agent: {len(result)} chars returned")
        return result

    # ── Agent 2: Source-Aware Critic & Fidelity Agent ───────────────────────
    def run_critic_agent(self, draft, source_text="", glossary_rules="", tone_info=None):
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"You are a senior bilingual editor ({src_lang} -> {tgt_lang}).\n"
            f"{tone_instruction}\n\n"
            f"{self._pair_guidance()}\n\n"
            "Compare the DRAFT with the SOURCE sentence by sentence and correct the draft. Check, in this order:\n"
            "1. MISTRANSLATION: wrong reading of an ambiguous word, wrong subject/object, wrong tense, a verb "
            "or common word mistaken for a name, invented names.\n"
            "2. OMISSION / ADDITION: every source sentence is present; nothing is added.\n"
            "3. GLOSSARY & CONSISTENCY: mandatory terms used exactly; recurring terms rendered the same way.\n"
            f"4. REGISTER: remove archaic or over-ornate wording the source does not justify, and any "
            f"translationese that makes the {tgt_lang} sound unnatural.\n\n"
            "MINIMAL EDITS: if a sentence is already correct and natural, copy it unchanged. Do not rewrite "
            "for taste. Do not shorten. Keep the paragraph breaks.\n"
            f"- Mandatory glossary: {glossary_rules if glossary_rules else 'None'}\n\n"
            f"{_OUTPUT_CONTRACT}"
        )

        if source_text:
            user_prompt = (
                f"[SOURCE TEXT ({src_lang})]\n---\n{source_text}\n---\n\n"
                f"[DRAFT TRANSLATION ({tgt_lang})]\n---\n{draft}\n---\n\n"
                f"Return the corrected {tgt_lang} translation."
            )
        else:
            user_prompt = (
                f"[DRAFT TRANSLATION ({tgt_lang})]\n---\n{draft}\n---\n\n"
                f"No source is available: only fix awkward or unnatural {tgt_lang} and terminology "
                "inconsistencies, keeping every detail. Return the corrected text."
            )

        logger.debug(f"Critic agent ({tgt_lang}): {len(draft)} chars")
        result = self._finalize(self._call_llm(system_prompt, user_prompt, temperature=0.2))
        logger.info(f"Critic agent: {len(result)} chars returned")
        return result

    # ── Agent 3: Voice & Idiom Polish (kept under its old name) ─────────────
    def run_cultural_expert_agent(self, refined_text, source_text="", glossary_rules="", tone_info=None):
        # Add specific rules for cultural expressions and idioms
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"You are a literary stylist and cultural mediator for {tgt_lang} ({src_lang} -> {tgt_lang}). "
            "This is the LAST pass: voice and idiom only.\n"
            f"{tone_instruction}\n\n"
            f"{self._pair_guidance()}\n\n"
            "Fix ONLY what is flat or wrong:\n"
            f"1. Idioms, metaphors, humour or sarcasm that were rendered literally: express them in natural "
            f"{tgt_lang} while keeping the original image and tone.\n"
            "2. Character voices: speakers who sound identical although the source distinguishes them "
            "(formality, temperament, humour).\n"
            "3. Tonal mismatch with the source. Narration stays at the register of the source — do NOT "
            "elevate or ornament it.\n\n"
            "NEVER change the meaning, delete or add details, alter glossary terms or change the paragraph "
            "structure. If the text already reads well, return it unchanged.\n"
            f"- Mandatory glossary: {glossary_rules if glossary_rules else 'None'}\n\n"
            f"{_OUTPUT_CONTRACT}"
        )

        if source_text:
            user_prompt = (
                f"[SOURCE TEXT ({src_lang})]\n---\n{source_text}\n---\n\n"
                f"[CURRENT TRANSLATION ({tgt_lang})]\n---\n{refined_text}\n---\n\n"
                f"Return the final {tgt_lang} text."
            )
        else:
            user_prompt = (
                f"[CURRENT TRANSLATION ({tgt_lang})]\n---\n{refined_text}\n---\n\n"
                f"Return the final {tgt_lang} text."
            )

        logger.debug(f"Cultural expert agent ({tgt_lang}): {len(refined_text)} chars")
        result = self._finalize(self._call_llm(system_prompt, user_prompt, temperature=0.2))
        logger.info(f"Cultural expert agent: {len(result)} chars returned")
        return result

    def close(self):
        # Ensure all resources are properly closed to prevent memory leaks
        """Close the persistent HTTP session cleanly."""
        try:
            self.session.close()
        except Exception:
            pass

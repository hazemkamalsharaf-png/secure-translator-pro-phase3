import os
import requests
import google.generativeai as genai
from datetime import datetime
from core.logging_helper import AppLogger

logger = AppLogger.get_instance()

LANG_NAMES = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}


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
        self._cached_gemini_key = None
        self._cached_gemini_model_name = None
        self._cached_gemini_model = None

    def _get_lang_name(self, key, default_code):
        code = (self.config.get(key) or default_code).strip().lower()
        return LANG_NAMES.get(code, code)

    def _get_source_lang_name(self):
        return self._get_lang_name("source_lang", "en")

    def _get_target_lang_name(self):
        return self._get_lang_name("target_lang", "ar")

    def _call_llm(self, system_prompt, user_prompt, temperature=0.3):
        if hasattr(self.config_manager, "get_config"):
            self.config = self.config_manager.get_config()
        self.engine_mode = self.config.get("engine_mode", "local")
        if self.engine_mode == "cloud":
            return self._call_cloud_gemini(system_prompt, user_prompt, temperature=temperature)
        else:
            return self._call_local(system_prompt, user_prompt, temperature=temperature)

    def _call_local(self, system_prompt, user_prompt, temperature=0.3):
        settings = self.config.get("local_settings", {})

        base_url = settings.get("base_url", "http://localhost:1234/v1").strip().rstrip('/')
        if not base_url.endswith("/chat/completions"):
            url = f"{base_url}/chat/completions"
        else:
            url = base_url

        model = settings.get("model_name", "local-model")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "top_p": 0.9,
        }

        # Configurable timeout (default 120s) and retry count
        timeout = int(settings.get("timeout", 120))
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
                        return data['choices'][0]['message']['content'].strip()
                    elif 'error' in data:
                        print(f"⚠️ LM Studio Error Detail: {data['error']}")
                        raise RuntimeError(f"LM Studio Refused the prompt: {data['error']}")
                    else:
                        raise RuntimeError("Received a 200 OK, but no 'choices' or 'error' key found in JSON.")
                else:
                    error_msg = data.get('error', response.text)
                    raise RuntimeError(f"Local LLM Error ({response.status_code}): {error_msg}")

            except requests.exceptions.Timeout:
                last_error = f"Request timed out after {timeout}s"
                if attempt < max_retries:
                    print(f"⏱️ Timeout — retrying ({attempt + 1}/{max_retries})...")
                    continue
                raise RuntimeError(f"LLM request timed out: {last_error}. Try increasing the timeout in settings.")
            except requests.exceptions.ConnectionError:
                last_error = "Connection failed — is LM Studio running?"
                if attempt < max_retries:
                    print(f"🔌 Connection error — retrying ({attempt + 1}/{max_retries})...")
                    continue
                raise RuntimeError(f"Cannot connect to LLM server: {last_error}. Ensure LM Studio server is running.")
            except RuntimeError:
                # Non-retryable error (e.g. LM Studio refusal)
                raise

        raise RuntimeError(f"LLM request failed after {max_retries + 1} attempts: {last_error}")

    def _call_cloud_gemini(self, system_prompt, user_prompt, temperature=0.3):
        settings = self.config.get("cloud_settings", {})
        api_key = settings.get("api_key")
        if not api_key:
            raise RuntimeError("Cloud API Key is missing in Settings.")

        model_name = settings.get("model_name") or "gemini-2.5-flash"
        try:
            provider = settings.get("provider", "gemini")
            logger.debug(f"Cloud LLM request (provider={provider}, model={model_name})")

            if self._cached_gemini_key != api_key or self._cached_gemini_model_name != model_name or self._cached_gemini_model is None:
                genai.configure(api_key=api_key)
                self._cached_gemini_model = genai.GenerativeModel(model_name)
                self._cached_gemini_key = api_key
                self._cached_gemini_model_name = model_name

            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self._cached_gemini_model.generate_content(
                full_prompt,
                generation_config={"temperature": temperature},
            )
            logger.info(f"Cloud LLM response received (model={model_name})")
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API Error (model={model_name}): {str(e)}")

    # ── Agent 0: Document Style & Voice Profiler (Runs ONCE per file) ─────────
    def run_style_profiler_agent(self, sample_text, custom_persona=""):
        """
        Analyzes an opening sample of the document ONCE before chunk translation starts.
        Returns a concise Style & Voice Blueprint (tone, POV, register, character voice cues)
        that is injected into tone_info['instruction'] across all chunks for consistency.
        """
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()

        system_prompt = (
            "You are a senior literary analyst and translation director.\n"
            f"Analyze the provided {src_lang} text excerpt and produce a compact Style & Voice Blueprint "
            f"(maximum 5 bullet points) to guide a {src_lang}-to-{tgt_lang} translation team.\n"
            "Cover ONLY:\n"
            "1. Genre & Literary Register (e.g., satirical, classical, dark literary, modern realistic, academic).\n"
            "2. Narrative POV & Tense.\n"
            "3. Pacing & Sentence Rhythm.\n"
            "4. Character Dialogue vs. Narration tone.\n"
            "Output ONLY the concise bullet points in English. Do NOT translate the sample."
        )
        user_prompt = (
            f"[USER PERSONA / NOTES]\n{custom_persona if custom_persona else 'Standard literary fidelity.'}\n\n"
            f"[OPENING SAMPLE ({src_lang})]\n---\n{sample_text[:1800]}\n---\n"
            "Generate the 4-point Style & Voice Blueprint now:"
        )
        logger.debug(f"Style profiler agent analyzing {len(sample_text[:1800])} chars")
        blueprint = self._call_llm(system_prompt, user_prompt, temperature=0.2)
        logger.info("Style profiler agent generated document blueprint")
        return f"DOCUMENT STYLE & VOICE BLUEPRINT:\n{blueprint}"

    # ── Agent 1: Literary Drafting Agent ──────────────────────────────────────
    def run_drafting_agent(self, text, context, glossary_rules, tone_info, custom_persona):
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"{custom_persona}\n"
            f"{tone_instruction}\n\n"
            "STRICT OPERATING PROTOCOLS:\n"
            f"- Translate the source text from {src_lang} into {tgt_lang}.\n"
            f"- Output ONLY the translated text in {tgt_lang}. No introductions, commentary, or outros.\n"
            "- Maintain atmospheric density, narrative voice, and emotional resonance.\n"
            "- Preserve all original paragraph breaks and dialogue structure.\n"
            "- CRITICAL RULE: DO NOT SUMMARIZE, truncate, or omit any descriptive details, adjectives, or clauses from the source.\n"
            f"- Glossary Constraints: {glossary_rules if glossary_rules else 'None'}"
        )
        user_prompt = (
            f"[CONTEXTUAL BACKGROUND FROM PREVIOUS PARAGRAPH]\n{context if context else 'No prior context.'}\n\n"
            f"[SOURCE TEXT ({src_lang})]\n---\n{text}\n---\n"
            f"Task: Execute a complete, unabridged translation into {tgt_lang}, preserving every descriptive element and paragraph break."
        )
        logger.debug(f"Drafting agent ({src_lang} -> {tgt_lang}): {len(text)} chars")
        result = self._call_llm(system_prompt, user_prompt, temperature=0.3)
        logger.info(f"Drafting agent: {len(result)} chars returned")
        return result

    # ── Agent 2: Source-Aware Critic & Fidelity Agent ─────────────────────────
    def run_critic_agent(self, draft, source_text="", glossary_rules="", tone_info=None):
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"You are a world-class bilingual senior editor and linguistic critic ({src_lang} -> {tgt_lang}).\n"
            f"{tone_instruction}\n\n"
            "Your task is to compare the Draft Translation against the Original Source Text and refine it:\n"
            "1. 100% SEMANTIC FIDELITY: Restore any subtle meaning, adjective, clause, or nuance that was softened or missed in the draft.\n"
            "2. GLOSSARY ENFORCEMENT: Verify that all mandatory glossary terms are strictly respected.\n"
            f"3. FLOW & ELEGANCE: Ensure the {tgt_lang} prose is fluid, natural, and free of awkward literal 'translationese'.\n\n"
            "CRITICAL RULES:\n"
            f"- Keep the output strictly in {tgt_lang}.\n"
            "- NEVER summarize, shorten, or compress the text.\n"
            "- Preserve all paragraph breaks.\n"
            f"- Glossary Constraints: {glossary_rules if glossary_rules else 'None'}\n\n"
            f"OUTPUT RULE: Return ONLY the final, polished {tgt_lang} translation text."
        )

        if source_text:
            user_prompt = (
                f"[ORIGINAL SOURCE TEXT ({src_lang})]\n---\n{source_text}\n---\n\n"
                f"[DRAFT TRANSLATION FOR REVIEW ({tgt_lang})]\n---\n{draft}\n---\n\n"
                f"[INSTRUCTION]\nCompare the draft against the source text, fix any inaccuracies or awkward phrasing, "
                f"and output ONLY the refined {tgt_lang} translation."
            )
        else:
            user_prompt = (
                f"[DRAFT TRANSLATION FOR REVIEW ({tgt_lang})]\n{draft}\n\n"
                f"[INSTRUCTION]\nCritique and refine the {tgt_lang} prose while strictly maintaining the full text length and details. "
                f"Output only the final corrected {tgt_lang} text."
            )

        logger.debug(f"Critic agent ({tgt_lang}): {len(draft)} chars")
        result = self._call_llm(system_prompt, user_prompt, temperature=0.25)
        logger.info(f"Critic agent: {len(result)} chars returned")
        return result

    # ── Agent 3: Cultural & Polyphony Master Agent ────────────────────────────
    def run_cultural_expert_agent(self, refined_text, source_text="", glossary_rules="", tone_info=None):
        src_lang = self._get_source_lang_name()
        tgt_lang = self._get_target_lang_name()
        tone_instruction = tone_info.get("instruction", "") if isinstance(tone_info, dict) else ""

        system_prompt = (
            f"You are an expert literary stylist and cultural mediator specializing in {tgt_lang}.\n"
            f"{tone_instruction}\n\n"
            "Your task is to ensure the 'soul', character voices (polyphony), and emotional cadence of the original work shine naturally in the translation:\n"
            f"1. CULTURAL & IDIOMATIC RESONANCE: Adapt metaphors, sarcasm, humor, and idioms into authentic literary {tgt_lang} without losing the original imagery.\n"
            "2. CHARACTER VOICE DISTINCTION: Keep narration elevated and character dialogue authentic to each speaker's tone.\n"
            "3. GLOSSARY & DETAIL LOCK: Never alter locked glossary terms or delete any descriptive detail.\n\n"
            "CRITICAL RULES:\n"
            f"- Keep the entire output strictly in {tgt_lang}.\n"
            "- NEVER omit, summarize, or alter the structural length or paragraph breaks of the text.\n"
            f"- Glossary Constraints: {glossary_rules if glossary_rules else 'None'}\n\n"
            f"OUTPUT RULE: Return ONLY the final version of the {tgt_lang} text."
        )

        if source_text:
            user_prompt = (
                f"[ORIGINAL SOURCE TEXT ({src_lang})]\n---\n{source_text}\n---\n\n"
                f"[REFINED TRANSLATION ({tgt_lang})]\n---\n{refined_text}\n---\n\n"
                f"[INSTRUCTION]\nPerform the final literary and cultural polish in {tgt_lang} while preserving every single detail, "
                f"glossary term, and paragraph break. Output ONLY the final {tgt_lang} text."
            )
        else:
            user_prompt = (
                f"[PROCESSED TRANSLATION ({tgt_lang})]\n{refined_text}\n\n"
                f"[INSTRUCTION]\nReview through a cultural lens in {tgt_lang} without losing a single descriptive detail. "
                f"Output only the final {tgt_lang} version."
            )

        logger.debug(f"Cultural expert agent ({tgt_lang}): {len(refined_text)} chars")
        result = self._call_llm(system_prompt, user_prompt, temperature=0.25)
        logger.info(f"Cultural expert agent: {len(result)} chars returned")
        return result

    def close(self):
        """Close the persistent HTTP session cleanly."""
        try:
            self.session.close()
        except Exception:
            pass
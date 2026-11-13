import os
import requests
import google.generativeai as genai
from datetime import datetime
from core.logging_helper import AppLogger

logger = AppLogger.get_instance()

class AgentOrchestrator:
    def __init__(self, config_manager):
        """
        config_manager: An instance of ConfigManager
        """
        self.config = config_manager.config
        self.engine_mode = self.config.get("engine_mode", "local")

    def _call_llm(self, system_prompt, user_prompt):
        if self.engine_mode == "cloud":
            return self._call_cloud_gemini(system_prompt, user_prompt)
        else:
            return self._call_local(system_prompt, user_prompt)

    def _call_local(self, system_prompt, user_prompt):
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
            "temperature": 0.3
        }
        
        # Configurable timeout (default 120s) and retry count
        timeout = int(settings.get("timeout", 120))
        max_retries = int(settings.get("max_retries", 2))
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"LLM request attempt {attempt + 1}/{max_retries + 1} → {url} (model={model}, timeout={timeout}s)")
                response = requests.post(url, json=payload, timeout=timeout)
                
                try:
                    data = response.json()
                except ValueError:
                    raise RuntimeError(f"Local LLM Error: Received non-JSON response. Status: {response.status_code}")

                if response.status_code == 200:
                    if 'choices' in data:
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
                last_error = f"Connection failed — is LM Studio running?"
                if attempt < max_retries:
                    print(f"🔌 Connection error — retrying ({attempt + 1}/{max_retries})...")
                    continue
                raise RuntimeError(f"Cannot connect to LLM server: {last_error}. Ensure LM Studio server is running.")
            except RuntimeError as e:
                # Non-retryable error (e.g. LM Studio refusal)
                raise
            
        raise RuntimeError(f"LLM request failed after {max_retries + 1} attempts: {last_error}")

    def _call_cloud_gemini(self, system_prompt, user_prompt):
        settings = self.config.get("cloud_settings", {})
        api_key = settings.get("api_key")
        if not api_key:
            raise RuntimeError("Cloud API Key is missing in Settings.")

        try:
            provider = settings.get("provider", "gemini")
            logger.debug(f"Cloud LLM request (provider={provider})")
            genai.configure(api_key=api_key)
            # Read model_name from cloud_settings with a sensible default
            model_name = settings.get("model_name", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(full_prompt)
            logger.info(f"Cloud LLM response received (model={model_name})")
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API Error (model={settings.get('model_name', 'gemini-1.5-flash')}): {str(e)}")

    def run_drafting_agent(self, text, context, glossary_rules, tone_info, custom_persona):
        system_prompt = (
            f"{custom_persona}\n"
            f"{tone_info['instruction']}\n"
            "STRICT OPERATING PROTOCOLS:\n"
            "- Output ONLY the translated text. No introductions or outros.\n"
            "- Maintain atmospheric density and emotional resonance.\n"
            "- CRITICAL RULE: DO NOT SUMMARIZE, truncate, or omit any descriptive details, adjectives, or clauses from the source.\n"
            f"- Glossary Constraints: {glossary_rules}"
        )
        user_prompt = (
            f"[CONTEXTUAL BACKGROUND]\n{context if context else 'No prior context.'}\n\n"
            f"[SOURCE TEXT]\n---\n{text}\n---\n"
            "Task: Execute a high-fidelity literary translation preserving every single descriptive element and length."
        )
        logger.debug(f"Drafting agent: {len(text)} chars")
        result = self._call_llm(system_prompt, user_prompt)
        logger.info(f"Drafting agent: {len(result)} chars returned")
        return result

    def run_critic_agent(self, draft):
        system_prompt = (
            "You are a world-class professional editor and linguistic critic.\n"
            "Your task is to review the provided draft translation against these criteria:\n"
            "1. ACCURACY: Does it faithfully represent the source context?\n"
            "2. FLOW & ELEGANCE: Is the English prose fluid, natural, and literary?\n"
            "3. NO LEAKAGE: Ensure no traces of 'translationese' remain.\n\n"
            "CRITICAL RULES:\n"
            "- NEVER summarize, shorten, or compress the text.\n"
            "- Preserve all descriptive details and atmospheric depth. You MUST split long run-on sentences into well-paced English prose using proper punctuation (periods and semicolons), but NEVER delete or summarize any details.\n\n"
            "OUTPUT RULE: Return ONLY the final, polished version of the translation text."
        )
        user_prompt = f"[DRAFT TRANSLATION FOR REVIEW]\n{draft}\n\n[INSTRUCTION]\nCritique and refine while strictly maintaining the full text length and details. Output only the final corrected text."
        logger.debug(f"Critic agent: {len(draft)} chars")
        result = self._call_llm(system_prompt, user_prompt)
        logger.info(f"Critic agent: {len(result)} chars returned")
        return result

    def run_cultural_expert_agent(self, refined_text):
        system_prompt = (
            "You are an expert cultural mediator.\n"
            "Your task is to ensure the 'soul' of the original text survives.\n"
            "CRITERIA:\n"
            "1. CULTURAL RESONANCE: Does it evoke the same emotion?\n"
            "2. IDIOMATIC EQUIVALENCE: Are metaphors adapted naturally?\n\n"
            "CRITICAL RULES:\n"
            "- NEVER omit, summarize, or alter the structural length of the text.\n"
            "- Keep all descriptive imagery fully intact.\n\n"
            "OUTPUT RULE: Return ONLY the final version of the text after cultural adjustment."
        )
        user_prompt = f"[PROCESSED TRANSLATION]\n{refined_text}\n\n[INSTRUCTION]\nReview through a cultural lens without losing a single descriptive detail. Output only the final version."
        logger.debug(f"Cultural expert agent: {len(refined_text)} chars")
        result = self._call_llm(system_prompt, user_prompt)
        logger.info(f"Cultural expert agent: {len(result)} chars returned")
        return result
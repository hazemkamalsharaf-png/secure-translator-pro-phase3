
import os
import re
import shutil
import threading
from datetime import datetime
from core.agents import AgentOrchestrator
from data.database import GlossaryManager
from docx import Document
from core.logging_helper import AppLogger

logger = AppLogger.get_instance()

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

    def _split_into_word_chunks(self, text, words_per_chunk=400):
        words = text.split()
        if not words: return []
        chunks = []
        current_chunk_words = []
        current_word_count = 0
        for word in words:
            current_chunk_words.append(word)
            current_word_count += 1
            if current_word_count >= words_per_chunk:
                last_punctuation_idx = -1
                for i in range(len(current_chunk_words) - 1, -1, -1):
                    if re.search(r'[.!?]', current_chunk_words[i]):
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
        if current_chunk_words: chunks.append(" ".join(current_chunk_words))
        return chunks

    def run(self):
        try:
            # Robust path resolution using unified helper
            from ui.asset_path import data_dir
            db_path = os.path.join(data_dir(), "glossary.db")
            
            glossary_manager = GlossaryManager(db_path)
            all_terms = glossary_manager.get_all_terms()
            glossary_rules = glossary_manager.format_for_prompt(all_terms)

            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            if not os.path.exists(self.archive_dir):
                os.makedirs(self.archive_dir)

            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            chunks = self._split_into_word_chunks(content)
            total_chunks = len(chunks)
            
            logger.info(f"Starting translation: {self.input_file} ({len(content)} chars, {total_chunks} chunks)")
            agent_orchestrator = AgentOrchestrator(self.config_manager)

            translated_parts = []
            prev_context = ""

            for idx, chunk in enumerate(chunks):
                if self._stop_event.is_set(): break
                
                current_idx = idx + 1
                tone_info = {"instruction": ""} 
                
                self.progress_callback(current_idx, total_chunks, f"Chunk {current_idx}/{total_chunks}: Drafting...")
                draft = agent_orchestrator.run_drafting_agent(chunk, prev_context, glossary_rules, tone_info, self.persona)

                self.progress_callback(current_idx, total_chunks, f"Chunk {current_idx}/{total_chunks}: Critiquing...")
                criticized = agent_orchestrator.run_critic_agent(draft)

                self.progress_callback(current_idx, total_chunks, f"Chunk {current_idx}/{total_chunks}: Cultural Check...")
                final_chunk = agent_orchestrator.run_cultural_expert_agent(criticized)

                translated_parts.append(final_chunk)
                
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                prev_context = " ".join(sentences[-2:]) if len(sentences) > 1 else ""

            if not self._stop_event.is_set():
                # 1. Calculate new path: Force .docx extension
                source_dir = os.path.dirname(self.input_file)
                base_name, _ = os.path.splitext(os.path.basename(self.input_file))
                output_filename = f"{base_name}_translated.docx"
                output_path = os.path.abspath(os.path.join(source_dir, output_filename))

                # 2. Write the translated content to a Word Document
                doc = Document()
                for part in translated_parts:
                    # Clean up any weird spacing and add as a paragraph
                    if part.strip():
                        doc.add_paragraph(part.strip())
                doc.save(output_path)

                # 3. Archive the original file to prevent re-processing
                archive_dest = os.path.join(self.archive_dir, os.path.basename(self.input_file))
                shutil.move(self.input_file, archive_dest)

                # 4. Terminal Logging (Absolute Path)
                logger.info(f"Translation successful: {output_filename} ({len(translated_parts)} chunks)")
                print(f"✅ Translation successful! File saved to: {output_path}")

                # 5. UI Notification via callbacks
                self.progress_callback(total_chunks, total_chunks, f"✅ Complete! Saved as {os.path.basename(output_path)}")
                
                if self.completion_callback:
                    self.completion_callback(output_path)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Engine failed: {error_msg}")
            try:
                # Use unified path resolution for archive
                from ui.asset_path import data_dir
                archive_base = self.archive_dir if os.path.isabs(self.archive_dir) else os.path.join(data_dir(), "archived")
                if not os.path.exists(archive_base): os.makedirs(archive_base)
                shutil.move(self.input_file, os.path.join(archive_base, f"ERROR_{os.path.basename(self.input_file)}"))
            except: pass
            self.error_callback(f"Engine Error: {error_msg}")

    def stop(self):
        self._stop_event.set()

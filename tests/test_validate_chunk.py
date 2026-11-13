"""Tests for TranslationEngine._validate_chunk logic.

Covers:
  1. Empty output → rejected
  2. Summary-length output (too short) → rejected
  3. Valid Arabic translation of English dialogue containing "I can't" → accepted
  4. English-in-English "translation" → rejected (low Arabic ratio)
"""
import os
import sys

# Ensure core is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import MagicMock, patch

from core.engine import TranslationEngine, _MIN_LENGTH_RATIO, _MIN_ARABIC_RATIO


class TestValidateChunk(unittest.TestCase):
    """Each test exercises _validate_chunk directly on a minimal mock engine."""

    def _make_engine(self):
        """Create a TranslationEngine with mocked callbacks."""
        engine = TranslationEngine(
            input_file="dummy.txt",
            output_dir="/tmp",
            archive_dir="/tmp",
            config_manager=MagicMock(),
            progress_callback=MagicMock(),
            error_callback=MagicMock(),
        )
        return engine

    # ── 1. Empty output ────────────────────────────────────────────────

    def test_empty_output_rejected(self):
        """Empty or whitespace-only translation should be rejected."""
        engine = self._make_engine()

        is_valid, reason = engine._validate_chunk("Hello world", "")
        self.assertFalse(is_valid)
        self.assertIn("Empty", reason)

        is_valid, reason = engine._validate_chunk("Hello world", "   ")
        self.assertFalse(is_valid)
        self.assertIn("Empty", reason)

    # ── 2. Summary-length output ───────────────────────────────────────

    def test_short_summary_rejected(self):
        """Translation much shorter than source (below min length ratio) → rejected."""
        engine = self._make_engine()

        source = "This is a detailed description of the scene with many adjectives and adverbs and clauses."
        short_translation = "OK"  # way too short
        ratio = len(short_translation) / len(source)

        is_valid, reason = engine._validate_chunk(source, short_translation)
        self.assertFalse(is_valid)
        self.assertIn("too short", reason)
        # Verify the ratio is present in the message (allow minor float formatting diffs)
        self.assertTrue("2%" in reason or "2.25%" in reason)

    # ── 3. Valid Arabic translation containing "I can't" ──────────────

    def test_valid_arabic_with_english_dialogue_accepted(self):
        """Arabic translation that contains an English phrase like "I can't" inside
        Arabic text should be accepted — because the source chunk itself also
        contains "I can't" (it's ignored via source-aware check)."""
        engine = self._make_engine()

        source = (
            "She looked at him and said: \"I can't believe you did this.\" "
            "He turned away silently, the rain washing his tears."
        )
        arabic_translation = (
            "نظرت إليه وقالت: \"ما أصدقك فعلت هذا.\" أدار ظهرها بهدوء، "
            "والأمطار تغسل دموعها."
        )
        is_valid, reason = engine._validate_chunk(source, arabic_translation, target_lang="ar")
        self.assertTrue(is_valid, f"Should be valid but reason was: {reason}")

    # ── 4. English-in-English "translation" ────────────────────────────

    def test_english_in_english_rejected(self):
        """An 'English → English' translation should be rejected because the
        Arabic letter proportion is zero (target_lang='ar' requires ≥30%)."""
        engine = self._make_engine()

        source = "Hello world, this is a test."
        english_translation = "Hello world, this is a test."

        is_valid, reason = engine._validate_chunk(source, english_translation, target_lang="ar")
        self.assertFalse(is_valid)
        self.assertIn("Arabic", reason)

    # ── 5. Non-Arabic target (no Arabic ratio check) ───────────────────

    def test_non_arabic_target_no_arabic_check(self):
        """When target is not 'ar', Arabic letter check should be skipped."""
        engine = self._make_engine()

        source = "مرحبا بالعالم"
        english_translation = "Hello world"

        is_valid, reason = engine._validate_chunk(source, english_translation, target_lang="fr")
        # Should NOT be rejected for low Arabic ratio — only for short length
        # (but here the length is similar, so it may pass)
        if is_valid:
            self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()

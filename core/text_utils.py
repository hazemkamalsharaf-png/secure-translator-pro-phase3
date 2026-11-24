"""
Text helpers for Secure Translator Pro.

- extract_translation / strip_thinking / strip_markdown : clean raw LLM output
- build_style_sample                                   : multi-point sample for the style profiler
- validate_chunk                                       : direction-aware output validation
- load_progress / append_progress / chunk_hash         : checkpoint + resume support
"""
import hashlib
import json
import os
import re

# ── Output cleaning ─────────────────────────────────────────────────────────
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.S | re.I)
_TRANSLATION_TAG = re.compile(r"<translation>(.*?)</translation>", re.S | re.I)
_OPEN_TAG = re.compile(r"<translation>", re.I)
_SCENE_BREAK = re.compile(r"^\s*([*_\-=~#]\s*){3,}$")


def strip_thinking(text):
    """Remove <think>…</think> reasoning blocks that some models leak into content."""
    text = text or ""
    text = _THINK_BLOCK.sub("", text)
    # Template that only emits the closing tag: everything before it is reasoning.
    if re.search(r"</think>", text, re.I):
        text = re.split(r"</think>", text, flags=re.I)[-1]
    # Unterminated reasoning block (cut off): nothing usable after it.
    if re.search(r"<think>", text, re.I):
        text = re.split(r"<think>", text, flags=re.I)[0]
    return text.strip()


def extract_translation(raw):
    """Return the text inside <translation>…</translation>, or the cleaned raw text."""
    text = strip_thinking(raw)
    matches = _TRANSLATION_TAG.findall(text)
    if matches:
        return max(matches, key=len).strip()
    m = _OPEN_TAG.search(text)
    if m:  # opening tag but no closing tag
        return text[m.end():].strip()
    return text.strip()


def strip_markdown(text):
    """Turn markdown the model may emit into plain text suitable for a .docx."""
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            out.append("")
            continue
        if _SCENE_BREAK.match(s):
            out.append("* * *")
            continue
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"__(.+?)__", r"\1", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", s)
        s = re.sub(r"`([^`]*)`", r"\1", s)
        out.append(s)
    return "\n".join(out).strip()


# ── Style sample ────────────────────────────────────────────────────────────
def build_style_sample(content, max_chars=6000):
    """Sample the start, middle and late part of the book (snapped to line breaks).

    A solemn prologue at the start of a book should not define the style of the
    whole book, so the profiler also sees ordinary narrative and dialogue.
    """
    content = (content or "").strip()
    if len(content) <= max_chars:
        return content
    part = max_chars // 3
    pieces = []
    for frac in (0.0, 0.45, 0.80):
        start = int(len(content) * frac)
        if start > 0:
            nl = content.find("\n", start)
            start = nl + 1 if nl != -1 else start
        end = min(start + part, len(content))
        pieces.append(content[start:end].strip())
    return "\n\n[…]\n\n".join(p for p in pieces if p)


# ── Validation ──────────────────────────────────────────────────────────────
# Expected (min, max) ratio of output words to source words, per direction.
_RATIO_RANGES = {
    ("ar", "en"): (0.85, 2.4),   # measured ≈1.4 on a real Arabic→English chapter
    ("en", "ar"): (0.40, 1.3),
}
_DEFAULT_RATIO = (0.60, 1.8)
_MAX_LEFTOVER_ARABIC = 0.10      # non-Arabic target: share of Arabic letters allowed
_MIN_ARABIC = 0.30               # Arabic target: share of Arabic letters required

_REFUSAL_START = re.compile(
    r"^(i\s*(can(no|')t|am\s+(sorry|unable)|'m\s+(sorry|unable))|i\s+apologi[sz]e|"
    r"as\s+an\s+ai|sure[,!. ]|certainly[,!. ]|here\s*('s|\s+is)\s+(the|a|your)\s+(translation|summary)|"
    r"the\s+following\s+is\s+(the|a)\s+translation|"
    r"عذر(اً|ا)\b|آسف|لا\s+(أستطيع|يمكنني)|إليك\s+الترجمة|بالتأكيد[،, ])",
    re.I,
)
_DIALOGUE_START = ('"', "“", "”", "«", "'", "‘", "-", "–", "—", "−")


def _arabic_share(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "\u0600" <= c <= "\u06FF") / len(letters)


def validate_chunk(source, translated, src_lang="en", tgt_lang="ar"):
    """Return (is_valid, reason)."""
    if not translated or not translated.strip():
        return False, "Empty translation output"
    if re.search(r"</?(think|translation)>", translated, re.I):
        return False, "Reasoning/format tags leaked into the output"

    sw, tw = len(source.split()), len(translated.split())
    lo, hi = _RATIO_RANGES.get((src_lang, tgt_lang), _DEFAULT_RATIO)
    ratio = tw / sw if sw else 0
    if ratio < lo:
        return False, f"Output too short (word ratio {ratio:.2f} < {lo}) — likely omissions"
    if ratio > hi:
        return False, f"Output too long (word ratio {ratio:.2f} > {hi}) — likely additions/commentary"

    share = _arabic_share(translated)
    if tgt_lang == "ar" and share < _MIN_ARABIC:
        return False, f"Arabic letter share too low ({share:.0%})"
    if tgt_lang != "ar" and share > _MAX_LEFTOVER_ARABIC:
        return False, f"Untranslated Arabic left in output ({share:.0%})"

    head = translated.strip()[:80]
    src_head = source.strip()[:1]
    if not head.startswith(_DIALOGUE_START) and src_head not in _DIALOGUE_START:
        if _REFUSAL_START.match(head):
            return False, f"Refusal/commentary pattern at start of output ({head[:30]!r})"
    return True, ""


# ── Checkpoint / resume ─────────────────────────────────────────────────────
def chunk_hash(chunk):
    return hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:12]


def load_progress(path):
    done = {}
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done[rec["idx"]] = rec
                except (ValueError, KeyError):
                    continue
    return done


def append_progress(path, idx, chunk, text, validated):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(
            {"idx": idx, "hash": chunk_hash(chunk), "text": text, "validated": bool(validated)},
            ensure_ascii=False) + "\n")

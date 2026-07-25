"""General lookup of CJK characters in the Unihan JSON database."""

import json
from functools import lru_cache
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "unihan_cache.json"


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def lookup(char: str) -> dict | None:
    """Returns the Unihan entry for a single CJK character, or None if unknown."""
    return _data().get(char)


NO_READING = "\u2015"

READING_ALIASES = {
    "korean": "korean_hangul",
    "japanese": "japanese_on",
}

# These shouldn't have a space after.
OPENING_PUNCT = {"（", "「", "『", "【", "《", "“", "‘"}
# Harder to tell these ones.
AMBIGUOUS_QUOTES = {'"', "'"}

FULLWIDTH_TO_ASCII = {
    "，": ",",
    "。": ".",
    "、": ",",
    "；": ";",
    "：": ":",
    "？": "?",
    "！": "!",
    "（": "(",
    "）": ")",
    "「": '"',
    "」": '"',
    "『": '"',
    "』": '"',
    "【": "[",
    "】": "]",
    "《": "<",
    "》": ">",
    "─": "\u2015",
}


def transliterate(text: str, reading: str) -> str:
    """Renders each character of `text` as its first `reading` pronunciation
    (e.g. "cantonese", "korean", "mandarin"). 

    Romanised readings are
    space-separated; Hangul (single-glyph) readings are run together like the source text.
    
    Characters with no entry, or no reading of the requested kind, becomes {NO_READING}.
    """
    reading = READING_ALIASES.get(reading, reading)
    use_ascii_punct = reading.startswith(("korean", "vietnamese", "cantonese", "mandarin"))
    no_word_spacing = reading == "korean_hangul"

    out = ""
    prev_was_word = False
    quote_is_opening = dict.fromkeys(AMBIGUOUS_QUOTES, True)
    for ch in text:
        if ch.isspace():
            # Whitespace is already a separator; collapse runs instead of
            # stacking with the punctuation-spacing logic below.
            if out and not out.endswith(" "):
                out += " "
            prev_was_word = False
            continue

        entry = lookup(ch)
        if entry is None:
            if ch in AMBIGUOUS_QUOTES:
                is_opening = quote_is_opening[ch]
                quote_is_opening[ch] = not is_opening
            else:
                is_opening = ch in OPENING_PUNCT

            if use_ascii_punct and is_opening and prev_was_word:
                out += " "
            out += FULLWIDTH_TO_ASCII.get(ch, ch) if use_ascii_punct else ch
            if use_ascii_punct and not is_opening:
                out += " "
            prev_was_word = False
            continue

        readings = entry.get("pronunciations", {}).get(reading)
        if prev_was_word and not no_word_spacing:
            out += " "
        out += readings[0] if readings else NO_READING
        prev_was_word = True
    return out if use_ascii_punct else out.rstrip()

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


NO_READING = "???"

READING_ALIASES = {
    "korean": "korean_hangul",
    "japanese": "japanese_on",
}

# Decide which chars hug the text before/after
OPENING_PUNCT = {"（", "「", "『", "【", "《", "“", "‘"}
CLOSING_PUNCT = {
    "。", "，", "、", "；", "：", "？", "！",
    "）", "」", "』", "】", "》", "”", "’",
    ".", ",", ";", ":", "?", "!", ")", "]", ">",
}
# Harder to tell these ones
AMBIGUOUS_QUOTES = {'"', "'"}
# Starts a new sentence for the Vietnamese capitalisation
SENTENCE_END = {"。", "？", "！", ".", "?", "!"}
# Quote openings
SPEECH_INTRODUCERS = {"：", ":"}
# Iteration/ditto marks
REPETITION_MARKS = {"々", "〻", "𖿣", "〃"}

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

WORD, OPEN, CLOSE = range(3)


def transliterate(text: str, reading: str) -> str:
    """Renders each character of `text` as its first `reading` pronunciation
    (e.g. "cantonese", "korean", "mandarin").

    Parameters
    ----------
    text : str
        The text to transliterate.
    reading : str
        The reading to use for transliteration. One of "cantonese", "korean", "mandarin", "japanese", "vietnamese" (so far).
    
    Returns
    -------
    str
        The transliterated text, with spacing and punctuation adjusted for the reading.
    """
    reading = READING_ALIASES.get(reading, reading)
    use_ascii_punct = reading.startswith(("korean", "vietnamese", "cantonese", "mandarin"))
    no_word_spacing = reading == "korean_hangul"
    capitalise_sentences = reading == "vietnamese"

    out = []
    prev_kind = None
    prev_char = None
    prev_passthrough = False
    pending_space = False
    start_of_sentence = True
    quote_is_opening = dict.fromkeys(AMBIGUOUS_QUOTES, True)

    for ch in text:
        if ch == "\n":
            # append for retaining linebreaks
            out.append("\n")
            prev_kind = None
            pending_space = False
            start_of_sentence = True
            continue
        if ch.isspace():
            # Remember the separation, but let the spacing rules below decide the fate
            pending_space = True
            continue

        lookup_char = prev_char if ch in REPETITION_MARKS and prev_char is not None else ch
        entry = lookup(lookup_char)
        passthrough = entry is None and ch not in AMBIGUOUS_QUOTES and ch not in OPENING_PUNCT and ch not in CLOSING_PUNCT

        if passthrough:
            # Not CJK or recognised punctuation (e.g. a Latin word, digits): left untouched.
            kind = WORD
            piece = ch
        elif entry is None:
            if ch in AMBIGUOUS_QUOTES:
                kind = OPEN if quote_is_opening[ch] else CLOSE
                quote_is_opening[ch] = not quote_is_opening[ch]
            elif ch in OPENING_PUNCT:
                kind = OPEN
            else:
                kind = CLOSE
            piece = FULLWIDTH_TO_ASCII.get(ch, ch) if use_ascii_punct else ch
            # Without ASCII punctuation the source is left as-is, glued to the
            # text on both sides, so it behaves like an opening mark.
            if not use_ascii_punct and kind != WORD:
                kind = OPEN
        else:
            kind = WORD
            readings = entry.get("pronunciations", {}).get(reading)
            piece = readings[0] if readings else NO_READING

        if kind == CLOSE:
            # Never separated from what it follows, however the source spaced it.
            space = False
        elif kind == OPEN:
            space = prev_kind in (WORD, CLOSE)
        elif prev_kind is None or prev_kind == OPEN:
            space = False
        elif prev_kind == CLOSE:
            space = True
        else:
            space = not no_word_spacing
        if passthrough and prev_passthrough:
            space = False
        if pending_space and prev_kind is not None and kind != CLOSE:
            space = True

        if kind == WORD and not passthrough and capitalise_sentences and start_of_sentence and piece:
            piece = piece[0].upper() + piece[1:]

        if space:
            out.append(" ")
        out.append(piece)

        if kind == WORD:
            start_of_sentence = False
        elif kind == OPEN:
            start_of_sentence = start_of_sentence or prev_char in SPEECH_INTRODUCERS
        elif ch in SENTENCE_END:
            start_of_sentence = True

        prev_kind = kind
        prev_char = ch
        prev_passthrough = passthrough
        pending_space = False

    return "".join(out)

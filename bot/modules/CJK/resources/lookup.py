"""General lookup of CJK characters in the Unihan JSON database."""

import json
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Literal, NewType, NotRequired, TypedDict

CACHE_FILE = Path(__file__).parent / "unihan_cache.json"

Char = NewType("Char", str)
"""A single character queried against the Unihan table (need not be CJK)."""
Codepoint = NewType("Codepoint", str)
"""A Unicode codepoint string, e.g. "U+4E00"."""
ReadingKey = NewType("ReadingKey", str)
"""A transliterate()/pronunciations key, e.g. "cantonese", "korean_hangul" and so on."""


class Variant(TypedDict):
    char: Char
    codepoint: Codepoint


class Readings(TypedDict, total=False):
    kDefinition: str


class Pronunciations(TypedDict, total=False):
    cantonese: list[str]
    mandarin: list[str]
    japanese_on: list[str]
    japanese_kun: list[str]
    korean_hangul: list[str]
    korean_romanized: list[str]
    vietnamese: list[str]


class Designations(TypedDict, total=False):
    korean_education: str
    korean_name: bool
    hanja_exam: str
    joyo: str
    jinmeiyo: bool
    hong_kong_grade: str
    tgh_level: Literal[1, 2, 3]


class UnihanEntry(TypedDict):
    char: Char
    codepoint: Codepoint
    readings: Readings
    variants: dict[str, list[Variant]]
    pronunciations: NotRequired[Pronunciations]
    designations: NotRequired[Designations]


@lru_cache(maxsize=1)
def _data() -> dict[Char, UnihanEntry]:
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))


def lookup(char: Char) -> UnihanEntry | None:
    """Returns the Unihan entry for a single CJK character, or None if unknown."""
    return _data().get(char)


NO_READING = "???"

READING_ALIASES: dict[ReadingKey, ReadingKey] = {
    ReadingKey("korean"): ReadingKey("korean_hangul"),
    ReadingKey("japanese"): ReadingKey("japanese_on"),
}

# Decide which chars hug the text before/after
OPENING_PUNCT = {"（", "「", "『", "【", "《", "“", "‘"}
CLOSING_PUNCT = {
    "。",
    "，",
    "、",
    "；",
    "：",
    "？",
    "！",
    "）",
    "」",
    "』",
    "】",
    "》",
    "”",
    "’",
    ".",
    ",",
    ";",
    ":",
    "?",
    "!",
    ")",
    "]",
    ">",
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


class PieceKind(Enum):
    WORD = auto()
    OPEN = auto()
    CLOSE = auto()


def transliterate(text: str, reading: ReadingKey) -> str:
    """Renders each character of `text` as its first `reading` pronunciation
    (e.g. "cantonese", "korean", "mandarin").

    Parameters
    ----------
    text : str
        The text to transliterate.
    reading : ReadingKey
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

    out: list[str] = []
    prev_kind: PieceKind | None = None
    prev_char: str | None = None
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
        entry = lookup(Char(lookup_char))
        passthrough = (
            entry is None and ch not in AMBIGUOUS_QUOTES and ch not in OPENING_PUNCT and ch not in CLOSING_PUNCT
        )

        if passthrough:
            # Not CJK or recognised punctuation (e.g. a Latin word, digits): left untouched.
            kind = PieceKind.WORD
            piece = ch
        elif entry is None:
            if ch in AMBIGUOUS_QUOTES:
                kind = PieceKind.OPEN if quote_is_opening[ch] else PieceKind.CLOSE
                quote_is_opening[ch] = not quote_is_opening[ch]
            elif ch in OPENING_PUNCT:
                kind = PieceKind.OPEN
            else:
                kind = PieceKind.CLOSE
            piece = FULLWIDTH_TO_ASCII.get(ch, ch) if use_ascii_punct else ch
            # Without ASCII punctuation the source is left as-is, glued to the
            # text on both sides, so it behaves like an opening mark.
            if not use_ascii_punct and kind != PieceKind.WORD:
                kind = PieceKind.OPEN
        else:
            kind = PieceKind.WORD
            readings = entry.get("pronunciations", {}).get(reading)
            piece = readings[0] if readings else NO_READING

        if kind == PieceKind.CLOSE:
            # Never separated from what it follows, however the source spaced it.
            space = False
        elif kind == PieceKind.OPEN:
            space = prev_kind in (PieceKind.WORD, PieceKind.CLOSE)
        elif prev_kind is None or prev_kind == PieceKind.OPEN:
            space = False
        elif prev_kind == PieceKind.CLOSE:
            space = True
        else:
            space = not no_word_spacing
        if passthrough and prev_passthrough:
            space = False
        if pending_space and prev_kind is not None and kind != PieceKind.CLOSE:
            space = True

        if kind == PieceKind.WORD and not passthrough and capitalise_sentences and start_of_sentence and piece:
            piece = piece[0].upper() + piece[1:]

        if space:
            out.append(" ")
        out.append(piece)

        if kind == PieceKind.WORD:
            start_of_sentence = False
        elif kind == PieceKind.OPEN:
            start_of_sentence = start_of_sentence or prev_char in SPEECH_INTRODUCERS
        elif ch in SENTENCE_END:
            start_of_sentence = True

        prev_kind = kind
        prev_char = ch
        prev_passthrough = passthrough
        pending_space = False

    return "".join(out)

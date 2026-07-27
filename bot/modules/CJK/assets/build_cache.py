"""One-time build script: parses Unihan_Readings.txt and Unihan_Variants.txt
into a single dict keyed by character, and writes it out as unihan_cache.json.

Run this whenever the source Unihan_*.txt files are updated:
    python build_cache.py
"""

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

DATA_DIR = Path(__file__).parent
SOURCE_DIR = DATA_DIR / "resources"
READINGS_FILE = SOURCE_DIR / "Unihan_Readings.txt"
VARIANTS_FILE = SOURCE_DIR / "Unihan_Variants.txt"
EQUIVALENT_UNIFIED_IDEOGRAPH_FILE = SOURCE_DIR / "EquivalentUnifiedIdeograph.txt"  # for more Spoofs!
OTHER_MAPPINGS_FILE = SOURCE_DIR / "Unihan_OtherMappings.txt"
DICTIONARY_LIKE_FILE = SOURCE_DIR / "Unihan_DictionaryLikeData.txt"
KOREAN_EDUCATION_FILE = SOURCE_DIR / "korean_education_level.json"
HANJA_EXAM_FILE = SOURCE_DIR / "hanja_exam_level.json"
KANJI_LEVEL_FILE = SOURCE_DIR / "kanji_level.json"
KANJIDICTVN_FILES = [
    SOURCE_DIR / "KanjiDictVN_kanji_bank_1.json",
    SOURCE_DIR / "KanjiDictVN_kanji_bank_2.json",
]
HANGUL_TABLE_FILE = SOURCE_DIR / "table.json"
SHINJITAI_FILE = SOURCE_DIR / "shinjitai.json"
KYUJITAI_FILE = SOURCE_DIR / "kyujitai.json"
CACHE_FILE = DATA_DIR.parent / "resources" / "unihan_cache.json"

VARIANT_TOKEN_RE = re.compile(r"^(U\+[0-9A-Fa-f]+)((?:<[A-Za-z0-9,]+)?)$")
EQUIVALENT_UNIFIED_IDEOGRAPH_RE = re.compile(
    r"^([0-9A-Fa-f]{4,6})(?:\.\.([0-9A-Fa-f]{4,6}))?\s*;\s*([0-9A-Fa-f]{4,6})",
)
VN_GLOSS_READING_RE = re.compile(r"^\[([^\]]+)\]")
PINLU_RE = re.compile(r"^(.+?)\((\d+)\)$")
# CCCII to infer from (to override Uniihan)
CCCII_VARIANT_FIELD = "kCCCIIVariant"

# Reading fields that consolidate "pronunciations"
PRONUNCIATION_SOURCE_FIELDS = {
    "kCantonese",
    "kHangul",
    "kHanyuPinlu",
    "kHanyuPinyin",
    "kJapanese",
    "kJapaneseKun",
    "kJapaneseOn",
    "kKorean",
    "kMandarin",
    "kSMSZD2003Readings",
    "kTGHZ2013",
    "kVietnamese",
    "kXHC1983",
}

# fields to keep as a single string
SINGLE_VALUE_READING_FIELDS = {"kDefinition"}


def clean_reading_value(field: str, value: str) -> str | list[str]:
    if field in SINGLE_VALUE_READING_FIELDS:
        return value
    return dedup(value.split())


def dedup(seq: Sequence[str]) -> list[str]:
    """Deduplicates a sequence while preserving order."""
    return list(dict.fromkeys(seq))


def codepoint_to_char(codepoint: str) -> str:
    return chr(int(codepoint.replace("U+", "0x"), 0))


def parse_unihan_file(path: Path):
    """Yields (codepoint, field, value) for each data line in a Unihan_*.txt file."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            codepoint, field, value = line.split("\t", 2)
            yield codepoint, field, value


def extract_location_pinyin(value: str) -> list[str]:
    """
    Extract the pinyin readings from a Unihan location-based field.

    This is because `kHanyuPinyin`/`kXHC1983`/`kTGHZ2013` tokens look like "10019.020:tiàn" or
    "31606.080:yú,yóu", possibly multiple space-separated.

    Parameter
    ---------
    value: str
        The value of a Unihan location-based field.

    Returns
    -------
    pinyin: list[str]
        List of pinyin readings extracted from the input value.

    """
    pinyin = []
    for token in value.split():
        if ":" not in token:
            continue
        _, pinyin_part = token.split(":", 1)
        pinyin.extend(p for p in pinyin_part.split(",") if p)
    return pinyin


def extract_smszd(value: str) -> tuple[list[str], list[str]]:
    """
    Extract the Mandarin and Cantonese readings from a Unihan kSMSZD2003Readings field.

    `kSMSZD2003Readings` tokens look like `zhòu粵zau3` i.e. `<mandarin>粵<cantonese>`,
    so we split on the `粵` character to separate the two readings.

    Parameter
    ---------
    value: str
        The value of a Unihan kSMSZD2003Readings field.

    Returns
    -------
    mandarin: list[str]
        List of Mandarin readings extracted from the input value.
    cantonese: list[str]
        List of Cantonese readings extracted from the input value.
    """
    mandarin, cantonese = [], []
    for token in value.split():
        if "粵" not in token:
            continue
        mandarin_part, cantonese_part = token.split("粵", 1)
        mandarin.extend(p for p in mandarin_part.split(",") if p)
        cantonese.extend(p for p in cantonese_part.split(",") if p)
    return mandarin, cantonese


def load_kanjidictvn() -> tuple[dict[str, list[str]], dict[str, Counter]]:
    """
    Loads and extracts the Han-Viet readings from KanjiDictVN, returning a mapping of character to readings.

    KanjiDictVN (https://github.com/trungnt2910/KanjiDictVN) is a
    curated Han-Viet reading dataset covering 10K commonly Han Viet characters,
    derived from KANJIDIC + hvdic.thivien.net.
    I found it in search for ameliorating Unihan's `kVietnamese` field which was in itself
    quite destitute. It seems to be much higher quality, so we prefer it
    where available and fall back to `kVietnamese`.

    Briefly, each Yomitan kanji-bank row is [char, readings, "", "", meanings, stats];
    readings is a space-separated string, empty when KanjiDictVN has none.
    Readings are therefore ordered by gloss count, keeping alphabetical order as a stable tiebreaker.

    Returns
    -------
    readings_by_char: dict[str, list[str]]
        Mapping of character to list of Han-Viet readings.
    senses_by_char: dict[str, Counter]
        Mapping of character to a Counter of gloss counts per reading.
    """
    readings_by_char: dict[str, list[str]] = {}
    senses_by_char: dict[str, Counter] = {}
    for path in KANJIDICTVN_FILES:
        rows = json.loads(path.read_text(encoding="utf-8"))
        for char, readings, _, _, glosses, *_ in rows:
            if not readings:
                continue
            readings_by_char[char] = dedup(readings.split())
            senses = Counter()
            for gloss in glosses or []:
                m = VN_GLOSS_READING_RE.match(gloss)
                if m:
                    senses[m.group(1)] += 1
            if senses:
                senses_by_char[char] = senses
    return readings_by_char, senses_by_char


def load_hangul_table() -> dict[str, str]:
    """Loads `table.json` as a supplementary char-to-single Hangul-syllable reading map
    (27k+ entries), merged into korean_hangul alongside Unihan's kHangul.

    Returns
    -------
    hangul_table: dict[str, str]
        Mapping of character to Hangul reading.
    """
    with HANGUL_TABLE_FILE.open(encoding="utf-8-sig") as f:
        return json.load(f)


def extract_pinlu(value: str) -> list[tuple[str, int]]:
    """
    Extract pinyin from Unihan `kHanyuPinlu` field.

    Returns
    -------
    out: list[tuple[str, int]]
        List of (pinyin, frequency) tuples extracted from the input value.
    """
    out = []
    for token in value.split():
        m = PINLU_RE.match(token)
        if m:
            out.append((m.group(1), int(m.group(2))))
    return out


def load_shinjitai_kyujitai_pairs() -> set[tuple[str, str]]:
    """
    Loads two JSON files mapping Shinjitai <-> Kyujitai pairs, returning a set of (Shinjitai, Kyujitai) tuples.

    Returns
    -------
    pairs: set[tuple[str, str]]
        Set of (Shinjitai, Kyujitai) character pairs.
    """
    pairs: set[tuple[str, str]] = set()
    shin = json.loads(SHINJITAI_FILE.read_text(encoding="utf-8-sig"))
    for shin_char, kyu_chars in shin.items():
        for kyu_char in kyu_chars or []:
            pairs.add((shin_char, kyu_char))
    kyu = json.loads(KYUJITAI_FILE.read_text(encoding="utf-8-sig"))
    for kyu_char, shin_char in kyu.items():
        if shin_char:
            pairs.add((shin_char, kyu_char))
    return pairs


def apply_shinjitai_kyujitai_variants(entries: dict[str, dict]) -> None:
    """
    Records each Shinjitai/Kyujitai pair as a variant link on both
    characters, skipping pairs involving a CJK Compatibility Ideograph.

    Used for inferring Shinjitai <-> Traditional variants.

    Parameter
    ---------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which will be updated in-place with variant links.
    """

    def add_variant(char: str, field: str, other_char: str) -> None:
        variant_list = entries[char]["variants"].setdefault(field, [])
        if not any(v["char"] == other_char for v in variant_list):
            variant_list.append(
                {"char": other_char, "codepoint": entries[other_char]["codepoint"], "source": None},
            )

    for shin_char, kyu_char in load_shinjitai_kyujitai_pairs():
        if shin_char not in entries or kyu_char not in entries:
            continue
        add_variant(kyu_char, "kJapaneseNewVariant", shin_char)
        add_variant(shin_char, "kTraditionalVariant", kyu_char)


def load_equivalent_unified_ideographs() -> list[tuple[str, str]]:
    """
    Parses EquivalentUnifiedIdeograph.txt into (radical_or_stroke_char, target_char) pairs.

    Returns
    -------
    pairs: list[tuple[str, str]]
        A (radical/stroke character, equivalent Unihan character) pair for every codepoint
        covered, with ranges expanded to individual pairs.
    """
    pairs = []
    with EQUIVALENT_UNIFIED_IDEOGRAPH_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            m = EQUIVALENT_UNIFIED_IDEOGRAPH_RE.match(line)
            if not m:
                continue
            start, end, target = m.group(1), m.group(2) or m.group(1), m.group(3)
            target_char = chr(int(target, 16))
            pairs.extend((chr(cp), target_char) for cp in range(int(start, 16), int(end, 16) + 1))
    return pairs


def apply_equivalent_unified_ideograph_variants(entries: dict[str, dict]) -> None:
    """
    Folds EquivalentUnifiedIdeograph.txt's CJK radical/stroke mappings into kSpoofingVariant.

    Per UAX #38, kSpoofingVariant is symmetric and transitive, so a radical/stroke visually
    equivalent to one member of an existing spoofing-variant cluster is recorded against every
    member of that cluster, not just the specific character named in the source file. Radicals
    and strokes aren't Unihan characters, so we don't mint entries for them; the link is
    one-directional, showing up under the ideograph's "Confused for" only.

    Parameters
    ----------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which will be updated in-place with new
        kSpoofingVariant links.
    """
    parent: dict[str, str] = {}

    def find(char: str) -> str:
        parent.setdefault(char, char)
        while parent[char] != char:
            parent[char] = parent[parent[char]]
            char = parent[char]
        return char

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for char, entry in entries.items():
        for variant in entry["variants"].get("kSpoofingVariant", []):
            union(char, variant["char"])

    clusters: dict[str, set[str]] = defaultdict(set)
    for char in parent:
        clusters[find(char)].add(char)

    for radical_char, target_char in load_equivalent_unified_ideographs():
        if target_char not in entries:
            continue
        cluster = clusters.get(find(target_char), {target_char})
        for member in cluster:
            variant_list = entries[member]["variants"].setdefault("kSpoofingVariant", [])
            if not any(v["char"] == radical_char for v in variant_list):
                variant_list.append(
                    {"char": radical_char, "codepoint": f"U+{ord(radical_char):04X}", "source": None},
                )


def load_cccii_groups() -> list[set[str]]:
    """Groups characters that CCCII treats as forms of the same character.

    Returns
    -------
    groups: list[set[str]]
        List of sets of codepoints, each set representing a group of characters that CCCII treats as forms of the same character. Only groups with more than one member are included.
    """
    codes: dict[str, set[str]] = defaultdict(set)
    for codepoint, field, value in parse_unihan_file(OTHER_MAPPINGS_FILE):
        if field in ("kCCCII", "kEACC"):
            codes[codepoint].update(value.split())

    groups: dict[tuple, set[str]] = defaultdict(set)
    for codepoint, values in codes.items():
        for code in values:
            groups[((int(code[0:2], 16) - 0x21) % 12, code[2:4], code[4:6])].add(codepoint)
    return [group for group in groups.values() if len(group) > 1]


def shares_a_reading(a: dict, b: dict) -> bool:
    """Whether two entries agree on any reading, or on their definition."""
    a_pron, b_pron = a.get("pronunciations", {}), b.get("pronunciations", {})
    if any(set(a_pron.get(cat, ())) & set(b_pron.get(cat, ())) for cat in PRONUNCIATION_CATEGORIES):
        return True
    a_definition = a.get("readings", {}).get("kDefinition")
    b_definition = b.get("readings", {}).get("kDefinition")
    return bool(a_definition and a_definition == b_definition)


def apply_cccii_variants(entries: dict[str, dict]) -> int:
    """Records CCCII's groupings as variant links, keeping only pairs that also
    agree on a reading or a definition.

    The positional rule on its own is roughly 80% precise: 卌 and 軈 land in the
    same slot with no relationship whatsoever, as do 樮 and 遺. Requiring
    agreement drops those while keeping the pairs worth having, and costs about
    150 of the 862 candidates.

    Kept separate from Unihan's own variant fields because CCCII says only that
    two glyphs are the same character, never in what sense, and separate from
    VARIANT_FALLBACK_FIELDS so this changes no readings.
    """
    added = 0
    for group in load_cccii_groups():
        chars = [codepoint_to_char(codepoint) for codepoint in group]
        for char in chars:
            if char not in entries:
                continue
            for other in chars:
                if other == char or other not in entries:
                    continue
                if not shares_a_reading(entries[char], entries[other]):
                    continue
                # Any kSemanticVariant beats an untyped CCCII link, so remove dups
                if any(
                    v["char"] == other
                    for field, vs in entries[char]["variants"].items()
                    if field != CCCII_VARIANT_FIELD
                    for v in vs
                ):
                    continue
                variant_list = entries[char]["variants"].setdefault(CCCII_VARIANT_FIELD, [])
                if not any(v["char"] == other for v in variant_list):
                    variant_list.append(
                        {"char": other, "codepoint": entries[other]["codepoint"], "source": "CCCII"},
                    )
                    added += 1
    return added


def load_japan_specific() -> set[str]:
    """
    Codepoints for glyphs only Japan treats as current.

    kUnihanCore2020 lists the regions that consider a character part of their
    core set, and the Japan-only forms come out as exactly "HJ" (H being HK, but that's because it's broad enough to pick up other variants).

    Returns
    -------
    japan_specific: set[str]
        Set of codepoints for glyphs that are only considered current in Japan.
    """
    japan_specific = set()
    for codepoint, field, value in parse_unihan_file(DICTIONARY_LIKE_FILE):
        if field == "kUnihanCore2020":
            regions = set(value.strip())
            if "J" in regions and regions <= {"H", "J"}:
                japan_specific.add(codepoint)
    return japan_specific


def retype_japanese_variants(entries: dict[str, dict]) -> int:
    """
    Re-files links pointing at a Japan-only glyph under `kJapaneseNewVariant` (Shinjitai).

    Only fires when the source glyph is not itself Japan-only.

    Parameters
    ----------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which contains pronunciations and variants.

    Returns
    -------
    retyped: int
        The number of variant links that were retyped to `kJapaneseNewVariant`.
    """
    japan_specific = load_japan_specific()
    retyped: list[tuple[str, str]] = []

    def move(entry: dict, other_char: str, to_field: str) -> bool:
        moved = False
        for field, variants in list(entry["variants"].items()):
            if field == to_field:
                continue
            for variant in list(variants):
                if variant["char"] != other_char:
                    continue
                variants.remove(variant)
                target = entry["variants"].setdefault(to_field, [])
                if not any(v["char"] == other_char for v in target):
                    target.append(variant)
                moved = True
            if not variants:
                del entry["variants"][field]
        return moved

    for char, entry in entries.items():
        if entry["codepoint"] in japan_specific:
            continue
        for variant in [v for vs in entry["variants"].values() for v in vs]:
            if variant["codepoint"] in japan_specific:
                retyped.extend([(char, variant["char"])])

    for char, japanese_char in retyped:
        move(entries[char], japanese_char, "kJapaneseNewVariant")
        # Keep the pair symmetric, the way the shinjitai table records it when the other side is traditional.
        if japanese_char in entries and not entries[char]["variants"].get("kTraditionalVariant"):
            move(entries[japanese_char], char, "kTraditionalVariant")
    return len(retyped)


# Only pair that clashes between unihan and official list
KOREAN_EDUCATION_COGNATES = {"𮕩": "衰"}


def load_level_designations_sources() -> tuple[dict, dict, dict]:
    """
    Loads the three level lists.

    Returns
    -------
    korean_education: dict
        Mapping of educational tiers to their character blocks for Korean Hanja (1800 basic educational hanja).
    hanja_exam: dict
        Mapping of exam levels to their character blocks for Hanja Exam levels (from 社團法人韓國語文會).
    kanji_level: dict
        Mapping of grade levels to their character blocks for Kanji levels (from 文部科学省).
    """
    korean_education = json.loads(KOREAN_EDUCATION_FILE.read_text(encoding="utf-8"))
    hanja_exam = json.loads(HANJA_EXAM_FILE.read_text(encoding="utf-8"))
    kanji_level = json.loads(KANJI_LEVEL_FILE.read_text(encoding="utf-8"))
    return korean_education, hanja_exam, kanji_level


def apply_level_designations(entries: dict[str, dict]) -> None:
    """
    Records the lists and levels a character is designated under.

    Parameters
    ----------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which will be updated in-place with level designations.
    """
    korean_education, hanja_exam, kanji_level = load_level_designations_sources()

    education_tier = {}
    for block in korean_education.values():
        for char in block["characters"]:
            education_tier[char] = block["name"]

    exam_level = {char: block["name"] for block in hanja_exam.values() for char in block["characters"]}
    kanji_grade = {char: block["name"] for block in kanji_level.values() for char in block["characters"]}
    name_only = set(kanji_level.get("nameonly", {}).get("characters", ()))

    education_hanja, korean_name = set(), set()
    tgh_index: dict[str, int] = {}
    for codepoint, field, value in parse_unihan_file(OTHER_MAPPINGS_FILE):
        if field == "kKoreanEducationHanja":
            education_hanja.add(codepoint)
        elif field == "kKoreanName":
            korean_name.add(codepoint)
        elif field == "kTGH":
            # looks like "2013:6602"
            # 2013 means published in 2013
            # latter is the index
            # 1-3500 is 一级,
            # 3501-6500 is 二级
            # 6501-8105 is 三级
            tgh_index[codepoint] = int(value.split(":", 1)[1])

    hong_kong_grade = {
        codepoint: value.strip()
        for codepoint, field, value in parse_unihan_file(DICTIONARY_LIKE_FILE)
        if field == "kGradeLevel"
    }

    unresolved = []
    for char, entry in entries.items():
        designations = {}

        if entry["codepoint"] in education_hanja:
            tier = education_tier.get(char) or education_tier.get(
                KOREAN_EDUCATION_COGNATES.get(char, ""),
            )
            if tier is None:
                # Try the same character written at another codepoint.
                for variants in entry["variants"].values():
                    for variant in variants:
                        if variant["char"] in education_tier:
                            tier = education_tier[variant["char"]]
                            break
                    if tier:
                        break
            if tier is None:
                unresolved.append(char)
            designations["korean_education"] = tier or "기초 한자"

        if entry["codepoint"] in korean_name:
            designations["korean_name"] = True
        if char in exam_level:
            designations["hanja_exam"] = exam_level[char]
        if char in kanji_grade and char not in name_only:
            designations["joyo"] = kanji_grade[char]
        if char in name_only:
            designations["jinmeiyo"] = True
        if grade := hong_kong_grade.get(entry["codepoint"]):
            designations["hong_kong_grade"] = grade
        if index := tgh_index.get(entry["codepoint"]):
            designations["tgh_level"] = 1 if index <= 3500 else 2 if index <= 6500 else 3

        if designations:
            entry["designations"] = designations

    if unresolved:
        print(f"  no school tier for {len(unresolved)} educational hanja: {''.join(unresolved)}")  # noqa: T201


# Preference order for borrowing a reading from a related character when the
# character itself has no direct entry
VARIANT_FALLBACK_FIELDS = [
    "kJapaneseNewVariant",
    "kSemanticVariant",
    "kSimplifiedVariant",
    "kTraditionalVariant",
    "kZVariant",
]


def kanjidictvn_lookup(
    char: str,
    variants: dict[str, list[dict]],
    kanjidictvn: dict[str, list[str]],
) -> tuple[list[str], str | None]:
    """
    Looks up the Han-Viet readings for `char` in KanjiDictVN, falling back to
    its variants if necessary.

    Parameters
    ----------
    char: str
        The character to look up.
    variants: dict[str, list[dict]]
        Mapping of variant field names to lists of variant dicts for `char`.
    kanjidictvn: dict[str, list[str]]
        Mapping of characters to their Han-Viet readings from KanjiDictVN.

    Returns
    -------
    readings: list[str]
        List of Han-Viet readings for `char`, or an empty list if none found.
    source_char: str | None
        The character from which the readings were obtained (either `char` itself or a variant), or None if no readings were found.
    """
    if char in kanjidictvn:
        return kanjidictvn[char], char
    for field in VARIANT_FALLBACK_FIELDS:
        for variant in variants.get(field, []):
            readings = kanjidictvn.get(variant["char"])
            if readings:
                return readings, variant["char"]
    return [], None


VIETNAMESE_TONES = {
    "̀": "huyen",
    "́": "sac",
    "̉": "hoi",
    "̃": "nga",
    "̣": "nang",
}


def split_vietnamese(syllable: str) -> tuple[str, str]:
    """
    Decomposes a Vietnamese syllable into its toneless base and tone name.

    Inferrs tone names from the following table:

    | Tone | Name |
    |:---:|:---:|
    | ̀ | huyen |
    | ́ | sac |
    | ̉ | hoi |
    | ̃ | nga |
    | ̣ | nang |

    Example
    -------
    ```python
    split_vietnamese("hành")
    >>> ("hanh", "huyen")
    ```

    Parameter
    ---------
    syllable: str
        A Vietnamese syllable, possibly with diacritics indicating tone.

    Returns
    -------
    base: str
        The toneless base of the syllable, with diacritics removed.
    tone: str
        The name of the tone associated with the syllable, one of "ngang", "sac", "huyen", "hoi", "nga", or "nang".
    """
    base = ""
    tone = "ngang"
    for ch in unicodedata.normalize("NFD", syllable):
        if ch in VIETNAMESE_TONES:
            tone = VIETNAMESE_TONES[ch]
        else:
            base += ch
    return unicodedata.normalize("NFC", base), tone


def rank_vietnamese(
    entries: dict[str, dict],
    senses_by_char: dict[str, Counter],
    vietnamese_source: dict[str, str],
) -> int:
    """
    Orders ambiguous Han-Viet readings by gloss count, breaking ties with Cantonese as a pivot.

    Upon analysis, gloss count is a stronger signal but has ties often e.g., 子 carries two senses each
    for tý and tử - and alphabetical order is no way to settle those.
    Cantonese is a good reference because it and Sino-Vietnamese both descend from
    Middle Chinese and preserve its finals and tone categories closely, and
    regularly enough to learn the correspondence straight from the characters that are unambiguous
    in both (Cantonese tone 1 -> ngang, 2 -> hoi, 3 -> sac, 5 -> nga, 6 -> nang,
    and so on).
    Base and tone are modelled separately, since a joint syllable model is far too sparse to be useful.

    Runs before `apply_variant_fallback()` so borrowed readings inherit the ranking
    rather than needing one of their own.

    Parameters
    ----------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which contains pronunciations and variants.
    senses_by_char: dict[str, Counter]
        Mapping of character to a Counter of gloss counts per Han-Viet reading.
    vietnamese_source: dict[str, str]
        Mapping of character to the source character from which its Han-Viet readings were obtained (either itself or a variant).

    Returns
    -------
    reranked: int
        The number of characters whose Han-Viet readings were reranked.
    """

    def split_jyutping(syllable: str) -> tuple[str, str]:
        """
        Splits a Jyutping syllable into its base and tone number.
        """
        return (syllable[:-1], syllable[-1]) if syllable[-1:].isdigit() else (syllable, "?")

    base_model: dict[str, Counter] = defaultdict(Counter)
    tone_model: dict[str, Counter] = defaultdict(Counter)
    for entry in entries.values():
        pronunciations = entry.get("pronunciations", {})
        cantonese, vietnamese = pronunciations.get("cantonese"), pronunciations.get("vietnamese")
        if not (cantonese and vietnamese and len(cantonese) == 1 and len(vietnamese) == 1):
            continue
        cantonese_base, cantonese_tone = split_jyutping(cantonese[0])
        vietnamese_base, vietnamese_tone = split_vietnamese(vietnamese[0])
        base_model[cantonese_base][vietnamese_base] += 1
        tone_model[cantonese_tone][vietnamese_tone] += 1

    def log_prob(counts: Counter, key: str) -> float:
        """
        Computes the log probability of `key` given the counts in `counts`, with additive smoothing to avoid zero probabilities.
        """
        total = sum(counts.values())
        return math.log((counts[key] + 0.1) / (total + 1.0)) if total else 0.0

    reranked = 0
    for char, entry in entries.items():
        pronunciations = entry.get("pronunciations", {})
        vietnamese = pronunciations.get("vietnamese")
        if not vietnamese or len(vietnamese) < 2:
            continue
        # Readings borrowed from a variant are scored against that variant's glosses.
        senses = senses_by_char.get(vietnamese_source.get(char, char), Counter())
        cantonese = pronunciations.get("cantonese")
        cantonese_base, cantonese_tone = split_jyutping(cantonese[0]) if cantonese else ("", "?")

        def pivot_score(reading: str, cb: str = cantonese_base, ct: str = cantonese_tone) -> float:
            base, tone = split_vietnamese(reading)
            return log_prob(base_model[cb], base) + log_prob(tone_model[ct], tone)

        pronunciations["vietnamese"] = sorted(
            vietnamese,
            key=lambda r: (-senses[r], -pivot_score(r)),
        )
        reranked += 1
    return reranked


def build_pronunciations(
    raw: dict[str, str],
    char: str,
    variants: dict[str, list[dict]],
    kanjidictvn: dict[str, list[str]],
    hangul_table: dict[str, str],
    vietnamese_source: dict[str, str],
) -> dict[str, list[str]]:
    """
    Builds a dict of pronunciations for a character from its raw Unihan readings,
    KanjiDictVN readings, and Hangul table, deduplicating and ordering them appropriately.

    Parameters
    ----------
    raw: dict[str, str]
        Raw Unihan readings for the character, keyed by field name.
    char: str
        The character for which pronunciations are being built.
    variants: dict[str, list[dict]]
        Mapping of variant field names to lists of variant dicts for the character.
    kanjidictvn: dict[str, list[str]]
        Mapping of characters to their Han-Viet readings from KanjiDictVN.
    hangul_table: dict[str, str]
        Mapping of characters to their Hangul readings from the supplementary table.
    vietnamese_source: dict[str, str]
        Mapping of characters to the source character from which their Han-Viet readings were obtained (either themselves or a variant).

    Returns
    -------
    pronunciations: dict[str, list[str]]
        Mapping of pronunciation categories to lists of readings for the character.
    """
    smszd_mandarin, smszd_cantonese = extract_smszd(raw.get("kSMSZD2003Readings", ""))
    hangul_extra = hangul_table.get(char)
    vietnamese, vietnamese_from = kanjidictvn_lookup(char, variants, kanjidictvn)
    if vietnamese_from:
        vietnamese_source[char] = vietnamese_from

    pinlu = extract_pinlu(raw.get("kHanyuPinlu", ""))
    mandarin = dedup(
        raw.get("kMandarin", "").split()
        + [reading for reading, _ in sorted(pinlu, key=lambda p: -p[1])]
        + smszd_mandarin
        + extract_location_pinyin(raw.get("kHanyuPinyin", ""))
        + extract_location_pinyin(raw.get("kXHC1983", ""))
        + extract_location_pinyin(raw.get("kTGHZ2013", "")),
    )

    pronunciations = {
        "cantonese": dedup(raw.get("kCantonese", "").split() + smszd_cantonese),
        "mandarin": mandarin,
        "japanese_on": dedup(raw.get("kJapaneseOn", "").split()),
        "japanese_kun": dedup(raw.get("kJapaneseKun", "").split()),
        # prioritise table.json over kHangul
        "korean_hangul": dedup(
            ([hangul_extra] if hangul_extra else []) + [tok.split(":", 1)[0] for tok in raw.get("kHangul", "").split()],
        ),
        "korean_romanized": dedup(raw.get("kKorean", "").split()),
        "vietnamese": vietnamese or dedup(raw.get("kVietnamese", "").split()),
    }
    return {k: v for k, v in pronunciations.items() if v}


PRONUNCIATION_CATEGORIES = [
    "cantonese",
    "mandarin",
    "japanese_on",
    "japanese_kun",
    "korean_hangul",
    "korean_romanized",
    "vietnamese",
]


def apply_variant_fallback(entries: dict[str, dict], max_rounds: int = 5) -> None:
    """
    Fills in the missing pronunciation categories for characters by borrowing from known cognates.

    For exampe, Unihan provides no `korean_hangul` for `為` but its `kSemanticVariant`, `爲` does, so we can borrow that reading.

    Parameters
    ----------
    entries: dict[str, dict]
        Mapping of character to its entry dict, which contains pronunciations and variants.
    max_rounds: int
        The maximum number of rounds to perform when filling in missing pronunciations. Each round attempts to fill in missing pronunciations by borrowing from linked variant characters, and the process stops if no further changes are made in a round.
    """
    for entry in entries.values():
        entry.setdefault("pronunciations", {})

    for _ in range(max_rounds):
        snapshot = {char: dict(entry["pronunciations"]) for char, entry in entries.items()}
        changed = False
        for entry in entries.values():
            pronunciations = entry["pronunciations"]
            for category in PRONUNCIATION_CATEGORIES:
                if pronunciations.get(category):
                    continue
                for field in VARIANT_FALLBACK_FIELDS:
                    borrowed = None
                    for variant in entry["variants"].get(field, []):
                        borrowed = snapshot.get(variant["char"], {}).get(category)
                        if borrowed:
                            break
                    if borrowed:
                        pronunciations[category] = borrowed
                        changed = True
                        break
        if not changed:
            break

    for entry in entries.values():
        if not entry["pronunciations"]:
            del entry["pronunciations"]


def build_cache() -> dict:
    entries: dict[str, dict] = {}
    raw_readings: dict[str, dict[str, str]] = {}

    def get_entry(codepoint: str) -> dict:
        char = codepoint_to_char(codepoint)
        return entries.setdefault(
            char,
            {"char": char, "codepoint": codepoint, "readings": {}, "variants": {}},
        )

    for codepoint, field, value in parse_unihan_file(READINGS_FILE):
        char = get_entry(codepoint)["char"]
        raw_readings.setdefault(char, {})[field] = value
        if field not in PRONUNCIATION_SOURCE_FIELDS:
            get_entry(codepoint)["readings"][field] = clean_reading_value(field, value)

    for codepoint, field, value in parse_unihan_file(VARIANTS_FILE):
        variants = []
        for token in value.split():
            m = VARIANT_TOKEN_RE.match(token)
            if not m:
                continue
            var_codepoint, source = m.group(1), m.group(2).lstrip("<")
            variants.append(
                {
                    "char": codepoint_to_char(var_codepoint),
                    "codepoint": var_codepoint,
                    "source": source or None,
                },
            )
        get_entry(codepoint)["variants"][field] = variants

    apply_shinjitai_kyujitai_variants(entries)
    apply_equivalent_unified_ideograph_variants(entries)

    kanjidictvn, senses_by_char = load_kanjidictvn()
    hangul_table = load_hangul_table()
    vietnamese_source: dict[str, str] = {}
    for char, entry in entries.items():
        pronunciations = build_pronunciations(
            raw_readings.get(char, {}),
            char,
            entry["variants"],
            kanjidictvn,
            hangul_table,
            vietnamese_source,
        )
        if pronunciations:
            entry["pronunciations"] = pronunciations

    # Decide whether a CCCII grouping is trustworthy
    rank_vietnamese(entries, senses_by_char, vietnamese_source)
    apply_cccii_variants(entries)
    # Type CCCII to kJapaneseNewVariant if the target is Japan-only and the source is not
    retype_japanese_variants(entries)
    # After the variant work, which it leans on to line the school tiers up
    apply_level_designations(entries)

    apply_variant_fallback(entries)

    return entries


if __name__ == "__main__":
    cache = build_cache()
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(  # noqa: T201
        f"Wrote {CACHE_FILE} ({CACHE_FILE.stat().st_size / 1_048_576:.1f} MB, {len(cache)} characters)",
    )

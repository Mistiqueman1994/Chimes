"""
prompt_parser.py
------------------
Turns the free-text "describe the track" box into generator settings, and
screens it for attempts to reference real copyrighted artists, bands, or
songs - this app only ever describes and generates *original* sound
(genre/instruments/mood/tempo), never a specific existing recording.

The artist/band blocklist below is a best-effort list of well-known names
across genres. It is intentionally not exhaustive (that's not possible) -
it exists to catch the common, obvious case of someone typing a real
artist or song name into the prompt box, not to be a legal filter.
"""

import re

from music_engine import INSTRUMENTS

# --- genre keyword -> preset name -------------------------------------------------

_GENRE_KEYWORDS = {
    "Heavy Metal": ["metal", "thrash", "death metal", "black metal", "heavy"],
    "Punk Rock": ["punk", "hardcore"],
    "Blues Rock": ["blues"],
    "Classic Rock": ["classic rock", "70s rock", "80s rock", "arena rock"],
    "Pop Rock": ["pop rock", "pop", "radio friendly"],
    "Funk": ["funk", "groove"],
    "Synthwave": ["synthwave", "synth wave", "retrowave", "outrun", "80s synth"],
    "Ambient": ["ambient", "chill", "relax", "meditative", "atmospheric", "lo-fi", "lofi"],
}

# --- tempo hints -------------------------------------------------------------------

_BPM_RE = re.compile(r"(\d{2,3})\s*bpm", re.IGNORECASE)
_FAST_WORDS = ["fast", "upbeat", "energetic", "aggressive", "high energy", "frantic"]
_SLOW_WORDS = ["slow", "mellow", "relaxed", "laid back", "sleepy", "downtempo"]
_MID_WORDS = ["mid tempo", "moderate", "medium tempo"]

# --- instrument keywords -----------------------------------------------------------

_INSTRUMENT_KEYWORDS = {
    "Drums": ["drum", "drums", "beat", "percussion"],
    "Bass": ["bass"],
    "Rhythm Guitar": ["rhythm guitar", "power chord", "power chords", "chugging"],
    "Lead Guitar": ["lead guitar", "guitar solo", "solo", "riff", "shredding"],
}
_GENERIC_GUITAR_WORDS = ["guitar", "guitars"]

# --- vocals ---------------------------------------------------------------------

_VOCAL_WORDS = ["vocal", "vocals", "singing", "singer", "sung", "lyrics", "lyric",
                "rap", "rapping", "rapper", "choir", "acapella", "a cappella"]

# --- real-artist / copyrighted-reference screening ---------------------------------

_KNOWN_ARTISTS = [
    # metal / rock
    "metallica", "iron maiden", "black sabbath", "megadeth", "slayer", "pantera",
    "slipknot", "system of a down", "avenged sevenfold", "guns n roses",
    "guns n' roses", "led zeppelin", "pink floyd", "the rolling stones",
    "aerosmith", "acdc", "ac/dc", "nirvana", "pearl jam", "soundgarden",
    "foo fighters", "red hot chili peppers", "radiohead", "queen", "the beatles",
    "the who", "deep purple", "judas priest", "motorhead", "motörhead",
    "rage against the machine", "linkin park", "korn", "tool", "disturbed",
    # pop / hip-hop / r&b
    "taylor swift", "beyonce", "beyoncé", "rihanna", "drake", "kanye west",
    "ye", "eminem", "jay-z", "jay z", "kendrick lamar", "the weeknd",
    "ariana grande", "billie eilish", "ed sheeran", "adele", "bruno mars",
    "justin bieber", "michael jackson", "madonna", "prince", "whitney houston",
    "lady gaga", "katy perry", "coldplay", "maroon 5", "imagine dragons",
    "dua lipa", "olivia rodrigo", "post malone", "travis scott",
    # electronic / other
    "daft punk", "the chainsmokers", "calvin harris", "david guetta",
    "skrillex", "deadmau5", "avicii", "marshmello",
    "bob dylan", "elton john", "fleetwood mac", "the eagles", "u2",
]

_REFERENCE_PATTERNS = [
    r"\bsounds? like\b", r"\bin the style of\b", r"\bstyle of\b",
    r"\bsimilar to\b", r"\bcover of\b", r"\bremix of\b", r"\bsampling\b",
    r"\bsample of\b", r"\boriginally by\b", r"\bby the band\b",
    r"\bft\.?\s", r"\bfeaturing\b", r"\bas played by\b", r"\bjust like\b",
]


def _contains_word(text_lower, phrase):
    return re.search(r"\b" + re.escape(phrase) + r"\b", text_lower) is not None


def _check_copyright_block(text):
    text_lower = text.lower()

    for artist in _KNOWN_ARTISTS:
        if _contains_word(text_lower, artist):
            return (
                "Your description appears to reference a real artist, band, or "
                "song. This app only makes original instrumental music - "
                "describe the sound you want instead (genre, instruments, mood, "
                "tempo), not a real artist or song title."
            )

    for pattern in _REFERENCE_PATTERNS:
        if re.search(pattern, text_lower):
            return (
                "Your description sounds like it's asking for something modeled "
                "on a specific existing song or artist. This app only makes "
                "original instrumental music - describe the sound you want "
                "instead (genre, instruments, mood, tempo), not a reference to "
                "an existing recording."
            )

    return None


# --- public API ----------------------------------------------------------------

def parse_prompt(text):
    result = {
        "blocked": False,
        "block_reason": "",
        "mentions_vocals": False,
        "genre": None,
        "tempo_hint": None,
        "instruments_mentioned": [],
        "instruments_excluded": [],
    }

    if not text or not text.strip():
        return result

    block_reason = _check_copyright_block(text)
    if block_reason:
        result["blocked"] = True
        result["block_reason"] = block_reason
        return result

    text_lower = text.lower()

    result["mentions_vocals"] = any(_contains_word(text_lower, w) for w in _VOCAL_WORDS)

    for genre, keywords in _GENRE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            result["genre"] = genre
            break

    bpm_match = _BPM_RE.search(text_lower)
    if bpm_match:
        result["tempo_hint"] = max(50, min(200, int(bpm_match.group(1))))
    elif any(w in text_lower for w in _FAST_WORDS):
        result["tempo_hint"] = 170
    elif any(w in text_lower for w in _SLOW_WORDS):
        result["tempo_hint"] = 75
    elif any(w in text_lower for w in _MID_WORDS):
        result["tempo_hint"] = 110

    excluded = set()
    for instrument in INSTRUMENTS:
        for phrase in ("no " + instrument.lower(), "without " + instrument.lower()):
            if phrase in text_lower:
                excluded.add(instrument)
    for word in ["drum", "drums", "bass", "guitar", "guitars"]:
        if f"no {word}" in text_lower or f"without {word}" in text_lower:
            if word.startswith("drum"):
                excluded.add("Drums")
            elif word == "bass":
                excluded.add("Bass")
            elif word.startswith("guitar"):
                excluded.add("Rhythm Guitar")
                excluded.add("Lead Guitar")

    mentioned = set()
    for instrument, keywords in _INSTRUMENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            mentioned.add(instrument)
    if any(w in text_lower for w in _GENERIC_GUITAR_WORDS):
        mentioned.add("Rhythm Guitar")
        mentioned.add("Lead Guitar")

    mentioned -= excluded

    result["instruments_mentioned"] = sorted(mentioned)
    result["instruments_excluded"] = sorted(excluded)

    return result

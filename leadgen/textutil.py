"""Name, phone and place normalisation shared across stages."""
from __future__ import annotations

import difflib
import re
import unicodedata

from .config import CH_NAME_NOISE, POSTCODE_AREA_TO_CITY

_PUNCT = re.compile(r"[^a-z0-9]+")

# Trading suffixes and generic trade words that should not drive a name match.
_TRADE_WORDS = {
    "engineering", "engineers", "engineer", "services", "service", "solutions",
    "systems", "contractors", "contracting", "installations", "installation",
    "maintenance", "heating", "plumbing", "gas", "oil", "fuels", "fuel",
    "energy", "renewables", "renewable", "electrical", "mechanical",
    "industrial", "commercial", "domestic", "supplies", "supply", "products",
    "technologies", "technology", "international", "associates", "partners",
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("&", " and ")
    return _PUNCT.sub("-", text).strip("-")


def compact(text: str) -> str:
    """Lowercase alphanumerics only — 'The Gas Pro' -> 'thegaspro'."""
    return _PUNCT.sub("", (text or "").lower().replace("&", "and"))


def name_tokens(name: str, drop_trade_words: bool = False) -> list[str]:
    tokens = [t for t in slugify(name).split("-") if t and t not in CH_NAME_NOISE]
    if drop_trade_words:
        distinctive = [t for t in tokens if t not in _TRADE_WORDS]
        # Never strip everything: "Precision Engineering Ltd" must keep something.
        if distinctive:
            return distinctive
    return tokens


def normalise_company_name(name: str) -> str:
    """Strip legal suffixes and noise for similarity comparison."""
    return " ".join(name_tokens(name))


def name_similarity(a: str, b: str) -> float:
    """0..1 similarity between two company names, suffix-insensitive.

    Takes the best of whole-string ratio and token-set containment so that
    'MCR Gas' vs 'MCR GAS SERVICES LIMITED' scores high.
    """
    na, nb = normalise_company_name(a), normalise_company_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()

    ta, tb = set(na.split()), set(nb.split())
    if ta and tb:
        overlap = len(ta & tb) / min(len(ta), len(tb))
        # Containment is strong evidence, but only when the shared tokens are
        # not purely generic trade words.
        shared_distinctive = (ta & tb) - _TRADE_WORDS
        if overlap == 1.0 and shared_distinctive:
            ratio = max(ratio, 0.92)
        else:
            ratio = max(ratio, overlap * 0.85)

        # Two firms in the same trade share long substrings purely because of
        # words like 'gas engineers', which pushes the raw sequence ratio well
        # above threshold. If each name carries a distinctive part and those
        # parts have nothing in common, they are different companies however
        # similar the strings look.
        da, db = ta - _TRADE_WORDS, tb - _TRADE_WORDS
        if da and db and not (da & db):
            ratio = min(ratio, 0.50)

    return round(ratio, 4)


# ---------------------------------------------------------------- phones -----

def phone_digits(phone: str) -> str:
    """UK phone reduced to comparable national digits.

    '0117 964 0078', '+44 117 964 0078' and '(0117) 9640078' all reduce to
    '1179640078'.
    """
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("0044"):
        digits = digits[4:]
    elif digits.startswith("44") and len(digits) >= 11:
        digits = digits[2:]
    return digits.lstrip("0")


_PHONE_IN_TEXT = re.compile(r"(?:\+?44[\s\-().]*|0)(?:\d[\s\-().]*){8,12}")


def phones_in_text(text: str) -> set[str]:
    """Every plausible UK phone number found in a blob of HTML/text."""
    found: set[str] = set()
    for match in _PHONE_IN_TEXT.finditer(text or ""):
        norm = phone_digits(match.group(0))
        if 9 <= len(norm) <= 11:
            found.add(norm)
    return found


def phone_matches(target: str, text: str) -> bool:
    want = phone_digits(target)
    if len(want) < 9:
        return False
    # Direct substring on a digits-only projection catches numbers split across
    # markup that the regex above may miss.
    digits_only = re.sub(r"\D", "", text or "")
    if want in digits_only:
        return True
    return want in phones_in_text(text)


# ---------------------------------------------------------------- places -----

def location_parts(location: str) -> list[str]:
    """['Bishopsworth', 'Bristol'] from 'Bishopsworth, Bristol', lowercased."""
    return [p.strip().lower() for p in (location or "").split(",") if p.strip()]


def location_city(location: str) -> str:
    """The broadest place name in a Location value — usually the last segment."""
    parts = location_parts(location)
    return parts[-1] if parts else ""


_OUTCODE = re.compile(r"\b([A-Z]{1,2})\d[A-Z\d]?\s*\d[A-Z]{2}\b")


def postcode_area(text: str) -> str | None:
    """Leading letters of a UK outcode found in text, e.g. 'BS' from 'BS13 8AB'."""
    match = _OUTCODE.search((text or "").upper())
    return match.group(1) if match else None


def postcode_city(text: str) -> str | None:
    area = postcode_area(text)
    return POSTCODE_AREA_TO_CITY.get(area) if area else None


def town_matches(location: str, candidate_text: str) -> tuple[bool, str]:
    """Does an address blob sit in the same place as our Location column?

    Returns (matched, basis) where basis is 'town' for a direct place-name hit
    or 'postcode-area' when only the postcode maps to the same city. Both are
    accepted per the configured matching policy; the basis is recorded so a
    weaker match stays visible in the output.
    """
    if not location or not candidate_text:
        return False, ""
    blob = (candidate_text or "").lower()

    for part in location_parts(location):
        # Word-boundary match: 'bury' must not match 'canterbury'.
        if re.search(rf"\b{re.escape(part)}\b", blob):
            return True, "town"

    city = location_city(location)
    pc_city = postcode_city(candidate_text)
    if city and pc_city and (pc_city == city or pc_city in city or city in pc_city):
        return True, "postcode-area"

    return False, ""

#!/usr/bin/env python3
"""Shared plumbing for source adapters.

See docs/ADAPTER_SPEC.md for the contract. This module deliberately holds no
source-specific logic: it does HTTP politely, writes bronze-zone dumps in the
mandated layout, and refuses to write a dump missing its license block.

ASCII only, per ASCII_CODING_STANDARDS.md. Character tables in this file use
escape sequences, never literals, so the file passes its own gate.
"""

import hashlib
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone

ADAPTER_FRAMEWORK_VERSION = "0.1.0"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ROOT = os.path.join(REPO_ROOT, "data", "raw")

CONTACT = "pipfoweraker@gmail.com"
USER_AGENT = (
    "pdoom-data/0.1 (+https://github.com/PipFoweraker/pdoom-data; %s)" % CONTACT
)

VALID_KINDS = {
    "model_release",
    "publication",
    "incident",
    "policy",
    "org_event",
    "funding",
    "forum_post",
    "benchmark",
}

CONFIDENCE_LEVELS = {"high", "medium", "low"}

# Every non-ASCII character this repo will accept, and what it becomes.
#
# WHY THIS IS A MAP AND NOT A FOLD. CLAUDE.md records the 2026-08-10 ASCII
# clearance as using "an explicit substitution map that errors on unmapped
# characters", and that is the rule this table implements. Until 2026-08-29 it
# was only half of it: the map existed, but to_ascii's fallback ran NFKD and
# kept whatever came out as ASCII -- which for a character that does not
# decompose is the EMPTY STRING. So mapped characters were transliterated and
# unmapped ones were silently deleted.
#
# The cost was not cosmetic. "PanGu-Sigma" became "PanGu-", "Sigma-WASP" became
# "-WASP", "DALL(interpunct)E 2" became "DALLE 2". A deleted character changes
# the title, which changes the slug, which changes the id -- and two of Pip's
# 2026-07-26 accepts were orphaned against ids that no longer existed, with
# nothing going red. "x" was in the map so ResNeXt-101 (64x4d) survived intact,
# which is precisely why the defect read as working.
GREEK_TRANSLITERATIONS = {
    "\u03b1": "alpha", "\u0391": "Alpha",
    "\u03b2": "beta", "\u0392": "Beta",
    "\u03b3": "gamma", "\u0393": "Gamma",
    "\u03b4": "delta", "\u0394": "Delta",
    "\u03b5": "epsilon", "\u0395": "Epsilon",
    "\u03b6": "zeta", "\u0396": "Zeta",
    "\u03b7": "eta", "\u0397": "Eta",
    "\u03b8": "theta", "\u0398": "Theta",
    "\u03b9": "iota", "\u0399": "Iota",
    "\u03ba": "kappa", "\u039a": "Kappa",
    "\u03bb": "lambda", "\u039b": "Lambda",
    "\u03bc": "mu", "\u039c": "Mu",
    "\u03bd": "nu", "\u039d": "Nu",
    "\u03be": "xi", "\u039e": "Xi",
    "\u03bf": "omicron", "\u039f": "Omicron",
    "\u03c0": "pi", "\u03a0": "Pi",
    "\u03c1": "rho", "\u03a1": "Rho",
    "\u03c3": "sigma", "\u03a3": "Sigma", "\u03c2": "sigma",
    "\u03c4": "tau", "\u03a4": "Tau",
    "\u03c5": "upsilon", "\u03a5": "Upsilon",
    "\u03c6": "phi", "\u03a6": "Phi",
    "\u03c7": "chi", "\u03a7": "Chi",
    "\u03c8": "psi", "\u03a8": "Psi",
    "\u03c9": "omega", "\u03a9": "Omega",
}

CHAR_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": "\"",
    "\u201d": "\"",
    "\u2013": "-",
    "\u2014": "--",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2192": "->",
    "\u2190": "<-",
    "\u00d7": "x",
    "\u2212": "-",
    "\u2010": "-",
    "\u2011": "-",
    # Model names carry these, and each one cost an id when it was dropped.
    "\u00b7": "-",       # interpunct, as in DALL-E
    "\u2022": "-",       # bullet
    "\u00b0": " degrees",
    "\u00b5": "micro",   # MICRO SIGN
    "\u2032": "'",       # prime
    "\u2033": "\"",      # double prime
    "\u00b1": "+/-",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u2248": "~",
    "\u221e": "infinity",
    "\u2044": "/",       # fraction slash
    "\u2122": "(TM)",
    "\u00ae": "(R)",
    "\u00a9": "(C)",
    "\u2020": "+",       # dagger
    "\u00ab": "<<",
    "\u00bb": ">>",
    "\u201a": ",",
    "\u201e": ",,",
    "\u2039": "<",
    "\u203a": ">",
}
CHAR_REPLACEMENTS.update(GREEK_TRANSLITERATIONS)

# Characters we have DECIDED carry no textual meaning, so dropping them is a
# ruling rather than an accident. Forum titles are full of emoji and the corpus
# would be unusable if every one of them stopped an adapter run; the point of
# listing them is that the deletion is declared here and can be argued with,
# instead of falling out of an NFKD fold nobody reads.
DROPPABLE_UNICODE_CATEGORIES = frozenset([
    "Cf",   # format characters: ZWJ, ZWNJ, variation selectors, BOM
    "Mn",   # non-spacing marks left over after NFKD has taken the base letter
    "So",   # other symbols: emoji, dingbats, arrows we have not mapped
    "Sk",   # modifier symbols: skin-tone modifiers, spacing accents
    "Cs",   # surrogates
    "Co",   # private use
])


class UnmappableCharacterError(ValueError):
    """A character reached to_ascii that is neither mapped nor declared droppable.

    Deliberately fatal. The alternative -- the behaviour this replaced -- is to
    emit nothing for it, which silently rewrites identifiers. Add the character
    to CHAR_REPLACEMENTS with a transliteration, or to the droppable categories
    if it genuinely carries no meaning. Both are one-line decisions; neither is
    a guess.
    """


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def dump_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_session():
    """A requests session with honest identification."""
    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def polite_get(session, url, max_attempts=5, timeout=60, **kwargs):
    """GET with exponential backoff on 429 and 5xx.

    Raises on final failure so a caller never mistakes a rate-limit wall for
    an empty result set.
    """
    delay = 2.0
    last = None
    for _attempt in range(max_attempts):
        response = session.get(url, timeout=timeout, **kwargs)
        last = response
        if response.status_code < 400:
            return response
        if response.status_code in (429, 500, 502, 503, 504):
            retry_after = response.headers.get("Retry-After")
            if retry_after and str(retry_after).isdigit():
                wait = float(retry_after)
            else:
                wait = delay
            time.sleep(min(wait, 60.0))
            delay = min(delay * 2, 60.0)
            continue
        response.raise_for_status()
    last.raise_for_status()
    return last


def polite_post(session, url, max_attempts=5, timeout=60, **kwargs):
    """POST with the same backoff policy. Used by the GraphQL sources."""
    delay = 2.0
    last = None
    for _attempt in range(max_attempts):
        response = session.post(url, timeout=timeout, **kwargs)
        last = response
        if response.status_code < 400:
            return response
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(delay, 60.0))
            delay = min(delay * 2, 60.0)
            continue
        response.raise_for_status()
    last.raise_for_status()
    return last


class MojibakeError(ValueError):
    """Raised when text we just decoded is UTF-8 that was read as latin-1."""


def looks_like_mojibake(text):
    """True if `text` looks like UTF-8 bytes that were decoded as latin-1.

    The test is a round trip, not a character blacklist: only genuine mojibake
    re-encodes cleanly to latin-1 AND decodes as valid UTF-8 to something
    DIFFERENT. A legitimately accented string ('cafe' with an acute) fails the
    latin-1 re-encode or decodes back to itself, so it is not flagged.
    """
    return _mojibake_repair(text) is not None


# Two codecs, because this repo has now met BOTH species. The 2026-08-06
# timeline-events corruption was UTF-8 read as CP1252. The 2026-07-25 Epoch
# corruption was UTF-8 read as ISO-8859-1, which is what `requests` falls back
# to for a text/* body carrying no charset. The two codecs disagree over
# 0x80-0x9F, so neither alone finds both.
_MOJIBAKE_CODECS = ("cp1252", "latin-1")


def _mojibake_repair(text):
    """The repaired string, or None if `text` is not mojibake."""
    if text is None:
        return None
    s = str(text)
    if not s or all(ord(ch) < 128 for ch in s):
        return None
    for codec in _MOJIBAKE_CODECS:
        try:
            recovered = s.encode(codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if recovered != s:
            return recovered
    return None


def repair_mojibake(text):
    """Undo one latin-1/UTF-8 double decode. Returns text unchanged if it is
    not mojibake, so this is safe to call on anything."""
    repaired = _mojibake_repair(text)
    return text if repaired is None else repaired


def decode_response(response):
    """Text from an HTTP response, decoded correctly and checked.

    WHY THIS EXISTS. `requests` guesses: for a `text/*` body with no `charset`
    parameter it falls back to ISO-8859-1 per RFC 2616. Epoch AI serves
    `Content-Type: text/csv` with no charset, so `response.text` decoded UTF-8
    bytes as latin-1 and every accent mojibaked -- silently, because a latin-1
    decode of UTF-8 never raises. `to_ascii` then folded the mojibake to a
    LETTER: 'Universite de Montreal' was stored as 'UniversitA de MontrAal' in
    the 2026-07-25 Epoch dump, and 'e' cannot be recovered from 'A'.

    This is the `open()`-without-encoding defect that CLAUDE.md already warns
    about, arriving through a different door.

    Raises MojibakeError rather than returning damaged text: a wrong decode is
    a wrong answer, and a wrong answer is worse than no answer.
    """
    ctype = response.headers.get("Content-Type", "")
    if "charset=" not in ctype.lower():
        response.encoding = "utf-8"
    text = response.text
    if looks_like_mojibake(text):
        raise MojibakeError(
            "Decoded text from %s still looks double-decoded (declared "
            "Content-Type: %r). Refusing to hand back damaged text."
            % (getattr(response, "url", "<unknown>"), ctype))
    return text


def to_ascii(text):
    """Lossy but predictable ASCII coercion for text destined for the repo.

    Repairs mojibake FIRST. Folding double-decoded text is how an accent
    becomes an unrelated letter: NFKD of 'A-tilde' keeps 'A', so 'e-acute'
    read as latin-1 folds to 'A' rather than 'e'. Repairing first means even
    legacy text folds to the right letter. This never raises -- the boundary
    (decode_response) is where a bad decode should fail.
    """
    if text is None:
        return None
    text = repair_mojibake(text)
    out = []
    for char in str(text):
        if ord(char) < 128:
            out.append(char)
        elif char in CHAR_REPLACEMENTS:
            out.append(CHAR_REPLACEMENTS[char])
        else:
            # NFKD first, because it correctly resolves the whole accented-Latin
            # range: 'e-acute' -> 'e' plus a combining mark we then drop. It is
            # only a fold, though -- for a character with no decomposition it
            # returns the character itself, and filtering that to ASCII yields
            # the EMPTY STRING. That silent deletion is the defect this guard
            # closes, so an empty fold is an error and not an answer.
            folded = "".join(
                c for c in unicodedata.normalize("NFKD", char)
                if ord(c) < 128
                or unicodedata.category(c) in DROPPABLE_UNICODE_CATEGORIES
            )
            folded = "".join(c for c in folded if ord(c) < 128)
            if folded:
                out.append(folded)
            elif unicodedata.category(char) in DROPPABLE_UNICODE_CATEGORIES:
                continue
            else:
                raise UnmappableCharacterError(
                    "no ASCII spelling for %r (U+%04X, %s, %s) in %r. Add it to "
                    "CHAR_REPLACEMENTS with a transliteration, or to "
                    "DROPPABLE_UNICODE_CATEGORIES if it carries no meaning. Do "
                    "not let it be deleted: dropping a character rewrites the "
                    "title, which rewrites the slug, which orphans every human "
                    "verdict recorded against the old id."
                    % (char, ord(char), unicodedata.category(char),
                       unicodedata.name(char, "unnamed"), str(text)[:80]))
    return "".join(out)


def clean_summary(text, limit=400):
    """Collapse whitespace, coerce to ASCII, truncate on a word boundary.

    The existing arXiv import shipped raw PDF text as descriptions, complete
    with hard line breaks and hyphenation artifacts. This is the minimum
    defence; it does not attempt to repair broken extraction.
    """
    if not text:
        return ""
    collapsed = " ".join(to_ascii(text).split())
    if len(collapsed) <= limit:
        return collapsed
    cut = collapsed[:limit]
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(" ,;:.-") + "..."


def signal(name, value, observed_at=None):
    """Build a time-varying observation. Never store a bare scalar.

    A 2018 paper's citation count is a different number in 2019 and in 2026;
    which one a player should see depends on the game clock. Storing the
    observation date makes that answerable rather than a fudge.
    """
    return {name: [{"observed_at": observed_at or utc_now_iso(), "value": value}]}


URL_TRAILING = ",;"
SCHEMELESS_HOST = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,24}/")


def split_url_cell(value):
    """Recover the URLs from one upstream cell that may hold several.

    Lives here, not in the adapter or the projection, because BOTH need it and
    a second copy becomes a variant the moment either side changes. The
    projection needs it because 65 served records were built from a dump that
    already had the defect, and raw dumps are immutable; the adapter needs it
    so the next dump does not repeat it.

    Epoch AI's `Link` column is free text. 65 of 3,434 served candidates
    carried two or three URLs joined into a SINGLE value -- by a comma, a
    semicolon, or a newline -- so `source_urls[0]` was a string no consumer
    could fetch. Found 2026-08-21 by config/schemas/candidate_v1.json, the
    first thing in this repo that ever asserted the element was a URL.

    This is a parse, not a judgement: the cell says two URLs and the record now
    says two URLs. Prose in the cell -- "(was withdrawn)", "training code:" --
    is dropped here and stays in the raw dump, which is immutable and is where
    an unparsed original belongs.

    Deliberately conservative in three ways, each of which has a test:

      - Only whitespace splits.
      - Only a trailing comma or semicolon is stripped. A trailing full stop is
        NOT, because a URL may legitimately end in one and sentence punctuation
        in this column is rarer than the URLs it would corrupt.
      - A schemeless value is rescued to https ONLY if it carries a path
        separator. `arxiv.org/abs/2501.14818` is a URL that Epoch wrote without
        a scheme and that epoch_models.py dropped for exactly that reason,
        costing epoch_ai:eagle_2 its only source. `vs.something` in prose is
        not, and without the path-separator condition it would become
        `https://vs.something`.
    """
    out = []
    for token in str(value).split():
        token = token.rstrip(URL_TRAILING)
        if not (token.startswith("http://") or token.startswith("https://")):
            if SCHEMELESS_HOST.match(token.lower()):
                token = "https://" + token
            else:
                continue
        if token not in out:
            out.append(token)
    return out


def provenance(field_map):
    """Map field -> (layer, method, confidence) into a _provenance envelope."""
    out = {}
    for field, spec in field_map.items():
        layer, method, confidence = spec
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError("bad confidence %r for field %r" % (confidence, field))
        out[field] = {"layer": layer, "method": method, "confidence": confidence}
    return out


def validate_candidate(record):
    """Fail loudly at ingest rather than quietly at serving time."""
    problems = []
    for required in ("id", "title", "kind", "license", "ingested_at"):
        if not record.get(required):
            problems.append("missing %s" % required)
    kind = record.get("kind")
    if kind and kind not in VALID_KINDS:
        problems.append("unknown kind %r" % kind)
    lic = record.get("license") or {}
    for required in ("spdx", "attribution", "source_terms_url", "verified_at"):
        if not lic.get(required):
            problems.append("license missing %s" % required)
    spdx = str(lic.get("spdx", "")).upper()
    if "-SA" in spdx:
        problems.append("ShareAlike license %r excluded by repo policy" % spdx)
    for clock in ("occurred_at", "published_at", "source_available_at"):
        if clock not in record:
            problems.append("clock %s absent (use null if unknown)" % clock)
    return problems


def write_dump(source_id, candidates, raw_records, metadata):
    """Write a bronze-zone dump. Returns the dump directory path.

    Refuses to write if any candidate fails validation, because a dump that
    reaches disk is treated as immutable and gets committed.
    """
    failures = []
    seen_ids = {}
    for index, record in enumerate(candidates):
        problems = validate_candidate(record)
        record_id = record.get("id")
        # Duplicate ids are silent corruption: a consumer keying by id loses
        # one of the pair, and an attributed review lands on the wrong record.
        # Caught here rather than downstream, where it looks like a mystery.
        if record_id in seen_ids:
            problems.append("duplicate id, first seen at index %d"
                            % seen_ids[record_id])
        else:
            seen_ids[record_id] = index
        if problems:
            failures.append((index, record_id or "?", problems))
    if failures:
        raise ValueError(
            "%d of %d candidates failed validation; first few: %r"
            % (len(failures), len(candidates), failures[:5])
        )

    dump_dir = os.path.join(RAW_ROOT, source_id, "dumps", dump_stamp())
    os.makedirs(dump_dir, exist_ok=True)

    def write_jsonl(name, rows):
        path = os.path.join(dump_dir, name)
        with open(path, "w", encoding="ascii", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    write_jsonl("data.jsonl", candidates)
    write_jsonl("raw.jsonl", raw_records)

    meta = dict(metadata)
    meta.setdefault("source_id", source_id)
    meta.setdefault("extraction_date", utc_now_iso())
    meta["adapter_framework_version"] = ADAPTER_FRAMEWORK_VERSION
    meta["record_count"] = len(candidates)
    meta["raw_record_count"] = len(raw_records)
    meta_path = os.path.join(dump_dir, "_metadata.json")
    with open(meta_path, "w", encoding="ascii", newline="\n") as handle:
        json.dump(meta, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")

    manifest_path = os.path.join(dump_dir, "MANIFEST.sha256")
    with open(manifest_path, "w", encoding="ascii", newline="\n") as handle:
        for name in ("_metadata.json", "data.jsonl", "raw.jsonl"):
            digest = sha256_file(os.path.join(dump_dir, name))
            handle.write("%s  %s\n" % (digest, name))

    return dump_dir

"""Assert that the source-URL normaliser splits what it should and nothing else.

    python tests/test_url_normalisation.py

Why this exists
---------------
`project_candidates.normalise_urls()` rewrites values in the served feed. Any
code that rewrites data can improve it or quietly destroy it, and the two look
identical in a green build. The specific way this one could destroy data is by
dropping a list element it fails to recognise -- which would make the feed
schema-clean and source-poorer at the same time, the precise trade this repo
should never make to turn a check green.

So the corpus-wide case at the bottom is the one that matters most: run the
normaliser over every served record and require that NO record ends up with
fewer URLs than it started with. The hand-written cases exist to pin the
behaviour; that one exists to catch the failure mode.

Provenance of the defect: 65 records carried two or three URLs joined into one
list element, found 2026-08-21 by candidate_v1.json. Epoch AI's `Link` column
is free text and its separators are inconsistent -- comma, semicolon, newline,
double newline, and in one case the word "or".
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "build"))

sys.path.insert(0, os.path.join(REPO, "scripts", "adapters"))

import project_candidates as pc  # noqa: E402
import _base  # noqa: E402

FEED = os.path.join(REPO, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")

A = "https://a.example/x"
B = "https://b.example/y"

# (name, input cell, expected list). Named for the real record they come from.
CASES = [
    ("a comma-joined pair, as epoch_ai:grok_1 carries",
     A + ", " + B, [A, B]),
    ("a semicolon-joined pair, as epoch_ai:falcon_180b carries",
     A + "; " + B, [A, B]),
    ("a newline-joined pair, as epoch_ai:llama_2_70b carries",
     A + "\n" + B, [A, B]),
    ("a double-newline-joined pair, as epoch_ai:dall_e carries",
     A + "\n\n" + B, [A, B]),
    ("a triple, as epoch_ai:cogvlm_17b carries",
     A + "\n" + B + "\nhttps://c.example/z", [A, B, "https://c.example/z"]),
    ("the word 'or' between two URLs, as epoch_ai:protbert_bfd carries",
     A + " or \n" + B, [A, B]),
    ("a parenthetical note, as epoch_ai:codefusion_python carries",
     A + " (was withdrawn)\n\n" + B, [A, B]),
    ("a labelled second URL, as epoch_ai:blenderbot_3 carries",
     A + "\n\ntraining code: " + B, [A, B]),
    ("a trailing comma left by the split, as epoch_ai:pangu_weather carries",
     A + ", " + B + ",", [A, B]),
    ("a trailing space, as epoch_ai:gpt_4o carries",
     A + " \n" + B, [A, B]),

    ("one clean URL is returned unchanged", A, [A]),
    ("the same URL twice collapses to one", A + " " + A, [A]),

    ("a schemeless URL with a path is rescued to https, which is the value "
     "epoch_models.py dropped and the reason epoch_ai:eagle_2 has no source",
     "arxiv.org/abs/2501.14818", ["https://arxiv.org/abs/2501.14818"]),
    ("a schemeless token with NO path separator is not rescued: 'vs.something' "
     "in prose would otherwise become a URL",
     "vs.something", []),
    ("a bare hostname is not rescued either, for the same reason",
     "www.example.com", []),
    ("prose alone yields nothing, as EXAONE 4.5's author-list Link cell would",
     "Eunbi Choi, Kibong Choi, Sehyun Chun", []),
    ("an ftp URL is not a web source and is not accepted",
     "ftp://a.example/x", []),
    ("a URL ending in a full stop keeps it: a trailing dot can be part of a "
     "path, and stripping it would corrupt more URLs than the sentence "
     "punctuation it would tidy",
     "https://a.example/x.", ["https://a.example/x."]),
    ("a percent-encoded comma inside a path is not a separator",
     "https://a.example/p%2Cq", ["https://a.example/p%2Cq"]),
]


def check_cases():
    failures = []
    for name, cell, expected in CASES:
        got = _base.split_url_cell(cell)
        if got != expected:
            failures.append("  %s\n      cell     %r\n      expected %r\n"
                            "      got      %r" % (name, cell, expected, got))
    return failures


def check_idempotent():
    """normalise(normalise(x)) == normalise(x).

    A rewrite that is not idempotent makes the byte-identical rebuild check
    permanently red, which ends with someone deleting the check.
    """
    failures = []
    for name, cell, _ in CASES:
        rec = {"source_urls": [cell], "archive_urls": []}
        pc.normalise_urls(rec)
        once = list(rec["source_urls"])
        pc.normalise_urls(rec)
        if rec["source_urls"] != once:
            failures.append("  not idempotent: %s -- %r then %r"
                            % (name, once, rec["source_urls"]))
    return failures


def check_corpus_loses_nothing():
    """Over every served record: no record may end with fewer URLs."""
    failures = []
    if not os.path.isfile(FEED):
        return ["  served feed is missing, so the corpus case could not run -- "
                "which is a failure, not a skip"]
    rows = [json.loads(l) for l in io.open(FEED, encoding="utf-8") if l.strip()]
    shrank = 0
    emptied = 0
    for r in rows:
        for field in ("source_urls", "archive_urls"):
            before = list(r.get(field) or [])
            rec = json.loads(json.dumps(r))
            pc.normalise_urls(rec)
            after = rec[field]
            if len(after) < len(before):
                shrank += 1
                if len(before) and not after:
                    emptied += 1
                if shrank <= 5:
                    failures.append("  %s loses %s: %r -> %r"
                                    % (r["id"], field, before, after))
    if shrank:
        failures.append("  %d record/field pairs lose a URL, %d lose all of them"
                        % (shrank, emptied))
    return failures


def main():
    failures = check_cases() + check_idempotent() + check_corpus_loses_nothing()
    if failures:
        print("URL NORMALISATION FAILED")
        for f in failures:
            print(f)
        return 1
    print("url normalisation: %d cases, idempotent, and no served record loses "
          "a URL" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())

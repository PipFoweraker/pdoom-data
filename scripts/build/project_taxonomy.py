"""Project the taxonomy into the serveable zone, and assert it is coherent.

    python scripts/build/project_taxonomy.py            # write
    python scripts/build/project_taxonomy.py --check    # assert committed == fresh

Why this exists
---------------
On 2026-08-06 Pip ruled that pdoom-data is the authority on taxonomy for
real-time events and owns the structure of the editorial layer. That is a
larger grant than the workshop's option B, which only said that opinion crosses
the boundary attributed.

This seat accepted it and said in the same breath that authority obliges
publication: an authority whose vocabulary is implicit is just a seat with
opinions. So the vocabulary is an input with a gated output, on the same footing
as candidates, reviewed and frontier_labs -- not a document.

pdoom1 supplied the argument that made this the right shape, from a worked
example in its own tree. Two indexes of the same class of content sat in one
directory: one hand-maintained, which rotted so far that its CLAUDE.md now
instructs agents to trust the files instead, and one generated with a --check in
pre-commit, which cannot. The variable is not where a definition lives. It is
whether it is derived and gated.

What this asserts, and why each one is here
-------------------------------------------
  every term has a definition        a term list without definitions is a word
                                     list, and a reader would have to ask
                                     someone -- which is the state this replaces.

  every 'ruled' term cites authority  'ruled' with no citation is indistinguish-
                                     able from 'this seat decided'. The whole
                                     grant rests on the difference.

  no term is minted in two places    the failure coordination#15 records. If a
                                     term appears in both lists, two repos think
                                     they own it and neither knows.

  ASCII                              enforced repo-wide. Caught a stray CJK
                                     character in the seed file within a minute
                                     of it being written.

The known limit
---------------
This asserts that the taxonomy is internally coherent and that its published
form matches its source. It cannot assert that a definition is CORRECT, or that
a consumer is using a term the way this file defines it. pdoom1's mapping table
is where that would be caught, and pdoom1 has made a --check gate on that table
a condition of its own vote. Both halves are needed; this is one of them.
"""
import argparse
import io
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(REPO_ROOT, "config", "taxonomy", "taxonomy_v0.json")
OUT_DIR = os.path.join(REPO_ROOT, "data", "serveable", "api", "taxonomy")

VALID_STATUS = ("ruled", "proposed", "contested")


def load_source():
    with io.open(SOURCE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(source):
    problems = []
    here = source.get("minted_here", [])
    elsewhere = source.get("minted_elsewhere", [])

    for entry in here:
        term = entry.get("term", "<unnamed>")
        if not entry.get("definition", "").strip():
            problems.append("minted_here '%s' has no definition" % term)
        status = entry.get("status")
        if status not in VALID_STATUS:
            problems.append("minted_here '%s' has status %r, expected one of %s"
                            % (term, status, ", ".join(VALID_STATUS)))
        if status == "ruled" and not entry.get("authority", "").strip():
            problems.append("minted_here '%s' is 'ruled' but cites no authority; "
                            "'ruled' without a citation is just this seat deciding"
                            % term)

    for entry in elsewhere:
        term = entry.get("term", "<unnamed>")
        if not entry.get("minted_by", "").strip():
            problems.append("minted_elsewhere '%s' does not say which repo mints it"
                            % term)
        if not entry.get("note", "").strip():
            problems.append("minted_elsewhere '%s' has no note explaining why it is "
                            "listed here at all" % term)
        if entry.get("status") not in VALID_STATUS:
            problems.append("minted_elsewhere '%s' has status %r"
                            % (term, entry.get("status")))

    here_terms = [e.get("term") for e in here]
    elsewhere_terms = [e.get("term") for e in elsewhere]
    for term in sorted(set(here_terms) & set(elsewhere_terms)):
        problems.append("'%s' is claimed in BOTH minted_here and minted_elsewhere; "
                        "two repos believing they own one term is the failure "
                        "coordination#15 records" % term)
    for group, names in (("minted_here", here_terms),
                         ("minted_elsewhere", elsewhere_terms)):
        seen = set()
        for name in names:
            if name in seen:
                problems.append("'%s' appears twice in %s" % (name, group))
            seen.add(name)

    return problems


def ascii_check(payload):
    blob = json.dumps(payload, ensure_ascii=False)
    return [repr(ch) for ch in sorted(set(blob)) if ord(ch) > 126]


def render(source):
    """Deterministic. No wall-clock stamp anywhere, so --check can compare directly."""
    here = sorted(source.get("minted_here", []), key=lambda e: e["term"])
    elsewhere = sorted(source.get("minted_elsewhere", []), key=lambda e: e["term"])

    payload = {
        "taxonomy_version": source["taxonomy_version"],
        "status": source["status"],
        "boundaries": source["boundaries"],
        "how_to_read_status": source["how_to_read_status"],
        "minted_here": here,
        "minted_elsewhere": elsewhere,
    }

    by_status = {}
    for entry in here:
        by_status[entry["status"]] = by_status.get(entry["status"], 0) + 1

    lineage = {
        "build_version": "0.1.0",
        "source": "config/taxonomy/taxonomy_v0.json",
        "taxonomy_version": source["taxonomy_version"],
        "counts": {
            "minted_here": len(here),
            "minted_elsewhere": len(elsewhere),
            "minted_here_by_status": dict(sorted(by_status.items())),
        },
        "policy": {
            "authority": "pdoom-data is the authority on taxonomy for real-time "
                         "events and owns the structure of the editorial layer, "
                         "ruled by Pip 2026-08-06 (coordination#31 Phase 2).",
            "boundary": "Taxonomy authority is not shaping authority. This repo "
                        "defines what a term means; it does not define what a "
                        "consumer does with it.",
            "status_meaning": "'proposed' terms have not been ruled by anyone. Do "
                              "not build a contract on a proposed term without "
                              "saying so.",
            "ownership": "minted_elsewhere entries are pointers, not definitions. "
                         "The owning repo's definition governs; this file records "
                         "only that the term is not ours to change.",
        },
    }
    return payload, lineage


def write_json(path, obj):
    """Write via temp + os.replace.

    Never open an existing file with encoding='ascii' for writing: Python
    truncates on open and then raises on the first non-ASCII byte, destroying the
    file before the error surfaces. That ate two files in one session.
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=True, sort_keys=False)
        handle.write("\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="assert the committed output matches a fresh build; "
                             "write nothing")
    args = parser.parse_args()

    source = load_source()

    problems = validate(source)
    for problem in problems:
        print("SCHEMA: " + problem)
    if problems:
        return 1

    payload, lineage = render(source)

    bad = ascii_check(payload)
    for ch in bad:
        print("ASCII: " + ch)
    if bad:
        return 1

    print("taxonomy version     : %s" % payload["taxonomy_version"])
    print("minted here          : %d" % lineage["counts"]["minted_here"])
    for status, count in lineage["counts"]["minted_here_by_status"].items():
        print("  %-18s %d" % (status, count))
    print("minted elsewhere     : %d" % lineage["counts"]["minted_elsewhere"])

    feed_path = os.path.join(OUT_DIR, "taxonomy.json")
    lineage_path = os.path.join(OUT_DIR, "LINEAGE.json")

    if args.check:
        if not os.path.isfile(feed_path):
            print("CHECK FAILED: %s does not exist" % feed_path)
            return 1
        with io.open(feed_path, encoding="utf-8") as handle:
            if json.load(handle) != payload:
                print("CHECK FAILED: committed taxonomy differs from a fresh "
                      "build. data/serveable/ is a build output; re-run without "
                      "--check.")
                return 1
        if os.path.isfile(lineage_path):
            with io.open(lineage_path, encoding="utf-8") as handle:
                if json.load(handle) != lineage:
                    print("CHECK FAILED: committed LINEAGE differs from a fresh "
                          "build.")
                    return 1
        print("CHECK OK: committed output matches a fresh build")
        return 0

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    write_json(feed_path, payload)
    write_json(lineage_path, lineage)
    print("wrote %s" % os.path.relpath(feed_path, REPO_ROOT).replace("\\", "/"))
    print("wrote %s" % os.path.relpath(lineage_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

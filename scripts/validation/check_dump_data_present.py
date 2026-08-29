"""A tracked dump must either carry its data or say how to get it back.

    python scripts/validation/check_dump_data_present.py

WHY. On 2026-08-30 the corpus-review sitting could not start. Its dump
directory, data/raw/arxiv_abstracts/dumps/2026-08-24_010736/, held a COMMITTED
_metadata.json saying "record_count": 150 -- and no data.jsonl beside it. The
metadata asserted 150 records; zero existed. Nothing noticed, because nothing
compares a dump's claim against a dump's contents.

The gitignore that excludes these data files is correct and deliberate: real
arXiv abstracts carry mathematics and author names the ASCII gate would reject,
and the fetch is reproducible. But an intentional exclusion and an accidental
absence look IDENTICAL on a fresh clone -- a metadata file claiming N records
with nothing next to it, either way.

So the rule is: a tracked dump either ships its data, or its metadata says in
one field exactly how to reproduce it. Then the two cases are distinguishable
by reading, which is the whole of it. This is a claim about a file checked
against the filesystem, not a claim checked against itself.
"""

import io
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = os.path.join("data", "raw")
DECLARATION = "regenerate_with"


def tracked_files():
    out = subprocess.run(["git", "ls-files", RAW], cwd=REPO_ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("git ls-files failed: %s" % out.stderr.strip())
    return set(out.stdout.split("\n"))


def main():
    tracked = tracked_files()
    metadata_files = sorted(p for p in tracked
                            if os.path.basename(p) == "_metadata.json")

    problems = []
    declared = 0
    shipped = 0
    for rel in metadata_files:
        dump_dir = os.path.dirname(rel)
        data_rel = "/".join([dump_dir, "data.jsonl"])
        data_abs = os.path.join(REPO_ROOT, data_rel)

        if data_rel in tracked:
            shipped += 1
            continue

        # A _templates directory is the shape of a dump, not a dump. It claims
        # zero records and holds zero, which is consistent rather than missing.
        if os.path.basename(dump_dir) == "_templates":
            continue

        with io.open(os.path.join(REPO_ROOT, rel), encoding="utf-8") as handle:
            meta = json.load(handle)
        how = meta.get(DECLARATION)
        claimed = meta.get("record_count")

        if not how:
            problems.append(
                "%s is tracked and claims record_count=%s, but data.jsonl is "
                "NOT tracked and the metadata does not say how to reproduce "
                "it. Add a %r field naming the exact command, so a deliberate "
                "gitignore is distinguishable from a fetch that never "
                "happened." % (rel, claimed, DECLARATION))
            continue

        declared += 1
        # A declaration is a claim too. If the file IS present locally, its
        # length must match what the metadata says, or the metadata is lying
        # about a file anyone can count.
        if os.path.isfile(data_abs) and isinstance(claimed, int):
            with io.open(data_abs, encoding="utf-8") as handle:
                actual = sum(1 for line in handle if line.strip())
            if actual != claimed:
                problems.append(
                    "%s claims record_count=%d but data.jsonl beside it holds "
                    "%d" % (rel, claimed, actual))

    if problems:
        print("CHECK FAILED: a tracked dump neither ships its data nor says "
              "how to get it back.")
        for problem in problems:
            print("  - %s" % problem)
        return 1

    print("dump data: %d dump(s) ship their data, %d declare how to reproduce "
          "it, none claim records they cannot account for"
          % (shipped, declared))
    return 0


if __name__ == "__main__":
    sys.exit(main())

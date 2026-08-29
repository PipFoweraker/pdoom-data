#!/usr/bin/env python3
"""Every text file this repository writes must name its codec and its newline.

    python scripts/validation/check_source_portability.py

Why this is a gate and not a note. `open(path, "w")` inherits two things from
the machine it runs on: the locale codec, which is UTF-8 here and cp1252 on the
Windows seat, and the line ending, which is "\\n" here and "\\r\\n" there. The
CRLF half is loud -- `project_candidates.py --check` compares bytes and the
MANIFEST.sha256 comparison in `check_invariants.py` compares hashes, so a
Windows writer fails the rebuild checks against a tree that looks identical in
every editor. The cp1252 half is the dangerous one: a reader decodes a
UTF-8 byte sequence as mojibake, the caller writes the record back out, and the
corruption is now committed. That is the exact failure `check_transcoding.py`
exists to detect after the fact. This is the same defect one step earlier, and
CI cannot see either of them because CI is `ubuntu-latest` throughout.

Found by the seat-portability sweep of 2026-08-17 and fixed 2026-08-24, 31 call
sites across 14 files. The sweep named it as documentation. CLAUDE.md asks, for
any finding, whether the fix is a document or a mechanism, and a document would
have been the third time this repository wrote down the encoding rule -- it is
already in CLAUDE.md's landmines and in `redact_emails.write_text`'s docstring
-- while call sites kept being added without it.

The parse check below is not a separate concern bolted on. This scan reads
source with `ast.parse`, and a file that does not parse is a file it silently
skips: it would report clean on a module it never opened, which is the shape of
every defect this gate was written in response to. So a syntax error is a
failure of THIS check, reported as such. Nothing else in this repository ever
asked whether its Python compiles, which is how
`legacy/2025-09_prototype/setup_script.py` sat invalid from the commit that
created it on 2025-09-14 until 2026-08-24 while `pre-commit-hook.sh`
recommended it by name to every developer whose commit failed the ASCII gate.

The two arms have deliberately different scope, and the reasons matter because
an unexplained exclusion is an alibi. The I/O arm sweeps `scripts/` and
`tests/` only: `legacy/2025-09_prototype/` is quarantined by its own README and
nothing under `scripts/` calls it, so rewriting its I/O would be churn in code
kept as provenance; `data/raw/` is an immutable-dump zone and its extraction
prototypes are part of the dump; `tools/` holds two HTML files and no Python.
The parse arm sweeps every `.py` in the repository, because "does this compile"
is a question with no zone politics in it and the two known answers are both
worth pinning -- see KNOWN_UNPARSEABLE.
"""
import ast
import io
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IO_ROOTS = ["scripts", "tests"]
SKIP_DIRS = {"__pycache__", ".git", ".venv-checks", ".venv", "node_modules"}

# Files that are allowed not to compile, each with the reason and neither of
# them a shrug. An entry that stops being unparseable fails this check too:
# the point of the list is that it describes the repository, not that it
# suppresses output.
KNOWN_UNPARSEABLE = {
    os.path.join("data", "raw", "_templates", "extraction_script_template.py"):
        "a fill-in-the-blanks template -- `class [SourceName]Extractor` is a "
        "placeholder, not a bug, and renaming it away from .py would break the "
        "adapter docs that point at it",
    os.path.join("legacy", "2025-09_prototype", "setup_script.py"):
        "SyntaxError at line 250 in every revision git holds of it, from a "
        "nested triple-quote inside the integration-guide string. Quarantined "
        "and never called; see legacy/2025-09_prototype/README.md. Listed "
        "rather than repaired because fixing a module nobody has established a "
        "dependency on would make it look maintained",
}

# The one file that may still hold bare writers, with the count it is allowed.
#
# `clean_events.py` is a documented landmine: it rewrites the serveable zone,
# it once collapsed all_events.json from 1,194 records to 28 on an invocation
# that included --help, and the question of which producer is canonical for
# that zone is unsettled. Editing it to add `newline=` would be a six-line
# change to a file that CLAUDE.md says not to touch until that question is
# answered, so it is exempted rather than fixed.
#
# The count is the point. A bare name on an exemption list grows quietly --
# that is how three timeline_events sidecars claimed 28 of 1,194 records for
# nine months. Six is what was measured on 2026-08-24. A seventh fails this
# check, and so does a fifth, because a drop means somebody fixed the file and
# this entry is now stale cover for whatever lands next.
EXEMPT = {os.path.join("scripts", "transformation", "clean_events.py"): 6}


def source_files():
    """Every .py in the repository, repo-relative, in a stable order."""
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".py"):
                full = os.path.join(dirpath, name)
                yield os.path.relpath(full, REPO_ROOT), full


def in_io_scope(relpath):
    return relpath.split(os.sep)[0] in IO_ROOTS


def mode_of(node):
    """The mode string an open()-alike was called with, "" if not literal."""
    for i, arg in enumerate(node.args):
        if i == 1 and isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return kw.value.value or ""
    return ""


def offenders_in(tree):
    """Text-mode calls that let the platform choose codec or line ending."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            name = "open"
        elif isinstance(node.func, ast.Attribute) and node.func.attr in (
                "open", "read_text", "write_text"):
            # Attribute form only. `check_references.read_text` and
            # `redact_emails.write_text` are module-level helpers of the same
            # names that already do this correctly, and flagging their call
            # sites would train people to ignore this check.
            name = node.func.attr
        else:
            continue

        writing = name == "write_text"
        if name in ("open",):
            mode = mode_of(node)
            if "b" in mode:
                continue
            writing = any(ch in mode for ch in "wax+")

        given = {kw.arg for kw in node.keywords}
        missing = []
        if "encoding" not in given:
            missing.append("encoding")
        if writing and "newline" not in given:
            missing.append("newline")
        if missing:
            found.append((node.lineno, name, "+".join(missing)))
    return found


def main():
    failures = []
    parsed = 0
    io_scanned = 0
    unparseable_seen = set()

    for relpath, full in source_files():
        with io.open(full, encoding="utf-8", newline="") as handle:
            source = handle.read()
        try:
            tree = ast.parse(source, filename=relpath)
        except SyntaxError as exc:
            if relpath in KNOWN_UNPARSEABLE:
                unparseable_seen.add(relpath)
                continue
            failures.append(
                "%s:%s  will not parse (%s) -- this scan therefore did not read "
                "it, and a file it skipped is indistinguishable from a clean one"
                % (relpath, exc.lineno, exc.msg))
            continue
        parsed += 1
        if relpath in KNOWN_UNPARSEABLE:
            failures.append(
                "%s now parses -- delete its KNOWN_UNPARSEABLE entry, which is "
                "otherwise cover for the next file that does not" % relpath)

        if not in_io_scope(relpath):
            continue
        io_scanned += 1

        found = offenders_in(tree)
        allowed = EXEMPT.get(relpath)
        if allowed is not None:
            if len(found) != allowed:
                failures.append(
                    "%s: exemption says %d bare text-I/O call(s), found %d -- "
                    "update or remove the EXEMPT entry" % (relpath, allowed, len(found)))
            continue
        for lineno, name, missing in found:
            failures.append("%s:%d  %s() does not name %s" % (relpath, lineno, name, missing))

    for relpath in sorted(set(KNOWN_UNPARSEABLE) - unparseable_seen):
        failures.append(
            "%s is listed in KNOWN_UNPARSEABLE but was not found -- a list "
            "naming files that are gone stops describing the repository"
            % relpath)

    if failures:
        print("SOURCE PORTABILITY FAILED")
        for line in failures:
            print("  " + line)
        print()
        print("Text-mode reads must pass encoding=; text-mode writes must pass")
        print("encoding= and newline='\\n'. Otherwise the codec and the line")
        print("ending are whatever the machine that ran it happened to use.")
        return 1

    print("Source portability holds: %d file(s) compile (%d known not to), "
          "%d scanned for text I/O, 0 bare calls, %d exempt in %d file(s)."
          % (parsed, len(KNOWN_UNPARSEABLE), io_scanned,
             sum(EXEMPT.values()), len(EXEMPT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Assert that the references in this repository's prose resolve to something.

    python scripts/validation/check_references.py            # offline, gates CI
    python scripts/validation/check_references.py --strict    # warnings gate too
    python scripts/validation/check_references.py --online     # also resolve repo#n via gh

Why this exists
---------------
On 2026-08-06 a cross-repo memo cited a commit as evidence that a sealed
document predated a deliberation. Three readers passed over the line. Nobody
resolved the hash. It pointed at a commit reachable from no ref -- an earlier
attempt that a later rewrite had orphaned -- so the citation offered as proof
resolved to nothing.

The interesting half is that dereferencing it took about ninety seconds and
produced a BETTER answer than the one claimed: the real commit carried a
server-side push timestamp, which is the one timestamp in that chain its author
could not have set. So the unchecked citation was both wrong and needlessly
weak.

A hex string or an issue number inside a sentence READS as evidence. That is the
defect: the form of a citation is doing the work that resolving it is supposed
to do. This repo is dense with them -- cross-repo issue references are a ruled
convention here -- so it is the repo most exposed and the one with the existing
gate discipline to hang the fix on.

Two layers, and only one of them can gate a build
-------------------------------------------------
OFFLINE checks are deterministic, stdlib-only and run in CI. They ask whether a
reference resolves against this repository as it exists right now: does the file
path exist, does the commit resolve, is the issue reference qualified with a
repo the way the convention requires.

ONLINE checks resolve `repo#n` against GitHub via `gh`. They are NOT a gate and
should not become one, for the same reason check_evidence.py refuses to gate its
fetches: a network failure, a rate limit or a transferred issue is not a defect
in this repository. Run it deliberately, read the report, fix what is real.

What gates, and what only warns
-------------------------------
GATING is deliberately narrow, because a check that fails on prose nobody can
fix teaches people to route around it -- and this repo already carries one
cautionary example of exactly that, where an unrelated failing gate was the only
thing holding back a workflow that appended to a file without bound.

  GATE   a dangling repo-relative path in a LIVE document -- the navigational
         files a reader is steered through. If DOCUMENTATION_INDEX.md points at
         a file that does not exist, the index is worse than absent.

  WARN   a dangling path in a HISTORICAL document. docs/sessions/ and docs/adr/
         describe what was true when written. A path that has since moved is a
         fact about the past, not a defect, and rewriting history to satisfy a
         linter would destroy the evidence chain those files exist to hold.

  WARN   a bare `#123` issue reference. The convention says qualify it with its
         repo, and 38 unqualified references predate this checker. Gating on
         them would turn one lesson into a mass edit of prose, which is how the
         ASCII backlog became load-bearing.

  WARN   a hex token that looks like a commit and does not resolve. Most such
         tokens in this repo are decimal ids, example hashes in documentation,
         or commits belonging to sibling repositories, none of which are
         resolvable here. See the false-positive rules below.

The known limit
---------------
This catches references that resolve to NOTHING. It cannot catch a reference
that resolves to the WRONG thing -- a path that exists but no longer contains
what the sentence claims, or an issue number that was reused. Absence is the
failure that actually occurred, twice, and it is the half that is mechanical.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Directories whose .md files describe the past. A dangling path in one of these
# is a fact about when it was written, not a defect to be repaired.
HISTORICAL_PREFIXES = (
    os.path.join("docs", "sessions"),
    os.path.join("docs", "adr"),
    os.path.join("docs", "issues"),
    "legacy",
    "logs",
    "blog",
    # A changelog describes the past by construction. A path it names having
    # since moved is what a changelog is FOR, not a defect in it.
    "CHANGELOG.md",
)

# Sibling repositories. A path or a SHA under one of these names cannot be
# resolved from here and its absence is not evidence of anything.
SIBLING_REPOS = (
    "pdoom1",
    "pdoom1-website",
    "pdoom-dashboard",
    "coordination",
    "beacon",
    "beacon-internal",
    "certes",
)

# First path segments that mean "this repository". A backticked path starting
# with one of these is a claim about this tree and is checkable.
OWN_TOP_LEVEL = (
    "blog",
    "config",
    "data",
    "docs",
    "legacy",
    "logs",
    "scripts",
    "templates",
    "tests",
    "tools",
    ".github",
)

# Additional roots a path may be relative to. The serveable zone's own README
# and LINEAGE files cite paths relative to the zone, not to the repo.
ALTERNATE_ROOTS = (
    "",
    os.path.join("data", "serveable"),
)

EXTENSIONS = r"py|md|json|jsonl|yml|yaml|sh|txt|css|html|toml|cfg|ini"

RE_BACKTICK_PATH = re.compile(r"`([A-Za-z0-9_.][A-Za-z0-9_./-]*\.(?:" + EXTENSIONS + r"))`")
RE_QUALIFIED_ISSUE = re.compile(r"\b([a-z0-9][a-z0-9-]*)#(\d+)\b")
RE_BARE_ISSUE = re.compile(r"(?:^|[^A-Za-z0-9_/#-])#(\d+)\b")
RE_HEXISH = re.compile(r"\b([0-9a-f]{7,40})\b")
RE_REPO_AT_SHA = re.compile(r"\b([a-z0-9][a-z0-9-]*)@([0-9a-f]{7,40})\b")


DRIFT_REGISTRY = os.path.join(REPO_ROOT, "config", "reference_drift.json")


def load_drift():
    """Accepted dangling references, each with a reason someone had to write.

    Same shape as check_workflow_disarm.py's DISARMED list, and for the same
    reason: the registry is what makes accepting a broken reference a deliberate
    act with a name on it, rather than a linter quietly getting weaker. An entry
    without a reason is refused, because 'we accepted this' with no why is
    indistinguishable from having given up.
    """
    if not os.path.exists(DRIFT_REGISTRY):
        return {}
    with io.open(DRIFT_REGISTRY, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    accepted = {}
    for entry in payload.get("accepted", []):
        reason = entry.get("reason", "").strip()
        if not reason:
            raise SystemExit(
                "reference_drift.json: entry for %s has no reason" % entry.get("path"))
        accepted[(entry["path"], entry["reference"])] = reason
    return accepted


class Finding(object):
    def __init__(self, kind, path, line_no, detail, gating):
        self.kind = kind
        self.path = path
        self.line_no = line_no
        self.detail = detail
        self.gating = gating

    def render(self):
        tag = "FAIL" if self.gating else "WARN"
        return "%s  %s:%d  [%s] %s" % (tag, self.path, self.line_no, self.kind, self.detail)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def markdown_files():
    """Every tracked-looking .md file, repo-relative, sorted for stable output."""
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            absolute = os.path.join(dirpath, name)
            relative = os.path.relpath(absolute, REPO_ROOT).replace(os.sep, "/")
            found.append(relative)
    return sorted(found)


def is_historical(relative_path):
    normalised = relative_path.replace("/", os.sep)
    return any(normalised.startswith(prefix) for prefix in HISTORICAL_PREFIXES)


# A synced file carries this header and says DO NOT EDIT DIRECTLY. Its paths are
# claims about the SOURCE repository's tree, not this one, so resolving them here
# asks the wrong question -- and the file may not be edited to satisfy an answer
# anyway. This is the two-clause rule applied to a linter: do not derive what to
# look for from a system other than the one under test.
RE_SYNCED_HEADER = re.compile(
    r"This file is automatically synced from\s+([A-Za-z0-9_.-]+)/", re.IGNORECASE)


def synced_from(text):
    match = RE_SYNCED_HEADER.search(text[:1200])
    if match:
        return match.group(1)
    return None


def belongs_to_sibling(reference):
    head = reference.split("/", 1)[0]
    return head in SIBLING_REPOS


def path_exists_somewhere(reference):
    for root in ALTERNATE_ROOTS:
        candidate = os.path.join(REPO_ROOT, root, reference.replace("/", os.sep))
        if os.path.exists(candidate):
            return True
    return False


def looks_like_our_path(reference):
    """True only when the reference makes a checkable claim about THIS tree.

    A bare filename with no directory is excluded: `README.md` appears in prose
    meaning "the readme of whatever we are discussing" and resolving it here
    would be inventing a claim the author did not make.
    """
    if "/" not in reference:
        return False
    if belongs_to_sibling(reference):
        return False
    head = reference.split("/", 1)[0]
    return head in OWN_TOP_LEVEL


def commit_resolves(sha):
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", sha + "^{commit}"],
            cwd=REPO_ROOT,
            stderr=subprocess.STDOUT,
        )
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def plausible_commit_token(token):
    """Reject the false positives before asking git about a hex string.

    Measured against this repo on 2026-08-06, the naive form of this check found
    nine candidates and every single one was a false positive: three decimal
    ids, two documentation examples, one md5-shaped token, and two commits
    belonging to pdoom1. Requiring a letter removes decimals; the caller removes
    the rest by context.
    """
    if token.isdigit():
        return False
    if not re.search(r"[a-f]", token):
        return False
    if len(token) not in (7, 8, 9, 10, 11, 12, 40):
        return False
    return True


def scan_file(relative_path, findings, drift):
    absolute = os.path.join(REPO_ROOT, relative_path.replace("/", os.sep))
    try:
        text = read_text(absolute)
    except (IOError, OSError, UnicodeDecodeError) as exc:
        findings.append(Finding("unreadable", relative_path, 0, str(exc), True))
        return

    source_repo = synced_from(text)
    if source_repo is not None:
        # Report it once, as information, and check nothing else in the file.
        findings.append(
            Finding(
                "synced-file",
                relative_path,
                1,
                "synced from %s and marked DO NOT EDIT DIRECTLY; its references "
                "describe that tree, so they are not checked here" % source_repo,
                False,
            )
        )
        return

    historical = is_historical(relative_path)

    for line_no, line in enumerate(text.splitlines(), start=1):
        # Paths.
        # A line that names a sibling repo has told you whose tree the path is
        # in. "pdoom1-website, whose `scripts/calculate-game-stats.py`..." is a
        # correct sentence about a file that will never exist here, and a linter
        # that ignores the qualification the author supplied is reading worse
        # than a human would.
        line_names_sibling = any(
            re.search(r"\b%s\b" % re.escape(name), line) for name in SIBLING_REPOS)

        for match in RE_BACKTICK_PATH.finditer(line):
            reference = match.group(1)
            if not looks_like_our_path(reference):
                continue
            if line_names_sibling:
                continue
            if path_exists_somewhere(reference):
                continue
            accepted_reason = drift.get((relative_path, reference))
            if accepted_reason is not None:
                findings.append(
                    Finding(
                        "accepted-drift",
                        relative_path,
                        line_no,
                        "`%s` is absent, accepted: %s" % (reference, accepted_reason),
                        False,
                    )
                )
                continue
            findings.append(
                Finding(
                    "dangling-path",
                    relative_path,
                    line_no,
                    "`%s` does not exist in this tree" % reference,
                    not historical,
                )
            )

        # Issue references. Qualified ones are collected for the online layer;
        # unqualified ones violate a ruled convention and warn.
        stripped = RE_QUALIFIED_ISSUE.sub("", line)
        stripped = RE_REPO_AT_SHA.sub("", stripped)
        for match in RE_BARE_ISSUE.finditer(stripped):
            findings.append(
                Finding(
                    "unqualified-issue",
                    relative_path,
                    line_no,
                    "#%s is not qualified with a repo; a bare number costs a "
                    "context switch to resolve" % match.group(1),
                    False,
                )
            )

        # Commit-shaped tokens. repo@sha is a sibling's commit and unresolvable
        # here, so it is skipped rather than reported as dangling.
        remainder = RE_REPO_AT_SHA.sub("", line)
        for match in RE_HEXISH.finditer(remainder):
            token = match.group(1)
            if not plausible_commit_token(token):
                continue
            if commit_resolves(token):
                continue
            findings.append(
                Finding(
                    "unresolved-commit",
                    relative_path,
                    line_no,
                    "%s looks like a commit and resolves to nothing here; it may "
                    "belong to a sibling repo, in which case write it as "
                    "repo@%s" % (token, token),
                    False,
                )
            )


def collect_qualified_issues(files):
    seen = {}
    for relative_path in files:
        absolute = os.path.join(REPO_ROOT, relative_path.replace("/", os.sep))
        try:
            text = read_text(absolute)
        except (IOError, OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in RE_QUALIFIED_ISSUE.finditer(line):
                repo, number = match.group(1), match.group(2)
                if repo not in SIBLING_REPOS and repo != "pdoom-data":
                    continue
                seen.setdefault((repo, number), []).append((relative_path, line_no))
    return seen


def resolve_online(issues):
    """Resolve repo#n via gh. Never gates -- see the module docstring."""
    problems = []
    for (repo, number), sites in sorted(issues.items()):
        command = [
            "gh", "issue", "view", number,
            "--repo", "PipFoweraker/%s" % repo,
            "--json", "number,state,title",
        ]
        try:
            raw = subprocess.check_output(command, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, OSError) as exc:
            problems.append((repo, number, sites, "unresolved: %s" % _first_line(exc)))
            continue
        try:
            payload = json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            problems.append((repo, number, sites, "unparseable response"))
            continue
        print("  OK   %s#%s  [%s] %s" % (repo, number, payload.get("state", "?"),
                                         payload.get("title", "")[:70]))
    return problems


def _first_line(exc):
    output = getattr(exc, "output", None)
    if output:
        return output.decode("utf-8", "replace").strip().splitlines()[0]
    return str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true",
                        help="warnings gate the build too")
    parser.add_argument("--online", action="store_true",
                        help="also resolve qualified issue references via gh (never gates)")
    args = parser.parse_args()

    files = markdown_files()
    drift = load_drift()
    findings = []
    for relative_path in files:
        scan_file(relative_path, findings, drift)

    gating = [f for f in findings if f.gating]
    warnings = [f for f in findings if not f.gating]

    print("files scanned        : %d" % len(files))
    print("gating findings      : %d" % len(gating))
    print("warnings             : %d" % len(warnings))
    print("")

    for finding in gating:
        print(finding.render())
    if gating:
        print("")

    by_kind = {}
    for finding in warnings:
        by_kind.setdefault(finding.kind, []).append(finding)
    for kind in sorted(by_kind):
        group = by_kind[kind]
        print("%s: %d" % (kind, len(group)))
        for finding in group[:10]:
            print("  " + finding.render())
        if len(group) > 10:
            print("  ... and %d more" % (len(group) - 10))
        print("")

    if args.online:
        issues = collect_qualified_issues(files)
        print("resolving %d distinct issue references via gh" % len(issues))
        problems = resolve_online(issues)
        for repo, number, sites, reason in problems:
            print("  MISS %s#%s  %s" % (repo, number, reason))
            for path, line_no in sites[:3]:
                print("         cited at %s:%d" % (path, line_no))
        print("")
        print("online layer is informational and does not gate")

    failed = len(gating) > 0 or (args.strict and len(warnings) > 0)
    if failed:
        print("REFERENCE CHECK FAILED")
        return 1
    print("All gating reference checks hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

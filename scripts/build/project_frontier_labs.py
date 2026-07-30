"""Project the curated frontier-labs rows into the serveable zone.

    python scripts/build/project_frontier_labs.py           # build
    python scripts/build/project_frontier_labs.py --check   # assert committed
                                                            # output matches a
                                                            # fresh build

data/serveable/ is a build output. Never hand-edit it. This repo previously
lost that property for seven months -- MANIFEST.json said 28 events while
all_events.json said 1,194, because two producers wrote to one zone and
nothing compared them -- so --check exists to make the claim executable rather
than aspirational.

Inputs are split so that evidence and judgement can be reviewed separately:

    data/enrichment/frontier_labs/research/*.json   what was read. Each row
                                                    carries the URL and the
                                                    verbatim sentence. Treat as
                                                    an evidence record and do
                                                    not edit to change a verdict.
    data/enrichment/frontier_labs/curation_table.json  the judgement calls: id,
                                                    lab_kind, inclusion_basis
                                                    and, for editorial rows, the
                                                    reason the mechanical rule
                                                    missed them.

Cross-reference:      the newest data/raw/epoch_ai dump, read-only
Output:               data/serveable/api/frontier_labs/

Every founding date in the input carries the URL that was read and the
verbatim sentence containing the date. Where no citable date was found the
date is null, which is ungated and honest; a fabricated clock is
indistinguishable from a real one later.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABS_DIR = os.path.join(REPO_ROOT, "data", "enrichment", "frontier_labs")
RESEARCH_GLOB = os.path.join(LABS_DIR, "research", "*.json")
CURATION_TABLE = os.path.join(LABS_DIR, "curation_table.json")
EPOCH_GLOB = os.path.join(REPO_ROOT, "data", "raw", "epoch_ai", "dumps", "*", "raw.jsonl")
OUT_DIR = os.path.join(REPO_ROOT, "data", "serveable", "api", "frontier_labs")
SCHEMA = os.path.join(REPO_ROOT, "config", "schemas", "frontier_labs_v1.json")

# The window the collection covers. Organisations whose only Epoch-flagged
# frontier models predate this are out of scope for inclusion_basis
# epoch_frontier_model, though they may still enter editorially.
WINDOW_START = "2000"

SCHEMA_VERSION = "frontier_labs_v1"


def slugify(name):
    """Stable snake_case id.

    Note the trailing-punctuation handling: an earlier slugify in this repo
    stripped a trailing '+', which silently merged PointNet and PointNet++
    into one id. A consumer keying by id loses a record when that happens, and
    nothing errors. So '+' and '.' are transliterated rather than dropped.
    """
    s = name.lower().strip()
    s = s.replace("+", "_plus")
    s = s.replace("&", "_and_")
    s = s.replace(".", "_dot_")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def newest_epoch_dump():
    paths = sorted(glob.glob(EPOCH_GLOB))
    return paths[-1] if paths else None


def epoch_frontier_stats():
    """org name -> {'n', 'first', 'last'} over Epoch-flagged frontier models.

    Epoch's 'Frontier model' flag is era-relative: it marks the 1958 Perceptron
    as frontier for its time. It is also SPARSE -- 123 of 1,034 rows in the
    dump carry it -- so its absence is not evidence an organisation is not
    frontier. DeepSeek, Mistral and Alibaba have no flagged row at all. That
    sparsity is exactly why the collection has a second, editorial inclusion
    basis.
    """
    path = newest_epoch_dump()
    stats = defaultdict(lambda: {"n": 0, "first": None, "last": None})
    if not path:
        return stats, None
    for line in io.open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if str(r.get("Frontier model")).strip() != "True":
            continue
        d = str(r.get("Publication date", "")).strip()
        if not d or d[:4] < WINDOW_START:
            continue
        for org in str(r.get("Organization", "")).split(","):
            org = org.strip()
            if not org:
                continue
            a = stats[org]
            a["n"] += 1
            if a["first"] is None or d < a["first"]:
                a["first"] = d
            if a["last"] is None or d > a["last"]:
                a["last"] = d
    return stats, os.path.relpath(path, REPO_ROOT).replace("\\", "/")


def derive_evidence_strength(row):
    """Grade on source class, not on how confident the prose sounds.

    A statutory register outranks a company's own about page, which outranks
    journalism, which outranks an encyclopedia infobox whose citation does not
    resolve. This is deliberately mechanical: 'how sure am I' is not a
    property of the evidence.
    """
    if row.get("founded") is None:
        return "none"
    ev = row.get("founded_evidence") or {}
    pub = (ev.get("publisher") or "").lower()
    url = (ev.get("url") or "").lower()

    registry_marks = ("companies house", "company-information.service.gov.uk",
                      "recherche-entreprises", "annuaire des entreprises",
                      "sec form", "form 10-k", "form 10-q", "statutory register")
    if any(m in pub for m in registry_marks) or any(m in url for m in registry_marks):
        return "registry"
    if "first-party" in pub or "official" in pub:
        return "first_party"
    if "wikipedia" in pub or "wikipedia" in url or "baike" in url:
        return "secondary"
    if "forbes.com/companies" in url or "investing.com" in url:
        return "secondary"
    return "press"


def load_research():
    """Every row from every research file, with its source file recorded.

    A name appearing in two research files is an error rather than something to
    silently resolve: the two rows may disagree about the date, and picking one
    by file order would hide the disagreement.
    """
    paths = sorted(glob.glob(RESEARCH_GLOB))
    if not paths:
        sys.stderr.write(
            "no research files under %s\n"
            "This collection has no upstream dump to project from; the rows are\n"
            "hand-researched and those files are the source of record.\n"
            % os.path.relpath(os.path.dirname(RESEARCH_GLOB), REPO_ROOT))
        sys.exit(2)
    rows = []
    origin = {}
    for p in paths:
        rel = os.path.relpath(p, REPO_ROOT).replace("\\", "/")
        with io.open(p, encoding="utf-8") as f:
            batch = json.load(f)
        for row in batch:
            name = row["name"]
            if name in origin:
                raise SystemExit(
                    "%r appears in both %s and %s. Two research rows for one "
                    "organisation may disagree; resolve it in the research "
                    "files rather than letting file order decide."
                    % (name, origin[name], rel))
            origin[name] = rel
            row["_research_file"] = rel
            rows.append(row)
    return rows, sorted(set(origin.values()))


def load_curation():
    if not os.path.isfile(CURATION_TABLE):
        sys.stderr.write("missing curation table: %s\n"
                         % os.path.relpath(CURATION_TABLE, REPO_ROOT))
        sys.exit(2)
    with io.open(CURATION_TABLE, encoding="utf-8") as f:
        return json.load(f)


def build():
    rows_in, research_files = load_research()
    table = load_curation()
    curation = table["labs"]

    # Both directions. A researched organisation with no curation entry would
    # be silently dropped; a curation entry with no research would be a row
    # asserting a judgement about something nobody looked up.
    researched = set(r["name"] for r in rows_in)
    curated = set(curation.keys())
    missing_curation = sorted(researched - curated)
    missing_research = sorted(curated - researched)
    if missing_curation:
        raise SystemExit(
            "researched but not in the curation table, so they would be "
            "silently dropped: %s" % ", ".join(missing_curation))
    if missing_research:
        raise SystemExit(
            "in the curation table but never researched: %s"
            % ", ".join(missing_research))

    for row in rows_in:
        row.update({k: v for k, v in curation[row["name"]].items()
                    if k not in ("aliases",)})
        row["aliases"] = curation[row["name"]].get("aliases", [])
        row.setdefault("sources", [])
        # Build the sources list from every URL the research actually cites.
        urls = []
        ev = row.get("founded_evidence") or {}
        if ev.get("url"):
            urls.append(ev["url"])
        for alt in row.get("founded_alternatives", []):
            if alt.get("url"):
                urls.append(alt["url"])
        sev = row.get("status_evidence") or {}
        if sev.get("url"):
            urls.append(sev["url"])
        seen = set()
        row["sources"] = [u for u in urls if not (u in seen or seen.add(u))]
        if not row["sources"]:
            raise SystemExit(
                "%r cites no URL at all. Every row must record what was read, "
                "including rows whose date is null." % row["name"])

    stats, epoch_path = epoch_frontier_stats()

    out = []
    seen_ids = {}
    for row in rows_in:
        name = row["name"]
        rid = row.get("id") or slugify(name)
        if rid in seen_ids:
            raise SystemExit(
                "duplicate id %r from %r and %r -- ids must be unique or a "
                "consumer keying by id silently loses a record"
                % (rid, seen_ids[rid], name))
        seen_ids[rid] = name

        aliases = row.get("aliases", [])
        # Sum Epoch stats across every name this organisation appears under.
        n = 0
        first = None
        last = None
        matched_any = False
        for candidate in [name] + list(aliases):
            if candidate in stats:
                matched_any = True
                a = stats[candidate]
                n += a["n"]
                if a["first"] and (first is None or a["first"] < first):
                    first = a["first"]
                if a["last"] and (last is None or a["last"] > last):
                    last = a["last"]

        rec = {
            "id": rid,
            "name": name,
            "aliases": aliases,
            "founded": row.get("founded"),
            "founded_precision": row.get("founded_precision"),
            "founded_evidence": row.get("founded_evidence"),
            "founded_contested": bool(row.get("founded_contested", False)),
            "founded_alternatives": row.get("founded_alternatives", []),
            "evidence_strength": row.get("evidence_strength") or derive_evidence_strength(row),
            "status": row.get("status", "unknown"),
            "status_date": row.get("status_date"),
            "status_evidence": row.get("status_evidence"),
            "parent_org": row.get("parent_org"),
            "country": row.get("country"),
            "lab_kind": row["lab_kind"],
            "inclusion_basis": row["inclusion_basis"],
            "inclusion_reason": row.get("inclusion_reason"),
            "epoch_frontier_models": n if matched_any else None,
            "epoch_first_frontier_model": first,
            "epoch_last_frontier_model": last,
            "sources": row["sources"],
            "notes": row.get("notes"),
            "extra": row.get("extra", {}),
        }

        # A row claiming the mechanical basis must actually satisfy it.
        if rec["inclusion_basis"] == "epoch_frontier_model" and not matched_any:
            raise SystemExit(
                "%r claims inclusion_basis epoch_frontier_model but matches no "
                "organisation in the Epoch dump under its name or aliases. "
                "Either add the alias Epoch uses, or move the row to editorial "
                "with a reason." % name)

        out.append(rec)

    out.sort(key=lambda r: r["id"])
    return out, epoch_path, research_files, table.get("_inclusion_rule_v1", {})


def validate(records):
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed; schema validation skipped"]
    with io.open(SCHEMA, encoding="utf-8") as f:
        schema = json.load(f)
    errs = []
    v = jsonschema.Draft7Validator(schema)
    for r in records:
        for e in sorted(v.iter_errors(r), key=lambda e: e.path):
            errs.append("%s: %s" % (r["id"], e.message))
    return errs


def ascii_check(records):
    bad = []
    for r in records:
        blob = json.dumps(r, ensure_ascii=False)
        for ch in blob:
            if ord(ch) > 127:
                bad.append("%s: non-ASCII U+%04X (%r)" % (r["id"], ord(ch), ch))
                break
    return bad


def render(records, epoch_path, research_files, inclusion_rule):
    payload = {
        "schema": SCHEMA_VERSION,
        "collection": "frontier_labs",
        "description": (
            "Organisations that develop frontier AI systems. Facts only: no "
            "game impacts, no rarity, no salience. Inclusion is an editorial "
            "judgement and is recorded per row in inclusion_basis."
        ),
        "count": len(records),
        "window_start": WINDOW_START,
        "labs": records,
    }
    lineage = {
        "collection": "frontier_labs",
        "schema": SCHEMA_VERSION,
        "built_by": "scripts/build/project_frontier_labs.py",
        "inputs": {
            "research": research_files,
            "curation_table": os.path.relpath(CURATION_TABLE, REPO_ROOT).replace("\\", "/"),
            "epoch_dump": epoch_path,
        },
        "inclusion_rule": inclusion_rule,
        "counts": {
            "total": len(records),
            "by_inclusion_basis": _count(records, "inclusion_basis"),
            "by_lab_kind": _count(records, "lab_kind"),
            "by_evidence_strength": _count(records, "evidence_strength"),
            "by_status": _count(records, "status"),
            "founded_null": sum(1 for r in records if r["founded"] is None),
            "founded_contested": sum(1 for r in records if r["founded_contested"]),
        },
    }
    return payload, lineage


def _count(records, key):
    c = defaultdict(int)
    for r in records:
        c[r[key]] += 1
    return dict(sorted(c.items()))


def write_json(path, obj):
    """Write via temp + os.replace.

    Never open an existing file with encoding='ascii' for writing: Python
    truncates on open and then raises on the first non-ASCII byte, destroying
    the file before the error surfaces. That ate two files in one session.
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="assert the committed output matches a fresh build; "
                         "write nothing")
    args = ap.parse_args()

    records, epoch_path, research_files, inclusion_rule = build()

    errs = validate(records)
    bad = ascii_check(records)
    for e in errs:
        print("SCHEMA: " + e)
    for b in bad:
        print("ASCII: " + b)
    if errs and not errs[0].startswith("jsonschema not installed"):
        return 1
    if bad:
        return 1

    payload, lineage = render(records, epoch_path, research_files, inclusion_rule)

    feed_path = os.path.join(OUT_DIR, "all_labs.json")
    lineage_path = os.path.join(OUT_DIR, "LINEAGE.json")

    print("labs                : %d" % len(records))
    for k, v in lineage["counts"]["by_inclusion_basis"].items():
        print("  basis %-22s %d" % (k, v))
    for k, v in lineage["counts"]["by_evidence_strength"].items():
        print("  evidence %-19s %d" % (k, v))
    print("founded null        : %d" % lineage["counts"]["founded_null"])
    print("founded contested   : %d" % lineage["counts"]["founded_contested"])

    if args.check:
        if not os.path.isfile(feed_path):
            print("CHECK FAILED: %s does not exist" % feed_path)
            return 1
        with io.open(feed_path, encoding="utf-8") as f:
            committed = json.load(f)
        if committed != payload:
            print("CHECK FAILED: committed feed differs from a fresh build. "
                  "data/serveable/ is a build output; re-run without --check.")
            return 1
        # LINEAGE carries no wall-clock stamp by design, so it must match too.
        if os.path.isfile(lineage_path):
            with io.open(lineage_path, encoding="utf-8") as f:
                if json.load(f) != lineage:
                    print("CHECK FAILED: committed LINEAGE differs from a "
                          "fresh build.")
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

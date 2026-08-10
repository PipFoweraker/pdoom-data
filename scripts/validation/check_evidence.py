"""Assert that evidence actually supports the date it is attached to.

    python scripts/validation/check_evidence.py            # offline, gates CI
    python scripts/validation/check_evidence.py --online   # also fetch URLs
    python scripts/validation/check_evidence.py --online --strict   # gate on fetch

Why this exists
---------------
The frontier-labs build shipped AI21 Labs at month precision -- "November 2017"
-- on Wikipedia's authority. A researcher followed Wikipedia's own cited source
through to the Globes article it named, and found that page contains no founding
date at all. The month was unsupported by the citation offered for it.

That was caught by luck: one researcher happening to follow one link. Nothing in
the pipeline required it. This script makes the cheap half mechanical.

Two layers, and only one of them can gate a build
-------------------------------------------------
OFFLINE checks are deterministic and run in CI. They ask whether a row is
internally coherent: does the quoted sentence contain the date, does the claimed
precision match what the quote supports, is the evidence grade consistent with
the source class, is the cited URL listed in sources.

ONLINE checks fetch the page and ask whether the quote is still there. They are
NOT a gate and never will be, because a remote server being down, rate-limiting,
or rewording a page is not a defect in this repository. Run it periodically,
read the report, fix what is real. --strict exists for a human running it
deliberately, not for CI.

The known limit
---------------
A quote containing the right year, month and day tokens is not proof the
sentence asserts that date. "In 2019, ten years after the 2009 launch..." would
satisfy a check for either year. This catches absence, not misattribution.
Absence is the failure that actually occurred.
"""
import argparse
import io
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABS_FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "frontier_labs", "all_labs.json")

MONTHS = {
    1: ("january", "jan"), 2: ("february", "feb"), 3: ("march", "mar"),
    4: ("april", "apr"), 5: ("may",), 6: ("june", "jun"),
    7: ("july", "jul"), 8: ("august", "aug"), 9: ("september", "sept", "sep"),
    10: ("october", "oct"), 11: ("november", "nov"), 12: ("december", "dec"),
}

# Source classes, in the order derive_evidence_strength grades them. Kept in
# sync with scripts/build/project_frontier_labs.py by the test below rather
# than by anyone remembering.
REGISTRY_MARKS = ("companies house", "company-information.service.gov.uk",
                  "recherche-entreprises", "annuaire des entreprises",
                  "sec form", "form 10-k", "form 10-q", "statutory register")


def normalise(text):
    """Lowercase, collapse whitespace, and neutralise punctuation that varies.

    Sources write '4 November 2019', 'November 4, 2019' and '2019-11-04'. The
    check is on token presence, so commas and hyphens are separators, not
    content.
    """
    t = text.lower()
    t = t.replace(u"\u2013", "-").replace(u"\u2014", "-")  # en dash, em dash
    t = re.sub(r"[,;:()\[\]{}\"'`]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def date_tokens_present(iso, precision, quote):
    """Does the quote carry the parts of `iso` that `precision` claims?

    Returns (ok, missing_part).
    """
    if not iso or not quote:
        return False, "no quote"

    norm = normalise(quote)
    parts = iso.split("-")
    year = parts[0]

    if not re.search(r"\b%s\b" % re.escape(year), norm):
        return False, "year %s" % year

    if precision == "year":
        return True, None

    if len(parts) < 2:
        return False, "precision %s but date has no month" % precision
    month_i = int(parts[1])
    month_words = MONTHS[month_i]
    iso_month = "%s-%02d" % (year, month_i)
    month_hit = (any(re.search(r"\b%s" % w, norm) for w in month_words)
                 or iso_month in norm)
    if not month_hit:
        return False, "month %s" % month_words[0]

    if precision == "month":
        return True, None

    if len(parts) < 3:
        return False, "precision day but date has no day"
    day = int(parts[2])
    # Standalone day number, with or without an ordinal suffix.
    if not re.search(r"\b0?%d(st|nd|rd|th)?\b" % day, norm):
        return False, "day %d" % day

    return True, None


def grade_source(publisher, url):
    """Re-derive evidence_strength from source class alone.

    Mirrors derive_evidence_strength in scripts/build/project_frontier_labs.py.
    Re-deriving here and comparing catches a grade that was inflated by hand
    after the fact -- the ratchet failure mode, where someone re-reads a
    Wikipedia page and marks it first_party.
    """
    pub = (publisher or "").lower()
    u = (url or "").lower()
    if any(m in pub for m in REGISTRY_MARKS) or any(m in u for m in REGISTRY_MARKS):
        return "registry"
    if "first-party" in pub or "official" in pub:
        return "first_party"
    if "wikipedia" in pub or "wikipedia" in u or "baike" in u:
        return "secondary"
    if "forbes.com/companies" in u or "investing.com" in u:
        return "secondary"
    return "press"


def check_offline(labs):
    problems = []
    warnings = []

    for r in labs:
        rid = r["id"]
        ev = r.get("founded_evidence") or {}
        founded = r.get("founded")
        precision = r.get("founded_precision")

        # 1. A dated row must have evidence, and that evidence must carry the date.
        if founded:
            if not ev:
                problems.append("%s: founded=%s but no founded_evidence"
                                % (rid, founded))
            else:
                ok, missing = date_tokens_present(founded, precision,
                                                  ev.get("quote", ""))
                if not ok and not ev.get("date_in_quote") is False:
                    problems.append(
                        "%s: founded=%s (%s) but the quoted sentence does not "
                        "contain %s.\n      quote: %s\n      If the date comes "
                        "from a dateline or masthead rather than the sentence, "
                        "set founded_evidence.date_in_quote=false to declare it."
                        % (rid, founded, precision, missing,
                           (ev.get("quote", "") or "")[:110]))

        # 2. A null date must not carry a precision or a non-none grade.
        else:
            if precision is not None:
                problems.append("%s: founded is null but precision is %r"
                                % (rid, precision))
            if r.get("evidence_strength") != "none":
                problems.append("%s: founded is null but evidence_strength is %r"
                                % (rid, r.get("evidence_strength")))

        # 3. Grade must match source class, not curator confidence.
        if founded and ev:
            derived = grade_source(ev.get("publisher"), ev.get("url"))
            actual = r.get("evidence_strength")
            if actual != derived:
                problems.append(
                    "%s: evidence_strength=%r but the source class derives %r "
                    "from publisher/url. Grades follow the source, not the "
                    "curator's confidence." % (rid, actual, derived))

        # 4. Status evidence must carry the status date.
        sd = r.get("status_date")
        sev = r.get("status_evidence") or {}
        if sd and sev.get("quote"):
            ok, missing = date_tokens_present(sd, _infer_precision(sd),
                                              sev["quote"])
            if not ok and not sev.get("date_in_quote") is False:
                warnings.append(
                    "%s: status_date=%s but its quote does not contain %s"
                    % (rid, sd, missing))

        # 5. Alternatives: WARN, not fail.
        #
        # An alternative is context, not an assertion. Its what_it_represents
        # field exists precisely to explain the gap between what the quote
        # shows and what the date means -- "the sentence says 'today'; the day
        # comes from the article dateline" is a legitimate and common shape.
        # Failing on those would punish the rows that documented themselves
        # best, and would push the next curator toward dropping useful context
        # rather than recording it.
        for i, alt in enumerate(r.get("founded_alternatives") or []):
            if alt.get("date") and alt.get("quote"):
                ok, missing = date_tokens_present(
                    alt["date"], _infer_precision(alt["date"]), alt["quote"])
                if not ok:
                    warnings.append(
                        "%s: founded_alternatives[%d] date=%s, quote lacks %s "
                        "-- check what_it_represents explains why"
                        % (rid, i, alt["date"], missing))

        # 6. Every cited URL must be listed in sources.
        cited = set()
        if ev.get("url"):
            cited.add(ev["url"])
        if sev.get("url"):
            cited.add(sev["url"])
        for alt in r.get("founded_alternatives") or []:
            if alt.get("url"):
                cited.add(alt["url"])
        missing_src = sorted(cited - set(r.get("sources") or []))
        for u in missing_src:
            problems.append("%s: cites %s but it is absent from sources" % (rid, u))

    return problems, warnings


def _infer_precision(iso):
    n = len(iso.split("-"))
    return {1: "year", 2: "month", 3: "day"}[n]


def check_online(labs, timeout=20):
    """Fetch each cited URL and report whether the quote is still present.

    Report only. A remote page changing is not a defect in this repository.
    """
    try:
        from urllib.request import Request, urlopen
        from urllib.error import URLError, HTTPError
    except ImportError:
        return ["urllib unavailable"], []

    seen = {}
    findings = []
    for r in labs:
        ev = r.get("founded_evidence") or {}
        url, quote = ev.get("url"), ev.get("quote")
        if not url or not quote:
            continue
        if url in seen:
            body = seen[url]
        else:
            try:
                req = Request(url, headers={
                    "User-Agent": "pdoom-data evidence checker "
                                  "(+https://github.com/PipFoweraker/pdoom-data)"})
                body = urlopen(req, timeout=timeout).read().decode(
                    "utf-8", errors="replace")
            except (HTTPError, URLError, OSError, ValueError) as e:
                body = None
                findings.append("%s: FETCH FAILED %s -- %s"
                                % (r["id"], url, str(e)[:80]))
            seen[url] = body
        if not body:
            continue
        # Compare on a whitespace-normalised, tag-stripped body.
        text = normalise(re.sub(r"<[^>]+>", " ", body))
        needle = normalise(quote)[:90]
        if needle not in text:
            findings.append(
                "%s: quote not found on the live page. Either it was reworded, "
                "or it was never there.\n      %s\n      looking for: %s"
                % (r["id"], url, needle[:90]))
    return findings, []


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--online", action="store_true",
                    help="also fetch each cited URL and look for the quote")
    ap.add_argument("--strict", action="store_true",
                    help="with --online, exit nonzero on fetch findings too. "
                         "For a human running this deliberately; never CI.")
    args = ap.parse_args()

    if not os.path.isfile(LABS_FEED):
        print("missing %s -- run project_frontier_labs.py first"
              % os.path.relpath(LABS_FEED, REPO_ROOT))
        return 2

    with io.open(LABS_FEED, encoding="utf-8") as f:
        labs = json.load(f)["labs"]

    problems, warnings = check_offline(labs)

    dated = sum(1 for r in labs if r.get("founded"))
    print("rows                 : %d" % len(labs))
    print("with a date          : %d" % dated)
    print("offline checks       : %d problem(s), %d warning(s)"
          % (len(problems), len(warnings)))

    for w in warnings:
        print("WARN:  " + w)
    for p in problems:
        print("FAIL:  " + p)

    online_bad = []
    if args.online:
        print()
        print("fetching cited URLs (report only unless --strict)...")
        online_bad, _ = check_online(labs)
        for f in online_bad:
            print("ONLINE: " + f)
        print("online findings      : %d" % len(online_bad))

    print()
    if problems:
        print("FAILED: evidence does not support what is claimed of it.")
        return 1
    if args.online and args.strict and online_bad:
        print("FAILED (strict): online findings present.")
        return 1
    print("All evidence checks hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

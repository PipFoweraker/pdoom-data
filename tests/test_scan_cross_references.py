"""Prove the scan cross-reference check fires, and fires only where it should.

    python tests/test_scan_cross_references.py

Why a test rather than trusting the checker's own clean run
-----------------------------------------------------------
`check_scan_claims.py` reports that every cross-reference in the four
2026-08-14 payloads resolves. That is the answer we wanted, which is exactly
when a check deserves the least trust: a detector that never fires and a
detector that cannot fire produce identical output. This repository already
has the scar -- the redaction verifier reported clean while ten records still
carried addresses.

What the check is for
---------------------
Scan records cite each other, and cite the served corpus, by slug inside their
flags. `project_watchlist.py` reads the same citations to seed
`possible_duplicate_of`, but resolves them with `if slug in known_slugs`, which
DISCARDS a slug that does not resolve. A flag citing a record that does not
exist degrades there into no link at all, silently. These cases assert it is
loud here instead.

What the check deliberately does NOT do, and no case here asserts otherwise:

  * It does not validate duplicate DETECTION. Comparing similarity-found pairs
    against `possible_duplicate_of` would be one computation over the payloads
    checked against another computation over the same payloads.
  * It does not check claims made about record POSITIONS. The 2026 payload's
    `known_overlap` says "Records 1, 2 and 20", of which only 20 is right, and
    nothing mechanical catches that because the claim is prose about indices.
    Structured cross-payload claims are the fix; see the payloads README.
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_scan_claims as csc

FAILURES = []

SERVED = {"ai_summit_pivot_2023_2025", "eu_ai_act_watering_down_2024"}


def check(label, condition, detail=""):
    if condition:
        print("  ok   " + label)
    else:
        print("  FAIL " + label + ((" -- " + detail) if detail else ""))
        FAILURES.append(label)


def record(slug, flags):
    return {"slug": slug, "flags": flags}


def fires(payloads, served=SERVED):
    problems, _ = csc.check_cross_references(payloads, served)
    return problems


def test_clean_cases_pass():
    print("cases that must NOT fire")

    check("a flag citing the served corpus",
          not fires({"2026-01-01_a.json": {"records": [
              record("real_one", ["endpoint of ai_summit_pivot_2023_2025"])]}}))

    check("a flag citing a record in another payload",
          not fires({
              "2026-01-01_a.json": {"records": [record("alpha_beta_gamma", [])]},
              "2026-01-01_b.json": {"records": [
                  record("delta_epsilon_zeta", ["same matter as alpha_beta_gamma"])]},
          }))

    check("a record citing its own slug",
          not fires({"2026-01-01_a.json": {"records": [
              record("alpha_beta_gamma", ["alpha_beta_gamma is this record"])]}}))

    check("a payload naming a payload that exists",
          not fires({
              "2026-01-01_a.json": {"records": [
                  record("alpha_beta_gamma", ["also in 2026-01-01_b.json"])]},
              "2026-01-01_b.json": {"records": []},
          }))

    check("prose with no slug-shaped tokens",
          not fires({"2026-01-01_a.json": {"records": [
              record("alpha_beta_gamma",
                     ["Source returned 403. Verify before promotion."])]}}))

    check("a two-segment token is not mistaken for a slug",
          not fires({"2026-01-01_a.json": {"records": [
              record("alpha_beta_gamma", ["date_kind is action, not reported"])]}}))


def test_the_failures_it_exists_for():
    print("cases that MUST fire")

    check("a flag citing a slug that exists nowhere",
          fires({"2026-01-01_a.json": {"records": [
              record("real_one", ["same matter as totally_made_up_slug_2026"])]}}))

    check("a flag naming a payload that does not exist",
          fires({"2026-01-01_a.json": {"records": [
              record("real_one", ["also in 2026-01-01_ghost.json"])]}}))

    check("a bad slug in payload-level known_overlap",
          fires({"2026-01-01_a.json": {
              "known_overlap": "overlaps phantom_record_here_2026",
              "records": []}}))

    check("a bad slug in scanner_limits",
          fires({"2026-01-01_a.json": {
              "scanner_limits": ["could not reach nonexistent_thing_2026"],
              "records": []}}))

    # The served corpus is the only input this check reads that the scans did
    # not produce. Losing it must fail rather than quietly weaken the check.
    check("the served corpus being unreadable",
          fires({"2026-01-01_a.json": {"records": [
              record("real_one", ["endpoint of ai_summit_pivot_2023_2025"])]}},
                served=None))


def test_the_real_payloads_resolve():
    """Integration: the committed payloads must pass with the real corpus."""
    print("the committed corpus")
    import glob
    import json

    payloads = {}
    for path in sorted(glob.glob(os.path.join(
            REPO_ROOT, "data", "raw", "llm_event_scan", "payloads", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            payloads[os.path.basename(path)] = json.load(handle)

    served = csc.load_served_slugs()
    check("the served corpus is readable", served is not None)
    problems, external = csc.check_cross_references(payloads, served)
    check("every cross-reference in the committed payloads resolves",
          not problems, "; ".join(problems))
    check("at least one citation reaches the served corpus", external > 0,
          "external=%d -- if this drops to 0 the external half is dead" % external)


def main():
    for fn in (test_clean_cases_pass,
               test_the_failures_it_exists_for,
               test_the_real_payloads_resolve):
        fn()
    print()
    if FAILURES:
        print("%d failure(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("scan cross-references: all cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

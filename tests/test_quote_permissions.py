#!/usr/bin/env python3
"""Prove the quote gate refuses the things it exists to refuse.

    python tests/test_quote_permissions.py

An empty corpus passes trivially, which proves nothing. Every case below is
synthetic and exercises the decision directly, because a gate tested only
against data that currently passes is a gate tested against one sample. This
repository has shipped three checks that could not fail.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "validation"))

import check_quote_permissions as cqp  # noqa: E402

CHECKS = [0]
FAILURES = []


def check(condition, message):
    CHECKS[0] += 1
    print(("  PASS  " if condition else "  FAIL  ") + message)
    if not condition:
        FAILURES.append(message)


def quote(**over):
    row = {
        "id": "test:one",
        "text": "The hard part is not building it, it is knowing what we built.",
        "author": {"name": "A Named Person", "is_pseudonym": False},
        "source_url": "https://example.org/post",
        "archive_url": "https://web.archive.org/web/2026/https://example.org/post",
        "source_platform": "personal_blog",
        "published_at": "2024-05-01",
        "retrieved_at": "2026-08-30",
        "placements": ["death_screen"],
        "permission": {"basis": "licence", "licence_spdx": "CC0-1.0",
                       "licence_url": "https://example.org/licence"},
    }
    for key, value in over.items():
        if key == "permission" and isinstance(value, dict):
            row["permission"] = value
        else:
            row[key] = value
    return row


def fails(row):
    return bool(cqp.failures_for([row]))


def main():
    print("quote permissions: the default is not permission\n")

    print("MUST NOT FIRE")
    check(not fails(quote()), "a CC0 blog quote with an archive and a placement passes")
    check(not fails(quote(permission={
        "basis": "granted", "granted_by": "A Named Person",
        "granted_at": "2026-08-30", "granted_via": "email",
        "context_shown_to_author": "shown the death screen mockup"})),
        "a fully recorded personal grant passes")
    check(not fails(quote(source_platform="arxiv_abstract", permission={
        "basis": "licence", "licence_spdx": "CC0-1.0",
        "licence_url": "https://arxiv.org/help/license"})),
        "an arXiv ABSTRACT under CC0 passes: abstracts are released as metadata")
    check(not fails(quote(source_platform="ea_forum", published_at="2023-03-01")),
        "an EA Forum post after 2022-12-01 passes on the site licence")
    check(not fails(quote(permission={"basis": "not_yet_asked"})),
        "an unasked quote is FINE to hold: it is simply not servable")
    check(not fails(quote(permission={"basis": "refused",
                                      "refused_note": "declined by email"})),
        "a refusal with its reason recorded is a valid, permanent record")

    print("\nMUST FIRE -- the licence cases the brief established")
    check(fails(quote(source_platform="lesswrong")),
          "LessWrong cannot rest on a licence: its terms license MIRI, not the public")
    check(fails(quote(source_platform="alignment_forum")),
          "nor can the Alignment Forum, which shares those terms")
    check(fails(quote(source_platform="ea_forum", published_at="2021-06-01")),
          "an EA Forum post BEFORE 2022-12-01 is ordinary copyright")
    check(fails(quote(permission={"basis": "licence", "licence_spdx": "CC-BY-SA-4.0",
                                  "licence_url": "https://x"})),
          "share-alike is refused, as it is everywhere else in this repo")
    check(fails(quote(permission={"basis": "licence", "licence_spdx": "CC-BY-NC-4.0",
                                  "licence_url": "https://x"})),
          "non-commercial is refused: the game is a commercial product")
    check(fails(quote(permission={"basis": "licence", "licence_spdx": "CC-BY-ND-4.0",
                                  "licence_url": "https://x"})),
          "no-derivatives is refused: excerpting is what a quote IS")
    check(fails(quote(permission={"basis": "licence", "licence_url": "https://x"})),
          "basis 'licence' with no named licence is not a basis")

    print("\nMUST FIRE -- consent is to a context, not to a reuse")
    check(fails(quote(permission={
        "basis": "granted", "granted_by": "A Named Person",
        "granted_at": "2026-08-30", "granted_via": "email"})),
        "a grant with no record of what the author was SHOWN is not a grant "
        "for that placement")
    check(fails(quote(permission={
        "basis": "granted", "granted_at": "2026-08-30", "granted_via": "email",
        "context_shown_to_author": "mockup"})),
        "an unnamed grantor is an anonymous verdict, which ADR-001 forbids")

    print("\nMUST FIRE -- silence, absence and pseudonymity")
    check(fails(quote(permission={"basis": "refused"})),
          "a refusal with no reason recorded gets overturned by the next reader")
    check(fails(quote(archive_url=None)),
          "servable with no archive: the source can be edited or deleted under us")
    check(fails(quote(placements=[])),
          "servable but cleared for nowhere")
    check(fails(quote(author={"name": "throwaway_2019", "is_pseudonym": True})),
          "a pseudonymous author served with no attempt to reach the person")
    check(not fails(quote(author={"name": "throwaway_2019", "is_pseudonym": True,
                                  "identification_attempts": "DMed twice, no reply"},
                          permission={"basis": "not_yet_asked"})),
          "but holding that same pseudonymous quote unserved is fine")

    print("\nasked_no_reply is NOT permission")
    check(not fails(quote(permission={"basis": "asked_no_reply"})),
          "it is a valid state to record")
    row = quote(permission={"basis": "asked_no_reply"})
    check((row["permission"]["basis"] not in cqp.SERVABLE_BASES),
          "and it is not in SERVABLE_BASES: silence is not consent")

    print("\nACCOUNTABILITY: quoting someone who is not being agreed with")
    def acct(**over):
        row = quote(
            quote_kind="accountability",
            speaker_status="public_figure",
            source_platform="journalism",
            verbatim_verified={"against_primary_source": True,
                               "checked_by": "Pip Foweraker",
                               "checked_at": "2026-08-30",
                               "full_context_url": "https://example.org/full"},
            juxtaposition={"what_happened": "The safety team was disbanded.",
                           "occurred_at": "2024-05-17",
                           "evidence_urls": ["https://example.org/report"],
                           "evidence_retrieved_at": "2026-08-30"},
            framing_text="Said in 2022. In 2024 the team was disbanded.",
            permission={"basis": "granted", "granted_by": "Subject",
                        "granted_at": "2026-08-30", "granted_via": "email",
                        "context_shown_to_author": "shown the screen"})
        row.update(over)
        return row

    check(not fails(acct()),
          "a verified quote beside a dated, evidenced outcome passes")
    check(fails(acct(verbatim_verified={"against_primary_source": False,
                                        "full_context_url": "https://x"})),
          "MUST FIRE: not checked against a primary source")
    check(fails(acct(verbatim_verified={"against_primary_source": True,
                                        "full_context_url": None})),
          "MUST FIRE: no link to the full context, so a cropping claim has no answer")
    check(fails(acct(juxtaposition={"what_happened": "The team was disbanded.",
                                    "evidence_urls": []})),
          "MUST FIRE: the outcome carries no evidence")
    check(fails(acct(juxtaposition=None)),
          "MUST FIRE: an accountability quote with nothing set against it")
    check(fails(acct(speaker_status=None)),
          "MUST FIRE: no record of whether the speaker is a public figure")

    print("\nTHE FRAMING GUARD: say what happened, not what they knew")
    for phrase in ("He lied about it.", "She knowingly downplayed it.",
                   "They deliberately misled investors.",
                   "This was a cover-up.", "A fraud on the public."):
        check(fails(acct(framing_text=phrase)),
              "MUST FIRE: game-voice framing %r asserts a state of mind" % phrase)
    check(not fails(acct(framing_text=
          "Said in 2022. By 2024 the team named here no longer existed.")),
          "but dated evidence in the game's voice is fine")
    check(not fails(acct(text="I did not lie about our safety work.")),
          "and the guard NEVER touches the quote itself: if they said it, they said it")

    print("\ndifficulty quotes are not held to the accountability bar")
    check(not fails(quote(quote_kind="difficulty")),
          "a CoD-style quote about the problem being hard needs no juxtaposition")

    print("\n%d checks, %d failed" % (CHECKS[0], len(FAILURES)))
    if FAILURES:
        for failure in FAILURES:
            print("  FAILED: %s" % failure)
        return 1
    print("OK: nothing is servable until a named basis says so.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

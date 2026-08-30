"""No quote is servable until a named basis says it may be.

    python scripts/validation/check_quote_permissions.py

WHY THIS EXISTS, AND WHY IT IS A GATE RATHER THAN A GUIDELINE. This repository
has already published invented text attributed to unnamed safety researchers,
on all 1,194 served events, for months (pdoom-data#92, #76). A corpus of REAL
people's words carries the same failure mode with a real person on the other
end of it. ADR-001 forbids anonymous verdicts; this is the same rule pointed at
quotations.

THE DEFAULT IS NOT PERMISSION. `not_yet_asked` is the state a quote is born in,
and it is an ABSENCE rather than a value, the same shape the watch list uses
for untriaged atoms. `asked_no_reply` is also not permission: silence is not
consent, and a workflow that treats it as consent will eventually quote someone
who was ignoring it on purpose.

WHAT THE SOURCING BRIEF ESTABLISHED, and why the platform rules below are not
guesswork:

  LessWrong and the Alignment Forum grant NO third-party reuse right. Their
  terms give MIRI a licence to operate the site; that licence does not extend
  to anyone else, and there is no per-post Creative Commons option. These are
  the two most quote-dense sources for this subject, and neither can ever rest
  on a licence. Only a person saying yes will do.

  The EA Forum is split by date. CC BY 4.0 is mandatory from 2022-12-01. Posts
  before that are ordinary copyright unless that author added a licence clause
  to that post, so the date is load-bearing rather than decorative.

  arXiv has no site-wide licence. Abstracts are released as CC0 metadata and
  are quotable; full text is whatever the author chose, the modal choice grants
  no reuse right at all, and TWO of the six options are share-alike.

Share-alike is refused mechanically here for the same reason validate_candidate
refuses an -SA dump: it would reach into this project's own licensing. NC and
ND are refused too, because the game is a commercial product and ND forbids the
excerpting a quote inherently is.
"""

import io
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUOTES = os.path.join(REPO_ROOT, "data", "curated", "quotes", "quotes.jsonl")

# Words that assert what a person KNEW or INTENDED, as opposed to what they
# said and what later happened.
#
# THE DISTINCTION THIS ENCODES. Reproducing someone's own words accurately, and
# setting them beside a dated, evidenced outcome, leaves the inference to the
# player. Saying the person lied asserts a fact about their state of mind,
# which is a much harder thing to stand behind and a much easier thing to sue
# over. The juxtaposition is also the stronger rhetoric: a reader who works it
# out themselves is more convinced than one who is told.
#
# Scoped to framing_text ONLY, the game's own voice. It never applies to the
# quote itself: if the speaker used one of these words, that is what they said.
#
# This is a drafting guard, not legal advice, and it is not a substitute for a
# lawyer on the accountability tier.
STATE_OF_MIND_ASSERTIONS = (
    "lied", "lying", "liar", "knowingly", "deliberately misled",
    "deliberately", "intentionally", "covered up", "cover-up", "coverup",
    "fraud", "fraudulent", "conspired", "conspiracy", "perjur", "corrupt",
    "knew full well", "knew the truth",
)

SERVABLE_BASES = ("licence", "granted")
TOMBSTONE_BASES = ("refused", "withdrawn")

# Platforms whose terms license the operator, not the public. A quote from one
# of these can NEVER rest on a licence, however the record is filled in.
NO_PUBLIC_LICENCE = ("lesswrong", "alignment_forum")

EA_FORUM_CC_BY_FROM = "2022-12-01"


def load(path=None):
    path = path or QUOTES
    if not os.path.isfile(path):
        return []
    with io.open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def failures_for(rows):
    out = []
    seen = set()
    for row in rows:
        qid = row.get("id", "<no id>")
        if qid in seen:
            out.append("%s: duplicate id" % qid)
        seen.add(qid)

        perm = row.get("permission") or {}
        basis = perm.get("basis")
        platform = row.get("source_platform")

        if basis not in ("licence", "granted", "not_yet_asked",
                         "asked_no_reply", "refused", "withdrawn"):
            out.append("%s: unknown permission basis %r" % (qid, basis))
            continue

        # A tombstone is permanent and must carry its reason, so that nobody
        # who never saw the refusal can quietly reintroduce the quote.
        if basis in TOMBSTONE_BASES:
            if not perm.get("refused_note"):
                out.append("%s: basis is %r but no refused_note records why. A "
                           "refusal without a reason is a refusal that gets "
                           "overturned by the next person who reads the file."
                           % (qid, basis))
            continue

        if basis not in SERVABLE_BASES:
            continue                      # not_yet_asked / asked_no_reply: fine, just not servable

        # ---- from here down the record CLAIMS to be servable ----

        if basis == "licence":
            if platform in NO_PUBLIC_LICENCE:
                out.append(
                    "%s: %s grants no third-party reuse licence, so basis "
                    "'licence' cannot be true here. Its terms license the site "
                    "operator, not the public. Ask the author." % (qid, platform))
                continue

            spdx = (perm.get("licence_spdx") or "").strip()
            if not spdx:
                out.append("%s: basis 'licence' with no licence_spdx. Name the "
                           "licence or it is not a basis." % qid)
                continue
            upper = spdx.upper()
            for bad, why in (("-SA", "share-alike would reach into this "
                                     "project's own licensing"),
                             ("-NC", "the game is a commercial product"),
                             ("-ND", "no-derivatives forbids the excerpting a "
                                     "quote inherently is")):
                if bad in upper:
                    out.append("%s: licence %s contains %s, refused: %s"
                               % (qid, spdx, bad, why))
            if not perm.get("licence_url"):
                out.append("%s: basis 'licence' with no licence_url. A licence "
                           "we cannot point at is not a licence." % qid)

            if platform == "ea_forum":
                published = row.get("published_at") or ""
                if published < EA_FORUM_CC_BY_FROM:
                    out.append(
                        "%s: EA Forum post dated %r predates %s, when CC BY 4.0 "
                        "became mandatory. Earlier posts are ordinary copyright "
                        "unless that author added a licence clause to that post. "
                        "Record the clause or ask the author."
                        % (qid, published or "unknown", EA_FORUM_CC_BY_FROM))

        if basis == "granted":
            for field, why in (
                    ("granted_by", "a grant with no named grantor is anonymous, "
                                   "which ADR-001 forbids"),
                    ("granted_at", "an undated grant cannot be checked"),
                    ("granted_via", "a grant we cannot point at is not a grant"),
                    ("context_shown_to_author",
                     "consent is to a CONTEXT, not just to a reuse. A yes given "
                     "without being told about the death screen is not a yes "
                     "for the death screen")):
                if not perm.get(field):
                    out.append("%s: basis 'granted' but %s is empty: %s"
                               % (qid, field, why))

        # Applies to both servable bases.
        author = row.get("author") or {}
        if author.get("is_pseudonym") and not author.get("identification_attempts"):
            out.append(
                "%s: pseudonymous author served with no identification_attempts "
                "recorded. Someone who chose not to attach their name to this "
                "gets more diligence, not less." % qid)

        if not row.get("archive_url"):
            out.append("%s: servable with no archive_url. Forum posts get edited "
                       "and deleted; without a capture we cannot later show we "
                       "quoted it correctly." % qid)

        if not row.get("placements"):
            out.append("%s: servable but cleared for no placement. A grant for a "
                       "loading screen is not a grant for a death screen." % qid)

        out.extend(_accountability_failures(row, qid))

    return out


def _accountability_failures(row, qid):
    """Extra requirements for a quote that sets someone's words against events.

    A 'difficulty' quote says the problem is hard, and the speaker is being
    agreed with. An 'accountability' quote sets a named person's own words
    beside what happened next, and the speaker is not. The second needs to be
    right in ways the first does not.
    """
    out = []
    framing = row.get("framing_text") or ""
    lowered = framing.lower()
    for phrase in STATE_OF_MIND_ASSERTIONS:
        if phrase in lowered:
            out.append(
                "%s: framing_text says %r, which asserts what the speaker knew "
                "or intended rather than what they said and what followed. Give "
                "the dated evidence and let the player draw it: that is both "
                "easier to stand behind and harder to argue with."
                % (qid, phrase))

    if row.get("quote_kind") != "accountability":
        return out

    if not row.get("speaker_status"):
        out.append("%s: an accountability quote must record whether the speaker "
                   "is a public figure or a private individual." % qid)

    verified = row.get("verbatim_verified") or {}
    if not verified.get("against_primary_source"):
        out.append(
            "%s: not verified against a PRIMARY source. A misquote repeated "
            "accurately is still a misquote, and accuracy is the single "
            "biggest thing standing between this and a problem." % qid)
    if not verified.get("full_context_url"):
        out.append("%s: no full_context_url. The answer to 'you cropped me' is "
                   "that the whole thing is one click away." % qid)

    jux = row.get("juxtaposition") or {}
    if not jux.get("what_happened"):
        out.append("%s: an accountability quote with nothing set against it is "
                   "just a quote. Record the dated outcome, or file it as "
                   "quote_kind 'other'." % qid)
    elif not (jux.get("evidence_urls") or []):
        out.append("%s: the outcome carries no evidence. Every date in "
                   "config/sources.json names what was read; this is the same "
                   "rule and it matters more here." % qid)

    return out


def main():
    rows = load()
    problems = failures_for(rows)

    if problems:
        print("CHECK FAILED: a quote claims a basis it does not have.")
        for problem in problems:
            print("  - %s" % problem)
        return 1

    servable = sum(1 for r in rows
                   if (r.get("permission") or {}).get("basis") in SERVABLE_BASES)
    tombstoned = sum(1 for r in rows
                     if (r.get("permission") or {}).get("basis") in TOMBSTONE_BASES)
    print("quote permissions: %d quote(s), %d servable, %d permanently refused "
          "or withdrawn, %d awaiting an answer"
          % (len(rows), servable, tombstoned, len(rows) - servable - tombstoned))
    return 0


if __name__ == "__main__":
    sys.exit(main())

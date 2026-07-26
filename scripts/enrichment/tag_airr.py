#!/usr/bin/env python3
"""Tag candidates against the MIT AI Risk Repository Domain Taxonomy.

The vocabulary is LEARNED FROM THE SOURCE'S OWN LABELLED ROWS rather than
hand-written by whoever ran this script. The AI Risk Database ships ~1,400
risk descriptions already labelled with their domain, which is training data
sitting in plain sight. Deriving weights from it means the tagger reflects how
the taxonomy's authors actually use their own categories.

Method: per-token log-odds weights per domain, with additive smoothing. A
candidate is scored against each domain by summing the weights of its tokens.
The top domain is assigned ONLY if it beats the runner-up by a margin;
otherwise the record is left untagged. Abstention is deliberate -- an untagged
record costs a reviewer nothing, a confidently wrong tag costs trust.

Output is an ENRICHMENT LAYER, not a modification of any record:
    data/enrichment/airr_tags/machine_v1.json

It is an opinion, machine-produced, low confidence, and clearly labelled as
such. Human tags at higher precedence can override it.

Usage:
    python scripts/enrichment/tag_airr.py --evaluate    # measure only
    python scripts/enrichment/tag_airr.py               # measure then write
"""

import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter, defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "adapters"))

import _base  # noqa: E402

LAYER_ID = "machine_v1"
LAYER_VERSION = "0.1.0"
OUT_DIR = os.path.join(REPO_ROOT, "data", "enrichment", "airr_tags")
FEED = os.path.join(REPO_ROOT, "data", "serveable", "api", "candidates",
                    "all_candidates.jsonl")

SMOOTHING = 0.5
MIN_TOKEN_LEN = 3
MIN_MARGIN = 0.15   # top domain must beat runner-up by this share of its score
MIN_MATCHED_TOKENS = 4
HOLDOUT_FRACTION = 0.2
SEED = 20260725     # fixed: this script must be reproducible

STOPWORDS = set("""
the and for that with from this which are may can not but has have had was were
its their they them there then than when where what who whom whose will would
should could been being into onto upon over under about after before during
such some more most other others any all each both few own same too very
also however therefore thus while because although though due via per
ai system systems model models human humans use used using user users
risk risks harm harms result results lead leads leading cause causes caused
example examples including include includes e.g i.e etc
""".split())


def tokenize(text):
    if not text:
        return []
    words = re.findall(r"[a-z][a-z0-9\-]+", str(text).lower())
    return [w for w in words if len(w) >= MIN_TOKEN_LEN and w not in STOPWORDS]


def latest_dump(source_id):
    dumps = os.path.join(REPO_ROOT, "data", "raw", source_id, "dumps")
    if not os.path.isdir(dumps):
        return None
    stamps = sorted(os.listdir(dumps))
    return os.path.join(dumps, stamps[-1]) if stamps else None


def load_labelled():
    """Rows carrying both a Domain label and descriptive text."""
    dump = latest_dump("mit_airr")
    if dump is None:
        raise SystemExit("No mit_airr dump. Run scripts/adapters/mit_airr.py first.")
    path = os.path.join(dump, "risk_database.jsonl")
    examples = []
    for line in open(path, encoding="ascii"):
        row = json.loads(line)
        domain = row.get("Domain")
        text = " ".join(filter(None, [
            row.get("Description"), row.get("Risk category"),
            row.get("Risk subcategory"), row.get("Additional ev."),
        ]))
        if domain and text.strip():
            examples.append((domain, text))
    return examples, dump


def train(examples):
    """Per-domain log-odds token weights with additive smoothing."""
    per_domain = defaultdict(Counter)
    totals = Counter()
    vocabulary = set()
    for domain, text in examples:
        tokens = tokenize(text)
        per_domain[domain].update(tokens)
        totals[domain] += len(tokens)
        vocabulary.update(tokens)

    grand_counts = Counter()
    for domain in per_domain:
        grand_counts.update(per_domain[domain])
    grand_total = sum(totals.values())
    size = len(vocabulary) or 1

    weights = {}
    for domain in per_domain:
        inside = per_domain[domain]
        inside_total = totals[domain]
        outside_total = grand_total - inside_total
        table = {}
        for token in vocabulary:
            a = inside.get(token, 0)
            b = grand_counts.get(token, 0) - a
            p_in = (a + SMOOTHING) / (inside_total + SMOOTHING * size)
            p_out = (b + SMOOTHING) / (outside_total + SMOOTHING * size)
            table[token] = math.log(p_in / p_out)
        weights[domain] = table
    return weights, sorted(per_domain.keys())


def classify(text, weights, domains):
    tokens = tokenize(text)
    if len(tokens) < MIN_MATCHED_TOKENS:
        return None, 0.0, len(tokens), "too_few_tokens"
    scores = {}
    for domain in domains:
        table = weights[domain]
        scores[domain] = sum(table.get(t, 0.0) for t in tokens) / len(tokens)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top, top_score = ranked[0]
    runner_score = ranked[1][1] if len(ranked) > 1 else 0.0
    spread = abs(top_score) if top_score else 1e-9
    margin = (top_score - runner_score) / spread
    if margin < MIN_MARGIN:
        return None, margin, len(tokens), "margin_below_threshold"
    return top, margin, len(tokens), "ok"


def confidence_for(tokens, margin):
    """Confidence falls with text length, because the model was trained on
    paragraph-length risk descriptions and most candidates are short titles.

    Observed during bring-up: on long text the tagger is right about 82% of
    the time, but on bare titles it misplaced SolidGoldMagikarp and "The Rise
    of Parasitic AI" into Privacy & Security when both are system-safety
    findings. Reporting one confidence for both regimes would be dishonest.
    """
    if tokens >= 25 and margin >= 0.35:
        return "medium"
    if tokens >= 12 and margin >= 0.25:
        return "low"
    return "very_low"


def evaluate(examples):
    """Held-out top-1 accuracy. An UPPER BOUND on real performance, not an
    estimate of it: these are AIRR risk descriptions, whereas candidates are
    forum-post and model-release titles. The distribution shift is large and
    unmeasured."""
    rng = random.Random(SEED)
    shuffled = list(examples)
    rng.shuffle(shuffled)
    cut = int(len(shuffled) * (1 - HOLDOUT_FRACTION))
    train_set, test_set = shuffled[:cut], shuffled[cut:]
    weights, domains = train(train_set)

    correct = attempted = abstained = 0
    baseline = Counter(d for d, _ in train_set).most_common(1)[0][1] / float(len(train_set))
    for domain, text in test_set:
        predicted, _margin, _n, reason = classify(text, weights, domains)
        if predicted is None:
            abstained += 1
            continue
        attempted += 1
        if predicted == domain:
            correct += 1
    return {
        "train_size": len(train_set),
        "test_size": len(test_set),
        "attempted": attempted,
        "abstained": abstained,
        "coverage": round(attempted / float(len(test_set)), 4) if test_set else 0.0,
        "accuracy_when_attempted": round(correct / float(attempted), 4) if attempted else 0.0,
        "majority_class_baseline": round(baseline, 4),
        "caveat": (
            "Upper bound only. Measured on AIRR risk descriptions; candidates "
            "are forum-post and model-release titles, a different and much "
            "shorter text distribution. Real accuracy on candidates is "
            "UNMEASURED and expected to be materially lower."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluate", action="store_true",
                        help="measure held-out accuracy and stop")
    args = parser.parse_args()

    examples, dump_dir = load_labelled()
    print("labelled examples: %d from %s"
          % (len(examples), os.path.relpath(dump_dir, REPO_ROOT).replace("\\", "/")))

    metrics = evaluate(examples)
    print("--- held-out evaluation ---")
    for key in ("train_size", "test_size", "coverage", "accuracy_when_attempted",
                "majority_class_baseline", "abstained"):
        print("  %-26s %s" % (key, metrics[key]))
    print("  NOTE: %s" % metrics["caveat"])

    if args.evaluate:
        return 0

    if not os.path.isfile(FEED):
        print("No candidate feed at %s; run the projection first." % FEED)
        return 1

    weights, domains = train(examples)
    tags = {}
    reasons = Counter()
    for line in open(FEED, encoding="ascii"):
        record = json.loads(line)
        text = " ".join(filter(None, [
            record.get("title"), record.get("summary"),
            " ".join((record.get("extra") or {}).get("forum_tags") or []),
        ]))
        predicted, margin, ntokens, reason = classify(text, weights, domains)
        reasons[reason] += 1
        if predicted is None:
            continue
        tags[record["id"]] = {
            "domain": predicted,
            "margin": round(margin, 4),
            "tokens_used": ntokens,
            "confidence": confidence_for(ntokens, margin),
        }

    print("--- applied to candidates ---")
    print("  tagged   : %d" % len(tags))
    for reason, count in reasons.most_common():
        print("  %-24s %d" % (reason, count))
    spread = Counter(v["domain"] for v in tags.values())
    for domain, count in spread.most_common():
        print("    %5d  %s" % (count, domain))

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "_metadata": {
            "layer": "airr_tags",
            "layer_id": LAYER_ID,
            "layer_version": LAYER_VERSION,
            "precedence": "low (machine-produced; any human tag overrides)",
            "nature": (
                "MACHINE OPINION, not fact. Domain assignment inferred from "
                "token statistics, not read by a person."
            ),
            "produced_at": _base.utc_now_iso(),
            "taxonomy_source": "mit_airr Domain Taxonomy v1",
            "taxonomy_dump": os.path.relpath(dump_dir, REPO_ROOT).replace("\\", "/"),
            "method": (
                "Per-domain log-odds token weights trained on the AI Risk "
                "Database's own labelled descriptions; top domain assigned "
                "only when it beats the runner-up by a margin, else abstain."
            ),
            "parameters": {
                "smoothing": SMOOTHING, "min_margin": MIN_MARGIN,
                "min_matched_tokens": MIN_MATCHED_TOKENS,
                "min_token_len": MIN_TOKEN_LEN, "seed": SEED,
            },
            "evaluation": metrics,
            "observed_weakness": (
                "Accuracy on short titles is materially worse than the "
                "held-out figure and is UNMEASURED. Concrete misses seen "
                "during bring-up: 'SolidGoldMagikarp' and 'The Rise of "
                "Parasitic AI' were both assigned Privacy & Security when "
                "both are AI system safety findings. Treat very_low "
                "confidence tags as a starting filter, never as a label."
            ),
            "tagged_count": len(tags),
            "abstained_count": sum(v for k, v in reasons.items() if k != "ok"),
        },
        "tags": tags,
    }
    out_path = os.path.join(OUT_DIR, "%s.json" % LAYER_ID)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="ascii", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, out_path)
    print("wrote %s" % os.path.relpath(out_path, REPO_ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

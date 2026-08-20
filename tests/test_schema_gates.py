"""Assert that candidate_v1.json can actually reject things.

    python tests/test_schema_gates.py

Why this exists
---------------
The maturity ladder awards bronze for `has a schema` and `validates`. Both
predicates are passed by committing a file containing `{"type": "object"}`.
A collection would then report BRONZE having gained a consumer exactly nothing.

So the ladder measures that a schema EXISTS and that the data AGREES with it.
Neither predicate can see whether the schema constrains anything at all. This
file is the missing half: it takes a real served record, breaks it in ways that
matter, and requires the schema to notice.

The direction of failure is the point. A schema that wrongly REJECTS good data
announces itself immediately -- the build goes red and someone looks. A schema
that wrongly ACCEPTS bad data is silent forever, which is the same shape as the
redaction verifier that used a broken pattern and reported clean over ten
records that still carried addresses. Every MUST_FIRE case below is a specific
way of failing open, and three of them were found failing open while this file
was being written:

  - `^https?://[^ ]+$` matched a NEWLINE-joined pair of URLs, because the
    negated-space class excludes spaces and not newlines. It reported 19 bad
    records where there were 65.
  - the negated-whitespace class with a `$` anchor still accepted a URL with one
    trailing newline, because Python's `re` treats `$` as end-of-string-or-
    before-final-newline while ECMA-262, which JSON Schema specifies, treats it
    as end-of-input. The host regex engine, not the schema, decided the answer.
  - the first `confidence` enum was copied from `_provenance` and did not carry
    `very_low`, so it rejected 1,197 legitimate records. That one failed CLOSED
    and was found within a minute, which is the asymmetry restated.

Each case is named for the real defect it stands for, not for the field it
edits, because `test_bad_field_7` teaches nothing when it fires in two years.
"""
import copy
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(REPO, "config", "schemas", "candidate_v1.json")
SERVED = os.path.join(REPO, "data", "serveable", "api", "candidates",
                      "all_candidates.jsonl")


def load_schema():
    return json.load(io.open(SCHEMA, encoding="utf-8"))


def served_records():
    out = []
    for line in io.open(SERVED, encoding="utf-8"):
        if line.strip():
            out.append(json.loads(line))
    return out


def pick_base(validator, records):
    """A record that validates today, with at least one review and one signal.

    Chosen from the corpus rather than hand-written: a hand-written base drifts
    away from the real shape and the mutations then test a record that no
    producer emits.
    """
    for r in records:
        if list(validator.iter_errors(r)):
            continue
        if r.get("reviews") and r.get("signals") and r.get("source_urls"):
            return r
    return None


def mutate(base, path, value, delete=False):
    r = copy.deepcopy(base)
    node = r
    for k in path[:-1]:
        node = node[k]
    if delete:
        node.pop(path[-1], None)
    else:
        node[path[-1]] = value
    return r


# (name, mutation) pairs. Each MUST be rejected by the schema.
def must_fire_cases(base):
    cases = [
        ("a Share-Alike licence reaches the served zone",
         mutate(base, ["license", "spdx"], "CC-BY-SA-4.0")),
        ("a Share-Alike licence hidden inside a longer expression",
         mutate(base, ["license", "spdx"], "CC-BY-4.0 AND CC-BY-SA-3.0")),

        ("a verdict is published with no reviewer named (ADR-001)",
         mutate(base, ["reviews", 0, "reviewer"], "", delete=True)),
        ("a verdict is published with an empty reviewer string",
         mutate(base, ["reviews", 0, "reviewer"], "")),
        ("a verdict value nobody has defined",
         mutate(base, ["reviews", 0, "verdict"], "probably")),
        ("a review carrying no timestamp",
         mutate(base, ["reviews", 0, "at"], None, delete=True)),

        ("a bare salience field, the exact thing ADR-001 forbids",
         mutate(base, ["salience"], 0.91)),
        ("a salience profile key with no version in it",
         mutate(base, ["salience_by_profile"], {"default": 0.5})),
        ("an empty salience map, which reads as scored-zero not unscored",
         mutate(base, ["salience_by_profile"], {})),
        ("a salience value that is a string",
         mutate(base, ["salience_by_profile"], {"default_v1": "high"})),
        ("a tier outside A-D",
         mutate(base, ["salience_tier_by_profile"], {"default_v1": "S"})),

        ("a guessed date in a format nothing parses",
         mutate(base, ["occurred_at"], "sometime in 2024")),
        ("a date with no zero padding, which sorts wrongly as a string",
         mutate(base, ["occurred_at"], "2024-3-1")),
        ("a datetime where the schema promises a date",
         mutate(base, ["published_at"], "2024-03-01T00:00:00Z")),

        ("two URLs joined by a comma in one string, so neither fetches",
         mutate(base, ["source_urls"], ["https://a.example/x, https://b.example/y"])),
        ("two URLs joined by a NEWLINE, the form that defeated the first pattern",
         mutate(base, ["source_urls"], ["https://a.example/x\nhttps://b.example/y"])),
        ("two URLs joined by a semicolon",
         mutate(base, ["source_urls"], ["https://a.example/x; https://b.example/y"])),
        ("a URL with one trailing newline, the form that defeated the second pattern",
         mutate(base, ["source_urls"], ["https://a.example/x\n"])),
        ("a schemeless URL, the form epoch_models.py silently drops",
         mutate(base, ["source_urls"], ["arxiv.org/abs/2501.14818"])),
        ("prose in a URL field, the form Epoch's own Link column contains",
         mutate(base, ["source_urls"], ["Eunbi Choi, Kibong Choi, Sehyun Chun"])),
        ("an archive URL with the same joined-string defect",
         mutate(base, ["archive_urls"], ["https://a.example/x https://b.example/y"])),

        ("a truncated content hash",
         mutate(base, ["content_sha256"], "40f29ddb")),
        ("a content hash in upper case, so two spellings of one hash exist",
         mutate(base, ["content_sha256"], "A" * 64)),

        ("a record kind no adapter declared",
         mutate(base, ["kind"], "podcast_episode")),
        ("a review status no consumer knows how to branch on",
         mutate(base, ["review_status"], "done")),
        ("a privacy flag as a string, which is truthy for the wrong reason",
         mutate(base, ["privacy_review_required"], "false")),

        ("a signal recorded as a bare number, with its observation date lost",
         mutate(base, ["signals"], {"karma": [913]})),
        ("a signal with a value but no observed_at",
         mutate(base, ["signals"], {"karma": [{"value": 913}]})),

        ("a provenance confidence outside the three-level vocabulary",
         mutate(base, ["_provenance", "title"],
                {"confidence": "pretty sure", "layer": "raw", "method": "upstream_field"})),
        ("a provenance entry that does not say how the value was derived",
         mutate(base, ["_provenance", "title"],
                {"confidence": "high", "layer": "raw"})),

        ("an enrichment layer with no version, so a rerun cannot be told apart",
         mutate(base, ["airr_tags_by_layer"], {"machine": {"confidence": "low"}})),

        ("an id with no source prefix, so provenance is unrecoverable",
         mutate(base, ["id"], "iKm2FhpWkuuBojm82")),
        ("an empty title",
         mutate(base, ["title"], "")),

        ("an undeclared top-level field, the defect that broke event_v1 on 1,166 records",
         mutate(base, ["source_id"], "epoch_ai")),
    ]
    # Every required field, removed one at a time. Generated rather than typed,
    # so a field added to `required` gains a test without anyone remembering to.
    schema = load_schema()
    for field in schema.get("required", []):
        cases.append(("required field '%s' is missing" % field,
                      mutate(base, [field], None, delete=True)))
    return cases


# Each MUST be accepted. These are the legitimate shapes a too-strict schema
# would break, and breaking them would push producers to weaken the schema.
def must_not_fire_cases(base):
    return [
        ("an unknown occurrence date, left null rather than guessed",
         mutate(base, ["occurred_at"], None)),
        ("an unknown source-availability date, left null",
         mutate(base, ["source_available_at"], None)),
        ("no content hash, because the source stores no retrievable body",
         mutate(base, ["content_sha256"], None)),
        ("no machine enrichment yet, on 299 of 3,434 records",
         mutate(base, ["airr_tags_by_layer"], None, delete=True)),
        ("no reuse_basis, which only the forum licences carry",
         mutate(base, ["license", "reuse_basis"], None, delete=True)),
        ("a licence with no canonical url, as NOASSERTION has none",
         mutate(base, ["license", "url"], None)),
        ("an unreviewed record, which is the default and the majority",
         mutate(base, ["reviews"], [])),
        ("a review with a null note, layer and tier_override",
         mutate(base, ["reviews", 0, "note"], None)),
        ("a second salience profile added by a consumer-specific build",
         mutate(base, ["salience_by_profile"],
                {"default_v1": 0.5, "pdoom1_engine_v2": 0.9})),
        ("source-specific passthrough in extra, deliberately unconstrained",
         mutate(base, ["extra"], {"anything": {"nested": [1, 2, 3]}})),
        ("a privacy verdict, which exists on two records",
         mutate(base, ["reviews", 0, "verdict"], "privacy")),
        ("a very_low enrichment confidence, which 1,197 records carry",
         mutate(base, ["airr_tags_by_layer"],
                {"machine_v1": {"confidence": "very_low"}})),
        ("an evidence_count on a provenance entry, which all 3,434 carry",
         mutate(base, ["_provenance", "source_available_at"],
                {"confidence": "high", "layer": "registry",
                 "method": "config/sources.json", "evidence_count": 2})),
        ("multiple source URLs, correctly given as separate list items",
         mutate(base, ["source_urls"],
                ["https://a.example/x", "https://b.example/y"])),
    ]


def main():
    try:
        import jsonschema
    except ImportError:
        print("FAIL: jsonschema is not installed, so this gate cannot run.")
        print("      A gate that cannot run is not a gate that passes.")
        print("      pip install -r requirements-checks.txt")
        return 1

    schema = load_schema()
    validator = jsonschema.Draft7Validator(schema)
    records = served_records()

    base = pick_base(validator, records)
    if base is None:
        print("FAIL: no served record validates against candidate_v1.json.")
        print("      Without a known-good base every mutation below would be")
        print("      rejected for the wrong reason, and the suite would pass")
        print("      while measuring nothing.")
        return 1

    failures = []

    # Structural checks, run before the mutations. A schema of `{"type":
    # "object"}` would otherwise reach the generated cases and die on a KeyError
    # three frames down -- which does exit non-zero, but reports a Python bug
    # where the real finding is "this schema promises a consumer nothing".
    # Failing for the wrong reason is how a check stops being read.
    if not schema.get("required"):
        failures.append("VACUOUS: the schema requires no fields at all, so "
                        "every record validates and bronze means nothing")
    if schema.get("additionalProperties") is not False:
        failures.append("VACUOUS: additionalProperties is not false, so an "
                        "undeclared field is served without anyone being told "
                        "-- this is exactly the 'source_id' defect that put "
                        "1,166 timeline_events records outside event_v1")

    for name, record in must_fire_cases(base):
        if not list(validator.iter_errors(record)):
            failures.append("MUST FIRE but did not: %s" % name)

    for name, record in must_not_fire_cases(base):
        errs = list(validator.iter_errors(record))
        if errs:
            failures.append("MUST NOT FIRE but did: %s -- %s"
                            % (name, errs[0].message[:90]))

    n_fire = len(must_fire_cases(base))
    n_not = len(must_not_fire_cases(base))

    if failures:
        print("SCHEMA GATE FAILED")
        for f in failures:
            print("  " + f)
        print()
        print("%d must-fire and %d must-not-fire cases; %d wrong."
              % (n_fire, n_not, len(failures)))
        return 1

    print("schema gate: %d must-fire and %d must-not-fire cases pass, "
          "against base record %s" % (n_fire, n_not, base["id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

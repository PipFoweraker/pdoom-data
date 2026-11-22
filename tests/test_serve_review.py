"""The screen review server writes exactly what the keyboard tools write.

    python tests/test_serve_review.py

Runs the real HTTP server on a free localhost port against TEMPORARY copies of
the watch list, its log and decisions.jsonl, so nothing here can touch a real
judgement. Asserts:

  * triage keys set the same fields triage_watch.KEYS says they set, and log first;
  * month-end accept/reject refuse an empty reason (the reason is published);
  * a description decision carries the reviewer, serves the trimmed abstract,
    and an editorial is stored BESIDE the description, never in place of it;
  * the overlay the timeline build applies ignores the editorial entirely;
  * a POST from a foreign Origin is refused (a web page can POST to localhost).
"""
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts", "review"))
sys.path.insert(0, os.path.join(REPO, "scripts", "build"))

import triage_watch as tw            # noqa: E402
import review_descriptions as rd     # noqa: E402
import serve_review as sr            # noqa: E402

FAILURES = []


def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + ("" if cond or not detail else " -- " + detail))
    if not cond:
        FAILURES.append(label)


def post(base, path, body, origin=None):
    data = json.dumps(body).encode("ascii")
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    if origin:
        req.add_header("Origin", origin)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode("ascii"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("ascii"))


def main():
    tmp = tempfile.mkdtemp(prefix="serve_review_test_")
    try:
        watch = os.path.join(tmp, "candidates.jsonl")
        shutil.copy(tw.WATCHLIST, watch)
        tw.WATCHLIST, tw.LOG = watch, os.path.join(tmp, "triage_log.jsonl")
        rd.DECISIONS_DIR = tmp
        rd.DECISIONS = os.path.join(tmp, "decisions.jsonl")

        proposal = {"id": "test:paper", "arxiv_id": "0000.00000", "source_url": "https://arxiv.org/abs/0000.00000",
                    "current_title": "A Paper", "arxiv_title": "A Paper", "title_matches": True,
                    "chars_dropped": [], "current_description": "1 Introduction\n----",
                    "abstract_ascii": "We study a thing. " * 60}
        props = os.path.join(tmp, "data.jsonl")
        with io.open(props, "w", encoding="ascii", newline="\n") as h:
            h.write(json.dumps(proposal) + "\n")

        state = sr.State("Test Reviewer", props)
        state.rel = lambda p: os.path.basename(p)
        httpd = sr.ThreadingHTTPServer(("127.0.0.1", sr.free_port(18741)), sr.make_handler(state, "<html></html>"))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % httpd.server_address[1]

        print("watch triage")
        atom = state.rows[0]["id"]
        code, row = post(base, "/api/watch/triage", {"id": atom, "key": "a"})
        check("a puts the atom on Watch with rating A", code == 200 and row["rating"] == "A" and row["watch_status"] == "watching", str(row)[:120])
        check("watching clears decided_by", row.get("decided_by") is None)
        with io.open(tw.LOG, encoding="ascii") as h:
            log = [json.loads(l) for l in h]
        check("the log holds the decision, attributed", log and log[-1]["by"] == "Test Reviewer" and log[-1]["next"]["rating"] == "A")
        on_disk = {json.loads(l)["id"]: json.loads(l) for l in io.open(watch, encoding="ascii")}
        check("the atom file is rewritten on disk", on_disk[atom]["watch_status"] == "watching")
        code, _ = post(base, "/api/watch/triage", {"id": atom, "key": "z"})
        check("an unknown key is refused", code == 400)

        print("month end")
        code, body = post(base, "/api/watch/decide", {"id": atom, "status": "accepted", "note": "  "})
        check("accept without a reason is refused", code == 400, str(body))
        code, row = post(base, "/api/watch/decide", {"id": atom, "status": "rejected", "note": "tertiary source only"})
        check("reject with a reason records it and the decider", code == 200 and row["decision_note"] == "tertiary source only" and row["decided_by"] == "Test Reviewer")
        code, body = post(base, "/api/watch/gate", {"id": atom})
        check("the producer's gate answers", code == 200 and isinstance(body.get("reasons"), list), str(body)[:120])

        print("descriptions")
        code, row = post(base, "/api/descriptions/decide", {"id": "test:paper", "verdict": "accept_abstract",
                                                             "editorial": "  Short   version.  "})
        check("accept serves the trimmed abstract", code == 200 and row["description"] == rd.trim(proposal["abstract_ascii"]))
        check("the trim is at most 600 chars", len(row["description"]) <= 604)
        check("the editorial is stored beside it, attributed",
              row.get("editorial", {}).get("text") == "Short version." and row["editorial"]["by"] == "Test Reviewer")
        check("the description is NOT the editorial", row["description"] != "Short version.")
        import project_timeline_events as pte
        pte.CURATED_DESCRIPTIONS = rd.DECISIONS
        overlay = pte.load_description_overlay([])
        check("the build overlay serves the abstract, not the editorial",
              overlay.get("test:paper", {}).get("description") == row["description"])
        code, row = post(base, "/api/descriptions/decide", {"id": "test:paper", "verdict": "keep_current"})
        check("keep_current carries no description and no editorial", row["description"] is None and "editorial" not in row)

        print("origin")
        code, body = post(base, "/api/watch/triage", {"id": atom, "key": "b"}, origin="https://evil.example")
        check("a foreign Origin is refused", code == 403, str(body))
        check("and changed nothing", state.by_id[atom]["watch_status"] == "rejected")

        httpd.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if FAILURES:
        print("\n%d case(s) failed." % len(FAILURES))
        return 1
    print("\nserve_review: every front-end write matches the shared implementation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Criteria 4 (appeals) and 5 (bad input), three trials each.  python run_checks.py --label before

run_eval.py only sends {text, creator_id} bodies to /submit, so these two live
here: an appeal needs a real content_id from an earlier submission, and one of
the bad inputs is a bare JSON list, which run_eval's "bodies" can't express.
"""
import argparse, datetime as dt, json, time, uuid

import requests

import config
import audit

TEXT = ("The meeting ran long because nobody could agree on the budget. Sam wanted to cut the "
        "travel line, but Priya argued that the conference was the only reason we landed two "
        "clients last year. We left it for next week.")


def log_len():
    return len(audit.read_entries())


def criterion4(url, trial):
    """10 valid appeals -> under_review + one new appeal entry each; 5 unknown ids -> 404, no entry."""
    ok = 0
    samples = []
    for i in range(10):
        r = requests.post(f"{url}/submit", json={"text": TEXT, "creator_id": f"chk4_{trial}_{i}"}).json()
        cid = r["content_id"]
        before = len([e for e in audit.entries_for(cid) if e.get("event") == "appeal"])
        resp = requests.post(f"{url}/appeal", json={"content_id": cid, "reasoning": f"my own work, trial {trial}"})
        body = resp.json()
        after = len([e for e in audit.entries_for(cid) if e.get("event") == "appeal"])
        good = resp.status_code == 200 and body.get("status") == "under_review" and after == before + 1
        ok += good
        if i == 0:
            samples.append({"status_code": resp.status_code, "body": body})
    bad_ok = 0
    for i in range(5):
        n = log_len()
        resp = requests.post(f"{url}/appeal", json={"content_id": f"nope{uuid.uuid4().hex[:6]}", "reasoning": "x"})
        bad_ok += resp.status_code == 404 and log_len() == n
        if i == 0:
            samples.append({"status_code": resp.status_code, "body": resp.json()})
    return {"valid_ok": f"{ok}/10", "unknown_ok": f"{bad_ok}/5", "samples": samples}


def criterion5(url, trial):
    """6 bad inputs -> 4xx with JSON error, never 5xx, each leaves a rejected log entry."""
    cases = [
        ("missing text", {"creator_id": f"chk5_{trial}_a"}),
        ("empty text", {"text": "", "creator_id": f"chk5_{trial}_b"}),
        ("whitespace text", {"text": "   \n ", "creator_id": f"chk5_{trial}_c"}),
        ("missing creator_id", {"text": TEXT}),
        ("body is a list", ["not", "an", "object"]),
        ("50,000 chars", {"text": "word " * 10000, "creator_id": f"chk5_{trial}_f"}),
    ]
    ok, rows = 0, []
    for name, body in cases:
        n = log_len()
        resp = requests.post(f"{url}/submit", json=body)
        try:
            payload = resp.json()
            is_json = isinstance(payload, dict) and "error" in payload
        except ValueError:
            payload, is_json = resp.text[:100], False
        logged = log_len() == n + 1 and audit.read_entries(limit=1)[0].get("event") == "rejected"
        good = 400 <= resp.status_code < 500 and is_json and logged
        ok += good
        rows.append({"case": name, "status_code": resp.status_code, "json_error": is_json,
                     "logged_rejection": logged, "pass": good, "body": payload})
    return {"ok": f"{ok}/6", "rows": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--label", default="")
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--url", default=f"http://{config.HOST}:{config.PORT}")
    a = p.parse_args()
    out = {"criterion_4": [], "criterion_5": []}
    for t in range(1, a.trials + 1):
        out["criterion_4"].append(criterion4(a.url, t))
        out["criterion_5"].append(criterion5(a.url, t))
        print(f"trial {t}: c4 valid {out['criterion_4'][-1]['valid_ok']} unknown {out['criterion_4'][-1]['unknown_ok']} | c5 {out['criterion_5'][-1]['ok']}")
        if t < a.trials:
            time.sleep(61)  # bad inputs with no creator_id share one address-keyed limit
    config.RESULTS_DIR.mkdir(exist_ok=True)
    path = config.RESULTS_DIR / f"checks_{dt.datetime.now():%Y-%m-%d_%H%M}{'_' + a.label if a.label else ''}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote", path.relative_to(config.ROOT))


if __name__ == "__main__":
    main()

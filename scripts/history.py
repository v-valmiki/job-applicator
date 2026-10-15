"""Append-only application + account history (<local>/applications.jsonl, accounts.jsonl).

Never stores passwords. CLI:
  history.py log --company C --title T --url U --status S [--resume path] [--note N]
  history.py account --company C --portal-url U --email E [--note N]
  history.py check --url U      (prints latest record; exit 1 if none)
  history.py summary
"""
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resumes  # noqa: E402

ROOT = resumes.ROOT
STATUSES = ("filled", "submitted", "blocked", "skipped", "error")


def profile_path():
    return Path(os.environ.get("JOB_APPLICATOR_PROFILE") or ROOT / "profile.yml")


def profile_version():
    try:
        return hashlib.sha256(profile_path().read_bytes()).hexdigest()[:8]
    except OSError:
        return None


def _append(name, rec):
    with open(resumes.local_dir() / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(name):
    out = []
    try:
        with open(resumes.local_dir() / name, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def _no_pass(names):
    bad = [n for n in names if "pass" in str(n).lower()]
    if bad:
        raise ValueError(f"refusing to store passwords (argument: {bad[0]})")


def log_application(company, title, url, status, resume=None, note="", **extra):
    _no_pass(extra)
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "company": company,
           "title": title, "url": url, "status": status, "note": note,
           "resume": None, "resume_sha256": None, "profile_version": profile_version()}
    if resume:
        sha, _ = resumes.archive_file(resume)
        rec["resume"], rec["resume_sha256"] = Path(resume).name, sha
    _append("applications.jsonl", rec)
    return rec


def log_account(company, portal_url, email, note="", **extra):
    _no_pass(extra)
    rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "company": company,
           "portal_url": portal_url, "email": email, "note": note}
    _append("accounts.jsonl", rec)
    return rec


def applied(url):
    latest = None
    for r in _read("applications.jsonl"):
        if r.get("url") == url:
            latest = r
    return latest


def summary():
    latest = {}
    for r in _read("applications.jsonl"):
        latest[r.get("url")] = r
    counts = {}
    for r in latest.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"counts": counts, "latest": list(latest.values())}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if any("pass" in x.lower() for x in a if x.startswith("-")):
        print("error: refusing to accept or store passwords", file=sys.stderr)
        return 2
    ap = argparse.ArgumentParser(prog="history.py")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("log")
    for k in ("company", "title", "url"):
        p.add_argument("--" + k, required=True)
    p.add_argument("--status", required=True, choices=STATUSES)
    p.add_argument("--resume")
    p.add_argument("--note", default="")
    p = sp.add_parser("account")
    p.add_argument("--company", required=True)
    p.add_argument("--portal-url", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--note", default="")
    sp.add_parser("check").add_argument("--url", required=True)
    sp.add_parser("summary")
    try:
        n = ap.parse_args(a)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    if n.cmd == "log":
        print(json.dumps(log_application(n.company, n.title, n.url, n.status, n.resume, n.note)))
    elif n.cmd == "account":
        print(json.dumps(log_account(n.company, n.portal_url, n.email, n.note)))
    elif n.cmd == "check":
        r = applied(n.url)
        if r is None:
            return 1
        print(json.dumps(r))
    else:
        print(json.dumps(summary(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

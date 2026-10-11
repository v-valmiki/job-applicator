"""Discord I/O for the application agent: ping the user when blocked, optionally wait for a reply.

Config (env vars win over a gitignored `.env` at repo root):
  DISCORD_WEBHOOK_URL, DISCORD_USER_ID, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID
"""
import json, os, re, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
API = "https://discord.com/api/v10"
KEYS = ("DISCORD_WEBHOOK_URL", "DISCORD_USER_ID", "DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID")
LABELS = {"captcha": "CAPTCHA", "login": "Login needed", "account_creation": "Account creation",
          "question": "Question", "error": "Error", "other": "Attention needed"}
KINDS = tuple(LABELS)


def load_config():
    """KEY=VALUE lines from .env, overridden by real environment variables."""
    cfg = {}
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip("\"'")
    except OSError:
        pass
    for k in KEYS:
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    return {k: cfg.get(k, "") for k in KEYS}


def local_dir():
    d = Path(os.environ.get("JOB_APPLICATOR_LOCAL_DIR") or ROOT / "local")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _http(method, url, payload=None, headers=None):
    """Returns (status, parsed_json_or_None). Never raises on HTTP error codes."""
    h = {"Content-Type": "application/json", "User-Agent": "job-applicator-bot"}
    h.update(headers or {})
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read()
    try:
        return status, json.loads(body) if body else None
    except ValueError:
        return status, None


def _request(method, url, payload=None, headers=None, retries=5):
    """_http with 429 handling. Errors never include the URL/token (they are secrets)."""
    for _ in range(retries):
        status, body = _http(method, url, payload, headers)
        if status == 429:
            time.sleep(float((body or {}).get("retry_after", 1)) + 0.05)
            continue
        if status >= 400:
            raise RuntimeError(f"discord http {status}")
        return body
    raise RuntimeError("discord rate limited too many times")


def format_message(kind, company, title, detail, url=None, user_id=""):
    label = LABELS.get(kind, LABELS["other"])
    head = f"<@{user_id}> " if user_id else ""
    lines = [f"{head}**{label}**: {company} - {title}", detail]
    if url:
        lines.append(url)
    if kind == "question":
        lines.append("Reply with your answer (start with `answer:` if replying in Discord).")
    else:
        lines.append("Fix it in the Chrome tab (or answer here / in the Manus app), then reply `done`. "
                     "Reply `skip` to skip this job.")
    return "\n".join(lines)[:2000]


def can_read(cfg):
    return bool(cfg["DISCORD_BOT_TOKEN"] and cfg["DISCORD_CHANNEL_ID"])


def _send(cfg, content):
    """Send via bot if fully configured (so replies can be correlated), else webhook. -> message id."""
    allowed = {"users": [cfg["DISCORD_USER_ID"]]} if cfg["DISCORD_USER_ID"] else {"parse": []}
    payload = {"content": content, "allowed_mentions": allowed}
    if can_read(cfg):
        body = _request("POST", f"{API}/channels/{cfg['DISCORD_CHANNEL_ID']}/messages", payload,
                        {"Authorization": f"Bot {cfg['DISCORD_BOT_TOKEN']}"})
    else:
        url = cfg["DISCORD_WEBHOOK_URL"]
        if not url:
            raise RuntimeError("DISCORD_WEBHOOK_URL is not set")
        body = _request("POST", url + ("&" if "?" in url else "?") + "wait=true", payload)
    return str((body or {}).get("id", ""))


def ping(kind, company, title, detail, url=None, cfg=None):
    cfg = cfg or load_config()
    return _send(cfg, format_message(kind, company, title, detail, url, cfg["DISCORD_USER_ID"]))


def norm_question(q):
    return " ".join(re.sub(r"[^\w\s]", " ", q.lower()).split())


def parse_reply(text):
    t = text.strip()
    low = t.lower().rstrip(".! ")
    if low == "done":
        return {"status": "done", "text": ""}
    if low == "skip":
        return {"status": "skipped", "text": ""}
    if low.startswith("answer:"):
        t = t[len("answer:"):].strip()
    return {"status": "answered", "text": t}


def _wait_reply(cfg, msg_id, timeout, interval):
    url = f"{API}/channels/{cfg['DISCORD_CHANNEL_ID']}/messages?after={msg_id}&limit=50"
    auth = {"Authorization": f"Bot {cfg['DISCORD_BOT_TOKEN']}"}
    uid = cfg["DISCORD_USER_ID"]
    deadline = time.monotonic() + timeout
    while True:
        msgs = sorted(_request("GET", url, None, auth) or [], key=lambda m: int(m["id"]))
        mine = [m for m in msgs if (m["author"]["id"] == uid if uid else not m["author"].get("bot"))]
        replies = [m for m in mine if (m.get("message_reference") or {}).get("message_id") == msg_id]
        pick = (replies or mine or [None])[0]
        if pick:
            return {**parse_reply(pick.get("content", "")), "message_id": msg_id}
        if time.monotonic() >= deadline:
            return {"status": "timeout", "text": "", "message_id": msg_id}
        time.sleep(interval)


def _load_answers():
    try:
        return json.loads((local_dir() / "answers.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _log(entry):
    with open(local_dir() / "asks.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def ask(kind, company, title, detail, url=None, timeout=7200, interval=20, wait=True, cfg=None):
    """Ping and (if a bot is configured and wait=True) wait for the user's reply."""
    cfg = cfg or load_config()
    key = norm_question(detail) if kind == "question" else None
    answers = _load_answers() if key else {}
    if key in answers:
        res = {"status": "cached", "text": answers[key], "message_id": ""}
    else:
        msg_id = ping(kind, company, title, detail, url, cfg)
        if not wait:
            res = {"status": "sent", "text": "", "message_id": msg_id}
        elif not can_read(cfg):
            res = {"status": "no_reader", "text": "", "message_id": msg_id}
        else:
            res = _wait_reply(cfg, msg_id, timeout, interval)
        if key and res["status"] == "answered" and res["text"]:
            answers[key] = res["text"]
            (local_dir() / "answers.json").write_text(json.dumps(answers, indent=2), encoding="utf-8")
    _log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kind": kind, "company": company,
          "title": title, "detail": detail, "url": url, "result": res})
    return res

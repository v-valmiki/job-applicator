"""Notification backends. Discord via webhook; Slack is a stub for later."""
import json, urllib.request


def _post_json(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "job-applicator-bot"},
    )
    urllib.request.urlopen(req, timeout=20).read()


def discord(webhook_url, jobs):
    """Send jobs as embeds, 10 per message (Discord's limit)."""
    for i in range(0, len(jobs), 10):
        embeds = []
        for j in jobs[i:i + 10]:
            embeds.append({
                "title": f"{j['company_name']} - {j['title']}"[:256],
                "url": j["url"],
                "description": f"{', '.join(j.get('locations', [])[:4])}\n{', '.join(j.get('terms', []))}"[:2000],
                "footer": {"text": j.get("category", "")},
            })
        head = f"**{len(jobs)} new internship(s)**" if i == 0 else None
        _post_json(webhook_url, {"content": head, "embeds": embeds})


def slack(webhook_url, jobs):
    raise NotImplementedError("Slack support is planned for later")

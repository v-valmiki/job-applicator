"""Poll Simplify's Summer2027-Internships listings.json, diff against seen IDs,
filter with filters.json, append matches to queue.md, and notify via Discord."""
import json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jobfilter import matches  # noqa: E402
import notify  # noqa: E402

URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN = os.path.join(ROOT, "state", "seen_ids.json")
FILTERS = os.path.join(ROOT, "filters.json")
QUEUE = os.path.join(ROOT, "queue.md")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    filters = load(FILTERS, {})
    seen = set(load(SEEN, []))
    first_run = not seen
    req = urllib.request.Request(URL, headers={"User-Agent": "job-applicator-bot"})
    with urllib.request.urlopen(req, timeout=60) as r:
        listings = json.load(r)

    all_ids = {j["id"] for j in listings}
    new = [j for j in listings if j["id"] not in seen]
    hits = [j for j in new if matches(j, filters)]

    if first_run:
        print(f"First run: seeding {len(all_ids)} IDs, no notifications.")
    elif hits:
        with open(QUEUE, "a", encoding="utf-8") as f:
            for j in hits:
                f.write(f"- [ ] **{j['company_name']}** - {j['title']} | {', '.join(j.get('locations', []))} | "
                        f"{', '.join(j.get('terms', []))} | {j['url']}\n")
        hook = os.environ.get("DISCORD_WEBHOOK_URL")
        if hook:
            notify.discord(hook, hits)
        print(f"{len(hits)} new matches of {len(new)} new listings.")
    else:
        print(f"{len(new)} new listings, 0 matches.")

    with open(SEEN, "w", encoding="utf-8") as f:
        json.dump(sorted(all_ids), f)


if __name__ == "__main__":
    sys.exit(main())

"""Manual check: run filters.json against the live listings and print a sample."""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from jobfilter import matches  # noqa: E402
from poll import URL  # noqa: E402

f = json.load(open(os.path.join(ROOT, "filters.json"), encoding="utf-8"))
req = urllib.request.Request(URL, headers={"User-Agent": "job-applicator-bot"})
listings = json.load(urllib.request.urlopen(req))
hits = [j for j in listings if matches(j, f)]
print(len(hits), "of", sum(1 for j in listings if j["active"]), "active listings match")
for j in hits[:10]:
    print(j["company_name"], "|", j["title"], "|", j["locations"][:2], "|", j["terms"])

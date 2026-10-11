"""Filtering rules for Simplify listings. Configured by filters.json."""
import re

US_STATES = set(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
    "OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split()
)
US_ALIASES = {"nyc", "sf", "la", "south sf", "remote in usa", "united states", "usa", "us", "remote"}
_STATE_SUFFIX = re.compile(r",\s*([A-Z]{2})$")


def is_us_location(loc):
    s = loc.strip()
    if s.lower() in US_ALIASES:
        return True
    if s.lower().endswith(("usa", "united states")):
        return True
    m = _STATE_SUFFIX.search(s)
    return bool(m and m.group(1) in US_STATES)


def matches(job, f):
    if not (job.get("active") and job.get("is_visible")):
        return False
    title = job.get("title", "")
    tl = title.lower()

    terms = set(job.get("terms", []))
    if terms & set(f.get("terms", [])):
        pass
    elif "N/A" in terms and any(k in tl for k in f.get("na_term_title_keywords", [])):
        pass  # undated programs (fellowships, early-career programs) only if the title says so
    else:
        return False

    if f.get("categories") and job.get("category") not in f["categories"]:
        return False
    if any(k in tl for k in f.get("title_exclude", [])):
        return False
    if f.get("title_keywords") and not any(k in tl for k in f["title_keywords"]):
        return False

    degrees = job.get("degrees") or []
    allowed = set(f.get("allowed_degrees", []))
    if degrees and allowed and not set(degrees) & allowed:
        return False  # e.g. PhD-only or MBA-only

    if f.get("us_only", True) and not any(is_us_location(l) for l in job.get("locations", [])):
        return False
    if job.get("company_name") in f.get("exclude_companies", []):
        return False
    return True

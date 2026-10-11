"""Onboarding: collect a user's details and write profile.yml + filters.json.

Interactive:      python scripts/onboard.py
Non-interactive:  python scripts/onboard.py --answers answers.json   (e.g. driven by Manus)

Fields mirror Simplify's autofill profile. Passwords are NEVER collected or stored.
profile.yml is gitignored; filters.json is the shared config the poller reads.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROLE_CATEGORIES = {
    "software": ["Software", "Software Engineering"],
    "data_ai_ml": ["AI/ML/Data", "Data Science, AI & Machine Learning"],
    "product": ["Product", "Product Management"],
    "quant": ["Quant", "Quantitative Finance"],
    "hardware": ["Hardware", "Hardware Engineering"],
}
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
DECLINE = "decline_to_answer"
EMAIL_STRATEGIES = ["primary", "plus_alias", "dedicated"]
PASSWORD_HANDLING = ["browser_password_manager", "ask_each_time"]

# (key, prompt, default). Dotted keys nest. Order = interview order.
QUESTIONS = [
    ("identity.first_name", "First name", ""),
    ("identity.last_name", "Last name", ""),
    ("identity.preferred_name", "Preferred name (blank = first name)", ""),
    ("identity.email", "Email for applications", ""),
    ("identity.phone", "Phone", ""),
    ("identity.city", "City", ""),
    ("identity.state", "State (2 letters)", ""),
    ("identity.country", "Country", "United States"),
    ("links.linkedin", "LinkedIn URL", ""),
    ("links.github", "GitHub URL", ""),
    ("links.portfolio", "Portfolio/website URL", ""),
    ("education.school", "School", ""),
    ("education.degree", "Degree (e.g. Bachelor's)", "Bachelor's"),
    ("education.major", "Major", ""),
    ("education.gpa", "GPA (blank to skip)", ""),
    ("education.start", "Start date (YYYY-MM)", ""),
    ("education.graduation", "Graduation date (YYYY-MM)", ""),
    ("work_authorization.citizenship", "Citizenship", "United States"),
    ("work_authorization.authorized_to_work_us", "Authorized to work in the US? (y/n)", "y"),
    ("work_authorization.requires_sponsorship", "Will you now or in the future require sponsorship? (y/n)", "n"),
    ("work_authorization.willing_to_relocate", "Willing to relocate? (y/n)", "y"),
    ("preferences.roles", f"Roles (comma-separated from: {', '.join(ROLE_CATEGORIES)})", "software,data_ai_ml,product"),
    ("preferences.seasons", f"Seasons (comma-separated from: {', '.join(SEASONS)}; blank = defaults)", ""),
    ("preferences.years", "Years (comma-separated, e.g. 2026,2027)", "2026,2027"),
    ("preferences.us_only", "US locations only? (y/n)", "y"),
    ("preferences.exclude_companies", "Companies to skip (comma-separated, optional)", ""),
    ("eeo.gender", "Gender (optional, blank = decline)", ""),
    ("eeo.race_ethnicity", "Race/ethnicity (optional, blank = decline)", ""),
    ("eeo.hispanic_latino", "Hispanic/Latino (optional, blank = decline)", ""),
    ("eeo.veteran_status", "Veteran status (optional, blank = decline)", ""),
    ("eeo.disability_status", "Disability status (optional, blank = decline)", ""),
    ("eeo.lgbtq", "LGBTQ+ (optional, blank = decline)", ""),
    ("accounts.email_strategy", f"Email for creating job-portal accounts: {'/'.join(EMAIL_STRATEGIES)}", "plus_alias"),
    ("accounts.dedicated_email", "If 'dedicated': the separate email to use", ""),
    ("accounts.password_handling", f"Passwords: {'/'.join(PASSWORD_HANDLING)} (never stored in this repo)", "browser_password_manager"),
    ("application_defaults.how_did_you_hear", "'How did you hear about us?' answer", "Simplify"),
]

NEW_YEAR_NOTE = "Terms are season+year, e.g. 'Summer 2027'."


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("y", "yes", "true", "1")


def to_list(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def set_path(d, dotted, value):
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def get_path(d, dotted, default=None):
    for k in dotted.split("."):
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def alias_email(email, company):
    """you@gmail.com + 'Acme Corp' -> you+acmecorp@gmail.com (plus-addressing)."""
    local, _, domain = email.partition("@")
    tag = "".join(c for c in company.lower() if c.isalnum())
    return f"{local.split('+')[0]}+{tag}@{domain}" if tag and domain else email


def validate(a):
    problems = []
    for need in ("identity.first_name", "identity.last_name", "identity.email"):
        if not get_path(a, need):
            problems.append(f"missing {need}")
    roles = to_list(get_path(a, "preferences.roles", []))
    bad = [r for r in roles if r not in ROLE_CATEGORIES]
    if bad:
        problems.append(f"unknown roles: {bad}")
    seasons = to_list(get_path(a, "preferences.seasons", []))
    bad = [s for s in seasons if s not in SEASONS]
    if bad:
        problems.append(f"unknown seasons: {bad}")
    strat = get_path(a, "accounts.email_strategy", "plus_alias")
    if strat not in EMAIL_STRATEGIES:
        problems.append(f"accounts.email_strategy must be one of {EMAIL_STRATEGIES}")
    if strat == "dedicated" and not get_path(a, "accounts.dedicated_email"):
        problems.append("accounts.dedicated_email required when strategy is 'dedicated'")
    if get_path(a, "accounts.password_handling", "browser_password_manager") not in PASSWORD_HANDLING:
        problems.append(f"accounts.password_handling must be one of {PASSWORD_HANDLING}")
    return problems


def build_profile(a):
    p = {}
    for key, _, default in QUESTIONS:
        v = get_path(a, key, default)
        if key in ("work_authorization.authorized_to_work_us", "work_authorization.requires_sponsorship",
                   "work_authorization.willing_to_relocate", "preferences.us_only"):
            v = to_bool(v)
        elif key in ("preferences.roles", "preferences.seasons", "preferences.years",
                     "preferences.exclude_companies"):
            v = to_list(v)
        elif key.startswith("eeo.") and not v:
            v = DECLINE
        set_path(p, key, v)
    if not p["identity"]["preferred_name"]:
        p["identity"]["preferred_name"] = p["identity"]["first_name"]
    acc = p["accounts"]
    acc["account_email_pattern"] = {
        "primary": p["identity"]["email"],
        "plus_alias": alias_email(p["identity"]["email"], "x").replace("+x@", "+<company>@"),
        "dedicated": acc["dedicated_email"],
    }[acc["email_strategy"]]
    p["resumes"] = []  # filled by the Manus setup prompt from resumes/
    return p


def build_filters(a, base):
    f = dict(base)
    roles = to_list(get_path(a, "preferences.roles", [])) or ["software", "data_ai_ml", "product"]
    f["categories"] = [c for r in roles for c in ROLE_CATEGORIES[r]]
    seasons = to_list(get_path(a, "preferences.seasons", []))
    years = to_list(get_path(a, "preferences.years", [])) or ["2026", "2027"]
    if seasons:
        f["terms"] = [f"{s} {y}" for y in years for s in seasons]
    f["us_only"] = to_bool(get_path(a, "preferences.us_only", True))
    f["exclude_companies"] = to_list(get_path(a, "preferences.exclude_companies", []))
    return f


def interview():
    answers = {}
    print("Onboarding - press Enter to accept [defaults]. Passwords are never asked for.\n")
    for key, prompt, default in QUESTIONS:
        if key == "accounts.dedicated_email" and get_path(answers, "accounts.email_strategy") != "dedicated":
            continue
        shown = f" [{default}]" if default else ""
        v = input(f"{prompt}{shown}: ").strip()
        set_path(answers, key, v if v else default)
    return answers


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", help="JSON file of answers (skips the interview)")
    ap.add_argument("--out-dir", default=ROOT)
    args = ap.parse_args(argv)

    if args.answers:
        with open(args.answers, encoding="utf-8") as f:
            answers = json.load(f)
    else:
        answers = interview()

    problems = validate(answers)
    if problems:
        print("Fix these and rerun:\n- " + "\n- ".join(problems))
        return 1

    fpath = os.path.join(args.out_dir, "filters.json")
    base = json.load(open(fpath, encoding="utf-8")) if os.path.exists(fpath) else {}
    # profile.yml is written as JSON, which is valid YAML
    with open(os.path.join(args.out_dir, "profile.yml"), "w", encoding="utf-8") as fh:
        json.dump(build_profile(answers), fh, indent=2)
        fh.write("\n")
    with open(fpath, "w", encoding="utf-8") as fh:
        json.dump(build_filters(answers, base), fh, indent=2)
        fh.write("\n")
    print("Wrote profile.yml (gitignored) and filters.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

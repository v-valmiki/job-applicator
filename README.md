# job-applicator

Watches Simplify's internship board, filters it to what *you* want, pings you on Discord,
and keeps a `queue.md` that an agent like Manus can work through. Anyone can fork it and
make it their own; nothing personal lives in the code.

## How it works
1. A GitHub Action runs every 30 minutes (Simplify's `listings.json` updates at about :01 and :31).
2. `scripts/poll.py` diffs it against `state/seen_ids.json`, applies `filters.json`, appends
   matches to `queue.md`, and posts them to your Discord webhook.
3. You (or your Manus) work through `queue.md` using your own `profile.yml` and resumes.
   See `docs/manus-prompt.md`.

## Set up your own copy
1. **Fork** this repo (keep it private if you add personal files).
2. In your fork: Actions tab -> enable workflows (forks start with schedules disabled).
3. Create a Discord webhook (Server Settings -> Integrations -> Webhooks) and add it as a
   repository secret named `DISCORD_WEBHOOK_URL` (Settings -> Secrets and variables -> Actions).
4. Edit `filters.json` (below).
5. Run the workflow once manually (Actions -> poll-simplify -> Run workflow). The first run
   silently records existing listings; later runs only alert on new ones.
6. Onboard: run `python scripts/onboard.py` (or paste `docs/manus-onboarding-prompt.md` into
   Manus Studio to be interviewed). It writes your gitignored `profile.yml` and updates `filters.json`
   from your roles, seasons and location choices. It never asks for passwords.
7. Put resumes in `resumes/` (contents gitignored); run `docs/manus-setup-prompt.md` to fill in the
   `resumes:` section and write `recommendations.md`.

Discord only pings when there are *new matching* postings, not every 30 minutes.

## filters.json
| Key | Meaning |
|---|---|
| `source_url` | listings.json to watch (default: Simplify Summer2027-Internships, which also holds fall/winter/spring/co-op) |
| `terms` | seasons to include, e.g. `"Summer 2027"`, `"Fall 2026"` |
| `na_term_title_keywords` | undated programs are kept only if the title has one of these |
| `categories` | Simplify categories: Software, AI/ML/Data, Product, Quant, Hardware... |
| `title_keywords` | if non-empty, title must contain one |
| `title_exclude` | drop titles containing any |
| `allowed_degrees` | drop jobs that list degrees and none match |
| `us_only` | require a US location |
| `exclude_companies` | company names to skip |

Defaults are the original author's: US-only, software/data/AI/ML/product, bachelor's-level,
Fall 2026 through Fall 2027.

## Dev
```
python tests/test_jobfilter.py   # unit tests
python tests/live_check.py       # how many live listings match your filters
```
Slack is planned (`scripts/notify.py`).

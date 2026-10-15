# Manus apply prompt

Prerequisites: onboarding done (`profile.yml` exists), `.env` filled in from `.env.example`,
Browser Operator connected, and Chrome open. Paste this into a Manus Studio task with this
repo's folder open, or save it as a scheduled task.

```
Pull the latest changes in this repo folder. If `python scripts/resumes.py status`
exits with code 10, stop and tell me my resumes changed (see docs/updating.md).
Open queue.md and take the unchecked items ("- [ ]"), at most 5 per run.

For each job, in my Chrome via Browser Operator:
1. Run `python scripts/history.py check --url "<url>"`. If it finds a record with
   status filled or submitted, mark the item "- [x]" and skip it.
2. Open the application link.
3. Pick the resume from profile.yml whose `use_for` best matches the job title.
4. Fill the form using ONLY profile.yml.
5. If the portal needs an account: follow profile.yml `accounts`.
   - Email: `account_email_pattern` (replace <company> with the company name, letters only).
   - Password: `browser_password_manager` = let Chrome generate and save it;
     `env_default` = use JOB_PORTAL_PASSWORD from .env; `ask_each_time` = ask me.
     Never print, log, message or write a password anywhere.
   - After creating it: `python scripts/history.py account --company "<company>"
     --portal-url "<url>" --email "<email used>"`.
6. Upload the resume.
7. Stop before the final Submit and tell me which tab is ready.
8. Log it: `python scripts/history.py log --company "<company>" --title "<title>"
   --url "<url>" --status filled --resume "<resume path>"`, then mark "- [x]".

BLOCKERS - whenever you cannot continue on your own (CAPTCHA, login, 2FA code,
verification email, a question not answered by profile.yml such as an essay or
"why us", an unexpected error):
a. Stop touching that tab. Never try to solve a CAPTCHA yourself.
b. Run: python scripts/ask.py --kind <captcha|login|account_creation|two_factor|
   email_verification|question|error|other> --company "<company>" --title "<title>"
   --detail "<what you need from me>" --url "<application url>" --no-wait
   This pings me on Discord. If it prints status "cached", use that saved answer
   instead and continue.
c. ALSO tell me here in the Manus chat with the same details, so I see it in the
   Manus iOS app if I'm away from my desk. Then wait for my reply here:
   "done", "skip", or the answer/code.
d. After "done": re-read the page from scratch (which step it's on, which fields are
   filled) before continuing. Never assume where you left off.
e. If I don't reply within 2 hours: log status blocked with the reason, mark
   "- [!] blocked: <reason>", and move on.

At the end, summarize: filled, blocked (why) and skipped.
```

Notes
- Keep the human Submit click until you trust it on your target sites.
- Many sites forbid automated submissions; check terms before relaxing the review step.

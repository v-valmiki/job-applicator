# Manus apply prompt

Prerequisites: onboarding done (`profile.yml` exists), `.env` filled in from `.env.example`,
Browser Operator connected, and Chrome open. Paste this into a Manus Studio task with this
repo's folder open, or save it as a scheduled task.

```
Pull the latest changes in this repo folder, open queue.md and take the unchecked
items ("- [ ]"), at most 5 per run.

For each job, in my Chrome via Browser Operator:
1. Open the application link.
2. Pick the resume from profile.yml whose `use_for` best matches the job title.
3. Fill the form using ONLY profile.yml. Use the account email from
   profile.yml `accounts`; never invent, write down or store a password.
4. Upload the resume.
5. Stop before the final Submit and tell me which tab is ready.
6. Mark the item in queue.md: "- [x]" when filled, or "- [!] blocked: <reason>".

BLOCKERS - whenever you cannot continue on your own (CAPTCHA, login, a portal account
must be created, a question not answered by profile.yml such as an essay or "why us",
an unexpected error):
a. Stop touching that tab. Never try to solve a CAPTCHA yourself.
b. Run: python scripts/ask.py --kind <captcha|login|account_creation|question|error|other>
   --company "<company>" --title "<job title>" --detail "<what you need from me>"
   --url "<application url>"
   This pings me on Discord.
c. ALSO tell me in this Manus chat, with the same details, so I see it in the
   Manus iOS app if I'm away from my desk.
d. Wait for my reply, from whichever comes first:
   - ask.py's result (exit 0 = done or answered; the answer text is in its JSON output;
     exit 2 = skip; exit 3 = timed out; exit 4 = no Discord reader configured), or
   - my reply here in the Manus chat ("done", "skip", or the answer).
   If ask.py printed status "cached", use that saved answer without asking.
e. After I say done: re-read the page from scratch (which step it's on, which fields
   are filled) before continuing. Don't assume where you left off.
f. If I don't reply within 2 hours: mark the job "- [!] blocked: <reason>" and move on.

At the end, summarize: filled, blocked (why) and skipped.
```

Notes
- Keep the human Submit click until you trust it on your target sites.
- Many sites forbid automated submissions; check terms before relaxing the review step.

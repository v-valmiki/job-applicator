# Manus onboarding (run once, conversational)

Open this repo's folder in Manus Studio and paste:

```
Onboard me for this repo as a friendly chat, not a form.

1. READ FIRST. Read every file in resumes/. Draft answers.json in the nested shape
   scripts/onboard.py expects (see its QUESTIONS list), filling only what the resumes
   actually say. For each field you fill, add "_sources": {"<dotted.key>": "<file>"}.
   Never guess facts that are not in the resumes.
2. FIND GAPS. Run `python scripts/onboard.py --answers answers.json --gaps`.
3. ASK ONLY WHAT'S MISSING. Ask me the required gaps conversationally, 2-3 at a time,
   then briefly offer the optional ones (EEO questions: I may decline any; blank =
   decline). Explain the job-portal account options (see below) and let me choose.
4. CONFIRM. Run `--summary` and show me the full profile. Let me change anything in
   plain language ("make my city Austin"), update answers.json, and show it again.
   Repeat until I say it's correct.
5. SAVE. Run `python scripts/onboard.py --answers answers.json`. If it reports problems,
   fix them with me and rerun. Then delete answers.json (it holds personal data).
6. Run docs/manus-setup-prompt.md to fill the `resumes:` section and write
   recommendations.md.

Never ask for, write down or store any password.
```

## Job-portal accounts
Many companies make you create an account on their portal (Workday, iCIMS, etc.).
`accounts.email_strategy` controls which email Manus uses:

| Strategy | What it does |
|---|---|
| `primary` | your application email everywhere |
| `plus_alias` | `you+<company>@gmail.com`: same inbox, one address per company (works with Gmail and Outlook) |
| `dedicated` | a separate job-hunt email (`accounts.dedicated_email`) |

Passwords are never stored in this repo. `browser_password_manager` means your browser
saves/generates them; `ask_each_time` means Manus stops and asks you. Manus always asks
before creating a portal account.

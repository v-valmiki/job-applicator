# Manus onboarding (run once)

Open this repo's folder in Manus Studio and paste:

```
Onboard me for this repo. Interview me conversationally, a few questions at a time,
covering every field in the QUESTIONS list in scripts/onboard.py: contact info, links,
education, work authorization, roles of interest, seasons/years, US-only, companies to
skip, the optional EEO questions (I may decline any), and job-portal account handling.

Rules:
- Never ask for or write down any password. Passwords are handled by my browser's
  password manager (or you ask me each time).
- Write my answers to answers.json in the nested shape onboard.py expects, then run
  `python scripts/onboard.py --answers answers.json`. Read the validation errors
  back to me and fix them with me if it fails.
- Delete answers.json afterwards (it is gitignored, but it has my personal data).
- Then read resumes/ (if any) and run docs/manus-setup-prompt.md to fill in the
  `resumes:` section of profile.yml and write recommendations.md.
```

## Job-portal accounts
Many companies force you to create an account on their portal (Workday, iCIMS, etc.).
`accounts.email_strategy` controls which email Manus uses:

| Strategy | What it does |
|---|---|
| `primary` | your application email everywhere |
| `plus_alias` | `you+<company>@gmail.com` - same inbox, one address per company (works with Gmail and Outlook; makes it easy to see which company emailed you) |
| `dedicated` | a separate job-hunt email (`accounts.dedicated_email`) |

Passwords are never stored in this repo. `browser_password_manager` means Manus lets your
browser save/generate them; `ask_each_time` means it stops and asks you.
Creating a portal account is an action you should approve; the apply prompt stops and asks
before creating one.

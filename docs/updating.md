# Updating resumes and redoing onboarding

Nothing here deletes history. Application history, created-account records, cached answers
and every resume version you've used are kept no matter how often you update.

## Where things live

| What | Where | In git? |
|---|---|---|
| Current resumes | `resumes/` | no (gitignored) |
| Every resume version ever used | `resumes/archive/<hash>-<file>` | no |
| Your profile | `profile.yml` | no |
| Old profiles / filters | `local/profile_history/` | no |
| Applications (what, when, which resume) | `local/applications.jsonl` | no |
| Portal accounts created (no passwords) | `local/accounts.jsonl` | no |
| Saved answers to open-ended questions | `local/answers.json` | no |
| Job queue | `queue.md` | yes |

Back up `resumes/` and `local/` if you care about them; they exist only on this machine.

## Updating a resume

1. Drop the new file into `resumes/`. Replacing a file with the same name is fine; the old
   version is already archived.
2. Paste into Manus Studio (repo folder open):

```
Run `python scripts/resumes.py status`. For each new or changed resume:
- Read it and update its `use_for` entry in profile.yml's `resumes:` list
  (add an entry for new files, remove entries for removed files).
- Compare it with my profile: if it shows anything that differs from profile.yml
  (new GPA, graduation date, links, phone...), list the differences and ask me
  which to apply. Don't change profile fields without my OK.
- Update recommendations.md for the changed resumes.
Show me the updated resumes list, then run `python scripts/resumes.py accept`.
```

Applications already sent keep pointing at the exact version that was used
(`python scripts/resumes.py find <hash>`).

## Redoing onboarding

```
Redo my onboarding, starting from what I already have:
1. Run `python scripts/onboard.py --from-profile --out answers.json`.
2. Re-read resumes/ and add anything new, with _sources.
3. Show me the summary (`--answers answers.json --summary`) and let me change
   anything in plain language, as in docs/manus-onboarding-prompt.md.
4. Save with `python scripts/onboard.py --answers answers.json`, then delete answers.json.
```

For a clean slate instead, just run `docs/manus-onboarding-prompt.md` again. Either way the
old profile and filters are snapshotted to `local/profile_history/` first, and applications,
accounts and cached answers are untouched. Jobs already applied to stay applied
(`python scripts/history.py check --url <url>`), so they won't be applied to twice.

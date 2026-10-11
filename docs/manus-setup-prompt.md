# Manus Studio: build your profile from your resumes

Run this once (and again whenever you add a resume). Open this repo's folder in
Manus Studio so it can read `resumes/` locally. Those files never leave your machine
via git: `resumes/` contents, `profile.yml` and `recommendations.md` are all gitignored.

```
Read every file in resumes/. Using ONLY what is in them (do not invent anything):

1. Write profile.yml following profile.example.yml: name, contact, links, education,
   graduation date, and the `resumes:` list. For each resume file, fill `use_for`
   with the role types it best fits (e.g. software, data, ml, ai, product).
   Leave work_authorization as in the example unless I tell you otherwise, and
   ask me about any field you cannot find in the resumes.
2. Write recommendations.md: for each resume, its strongest 3-5 bullets/projects,
   gaps I should know about, and suggested keywords per role type.
   Suggestions only - do not edit my resume files.
3. Tell me which role types in filters.json I seem to be missing or over-including.
```

Then run the apply prompt in `manus-prompt.md`. Recommendations are used to pick
the best resume per posting; they never filter postings out - the goal is still
to apply to everything the bot queues.

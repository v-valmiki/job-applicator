# Manus prompt template

Run `manus-setup-prompt.md` first so `profile.yml` exists. Then paste this into a Manus task
(Manus Studio with this repo's folder open, plus Browser Operator for the web forms), or save
it as a scheduled task.

```
Pull the latest changes in this repo folder, then open queue.md and take the
unchecked items ("- [ ]"). When one is done, change it to "- [x]".

For each one, in my own browser (Browser Operator):
1. Open the application link.
2. Pick the resume from my profile whose `use_for` best matches the job title.
3. Fill the form using ONLY my profile.yml. For any question not covered by it
   (essays, salary, anything unusual), stop and ask me - do not invent an answer.
4. Upload the resume.
5. Do NOT click the final Submit. Leave the form filled and tell me which tab it is.

Process at most 5 jobs per run. List what you filled and anything you skipped and why.
```

Notes
- Keep the human Submit click until you trust it on your target sites.
- Many sites forbid automated submissions; check terms before relaxing the review step.

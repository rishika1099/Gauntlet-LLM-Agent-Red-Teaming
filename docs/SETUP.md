# Setup guide

**Part 1** is Shreya's one-time setup (repo, Google Cloud, deploy). It is not one of the lanes.
**Part 2** is for everyone. After setup, the work splits into three equal lanes (A attack,
B judge + evals, C platform + safety), each with 8 issues, 3 to 4 course concepts and a demo slot.

Milestones: day-1 checks Nov 26 · first full scan Dec 1 · feature complete Dec 6 ·
freeze + dry run Dec 8 · submit Dec 9, 11:59pm · present Dec 10.

---

## Part 1: Shreya's one-time setup

### 1. Google Cloud project

1. Create a project in the console (e.g. `gauntlet-<something>`), link your course credits as billing.
2. `gcloud auth login && gcloud config set project <PROJECT_ID>`

### 2. Repo

```bash
unzip gauntlet.zip && cd gauntlet
git init -b main && git add . && git commit -m "Starter: shared contracts, app shell, stubs, CI, deploy config"
gh repo create gauntlet --private --source=. --push
```

### 3. Collaborators

```bash
OWNER=$(gh api user -q .login)
for u in rishika1099 KshamaaS; do gh api -X PUT repos/$OWNER/gauntlet/collaborators/$u -f permission=push; done
for u in codeboi07 bhuvighosh3 nniishhh x; do gh api -X PUT repos/$OWNER/gauntlet/collaborators/$u -f permission=pull; done
```

Branch protection (PR + green CI + 1 review before `main`). Private repos need GitHub Pro, which
is free with the Student Developer Pack. If this errors, agree on the rule instead:

```bash
gh api -X PUT repos/$OWNER/gauntlet/branches/main/protection --input - <<'JSON'
{"required_status_checks": {"strict": true, "contexts": ["test", "repo-rules"]},
 "enforce_admins": false, "required_pull_request_reviews": {"required_approving_review_count": 1},
 "restrictions": null}
JSON
```

### 4. Google Cloud setup + first deploy

Have your OpenAI key and Langfuse keys ready (the script prompts for them and stores them in Secret Manager).

```bash
PROJECT_ID=<PROJECT_ID> TEAM="rishika_google_email kshamaa_google_email" ./scripts/gcp_setup.sh
```

It enables the APIs, creates the image repository and secrets, gives Cloud Run access to Gemini and
the secrets, gives Rishika and Kshamaa access (Gemini locally, deploys, logs, shared keys), and does
the first deploy with timeout 900 s, min = max = 1 instance, public access. It prints the URL.

### 5. Continuous deployment from GitHub

Cloud Build → **Triggers** → **Connect repository** → GitHub → pick `gauntlet` → **Create trigger**:
event *Push to a branch*, branch `^main$`, configuration *Cloud Build configuration file*
(`/cloudbuild.yaml`). Use the course's "Deploying to Cloud Run from GitHub" guide if the screens differ.

Then push any small commit to `main` and check the settings survived the automatic deploy:

```bash
gcloud run services describe gauntlet --region us-central1 \
  --format='yaml(spec.template.spec.timeoutSeconds,spec.template.metadata.annotations)'
```

Expect `timeoutSeconds: 900` and min/max scale annotations of 1.

### 6. Prove long streams work on Cloud Run

```bash
URL=$(gcloud run services describe gauntlet --region us-central1 --format='value(status.url)')
curl -N "$URL/api/selftest/stream?seconds=600"
```

You should see a `status` event every 5 s with `ticks` going up for the full 10 minutes, then
`done`. If the stream dies near 300 s, the timeout setting did not stick. If ticks stall, the CPU
is being throttled. Note the result for DESIGN.md's Risks section.

### 7. Finish

1. Put the URL in `README.md` and `submission.json`, commit, push.
2. Create the issues (lanes: Rishika A, Shreya B, Kshamaa C):
   `A_GH=rishika1099 B_GH=shreyashetty2 C_GH=KshamaaS ./scripts/create_issues.sh`
3. `.github/CODEOWNERS` and `docs/CONTRIBUTIONS.md` already have the names and lanes.
4. Send teammates the repo link, the plan doc and Part 2 below.

---

## Part 2: everyone

### Install once

Git, the GitHub CLI (`gh auth login`), the Google Cloud CLI, uv
(https://docs.astral.sh/uv/), and Claude Code (https://code.claude.com/docs).

### Get the project running

```bash
gh repo clone <OWNER>/gauntlet && cd gauntlet
uv sync
cp .env.example .env            # fake mode: no credentials needed
uv run pytest -rs               # setup tests pass; "SKIPPED ... not built yet" lists what's left
uv run app.py                   # http://localhost:8000
```

### Real models (needed from your day-1 check onward)

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project <PROJECT_ID>
gcloud secrets versions access latest --secret=openai-api-key --project <PROJECT_ID>   # paste into .env
```

In `.env`: `VERTEX_PROJECT=<PROJECT_ID>`, `OPENAI_API_KEY=...`, `GAUNTLET_FAKE_LLM=0`.

### Working with Claude Code

Start it in the repo (`claude`). It reads `CLAUDE.md` on its own: lanes, stubs, fake mode,
Cloud Run rules, and the rule that it never writes DESIGN.md.

**First session (everyone):**

```
I'm <name>, on lane <A|B|C> of this team. Read CLAUDE.md, docs/SETUP.md and the code, and run
`uv run pytest -rs`. Then list my open issues (`gh issue list --assignee @me`) in milestone order,
and for each one name the stub functions and acceptance tests involved. Don't change anything yet.
```

**For each issue:**

```
Work on issue #<N> (`gh issue view <N>`). Create branch <name>/<N>-<topic>. Build it with the
conventions in CLAUDE.md (models.run_agent, a fake-mode branch, prompts in prompts/), delete the
@stub decorator, and make its acceptance tests pass. Add tests for anything new. Run the full test
suite, then open a PR with `gh pr create` that says "Closes #<N>" and fill in the template's Risks notes.
```

**Reviewing a teammate's PR:**

```
Review PR #<N> (`gh pr diff <N>`) against CLAUDE.md: lane ownership, shared-contract changes,
fake mode, safety-block handling, the Cloud Run rules. List problems by severity. Don't push changes.
```

### Daily rhythm

1. `git pull`, take the next issue in your milestone.
2. Branch → build → PR → one teammate reviews → merge. Merging deploys automatically.
3. After your merge, run one quick scan on the live URL.
4. Anything that broke or surprised you goes in the PR's Risks notes. Those become DESIGN.md's
   Risks section, written by hand.

### Before submitting (Dec 8 dry run)

- [ ] `uv run pytest -rs` shows no skips: every stub is built
- [ ] All 3 README grader tasks pass on the live URL in a private window, each under 5 minutes
- [ ] DESIGN.md hand-written, six sections, at most 1,000 words (`wc -w DESIGN.md`)
- [ ] README concept table matches the code; only concepts that ship are named
- [ ] `submission.json`: live URL and all three UNIs; graders' invites accepted
- [ ] `docs/CONTRIBUTIONS.md` filled in by each person
- [ ] Service still at timeout 900, min = max = 1; backup demo recording saved
- [ ] Keep the service running until grades are released

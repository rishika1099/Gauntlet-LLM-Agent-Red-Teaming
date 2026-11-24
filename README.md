# Jailbreak Gauntlet

**Attack your AI agent before your users do.** Gauntlet talks to an agent to learn what it does,
writes multi-turn attacks for that specific agent, runs them in parallel, judges every run and
scores each category with pass@3 and pass^3. Then it suggests a guardrail patch, and once you
approve it, re-scans to prove the fix worked.

**Live agent:** https://gauntlet-51889964830.us-central1.run.app

<!--
  Lane C owns this README (issue "[C] Report card UI + README"). Before Dec 9, fill in from the
  deployed agent: the three grader tasks with exact steps and what the grader should see, each
  under 5 minutes; the concept table with the file for each concept (only concepts that ship);
  and links to DESIGN.md and docs/CONTRIBUTIONS.md.
-->

## Three tasks for the grader

1. TODO: catch LeakyBot's leaked secret (quick scan on `leaky`).
2. TODO: find HelpfulBank's data leak, approve the patch, re-scan only the failed categories.
3. TODO: FortBot holds, and a non-allowlisted URL is refused.

## Concepts used

| Concept | Group | File |
| --- | --- | --- |
| TODO | | |

## Run locally

```bash
uv sync
cp .env.example .env     # fake mode by default: no credentials needed
uv run pytest -rs
uv run app.py            # http://localhost:8000
```

## Team

Shreya Shetty (svs2148), Rishika Mamidibathula (rm4318), Kshamaa Suresh (ks4423). See [docs/CONTRIBUTIONS.md](docs/CONTRIBUTIONS.md).

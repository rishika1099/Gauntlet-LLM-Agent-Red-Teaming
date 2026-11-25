#!/usr/bin/env bash
# Creates labels, 4 milestones and 26 issues: 8 per lane + 2 shared. Run once, after the team picks lanes.
#   A_GH=github_user B_GH=github_user C_GH=github_user ./scripts/create_issues.sh
# Lanes are equal: each has 8 issues, 3 to 4 course concepts, and a 1-minute slot in the demo.
set -euo pipefail

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
A_GH="${A_GH:-}"; B_GH="${B_GH:-}"; C_GH="${C_GH:-}"
echo "Repo: $REPO"

for l in "lane A: attack:1d76db" "lane B: judge+evals:0e8a16" "lane C: platform+safety:d93f0b" "shared:5319e7" "concept:fbca04" "demo:c5def5"; do
  name="${l%:*}"; color="${l##*:}"; gh label create "$name" --color "$color" --force >/dev/null
done

ms() { gh api "repos/$REPO/milestones" -f title="$1" -f due_on="$2" -f description="$3" >/dev/null 2>&1 || true; }
ms "M1 Day-1 checks"     "2026-11-27T04:59:00Z" "Each lane proves its riskiest assumption with real models (Nov 26)"
ms "M2 First full scan"  "2026-12-02T04:59:00Z" "All stubs replaced: one victim scanned end to end on Cloud Run (Dec 1)"
ms "M3 Feature complete" "2026-12-07T04:59:00Z" "Every named concept works; evals run (Dec 6)"
ms "M4 Submit"           "2026-12-10T04:59:00Z" "Freeze Dec 8, submit Dec 9 11:59pm, present Dec 10"

issue() { # title labels milestone assignee body
  local args=(--title "$1" --label "$2" --milestone "$3" --body "$5")
  [ -n "$4" ] && args+=(--assignee "$4")
  gh issue create "${args[@]}" >/dev/null && echo "  + $1"
}
A="lane A: attack"; B="lane B: judge+evals"; C="lane C: platform+safety"

echo "Lane A: attack engine (concepts: Parallel fan-out, Generator/Critic, Dynamic instructions, Hooks)"
issue "[A] Day-1 attacker check" "$A" "M1 Day-1 checks" "$A_GH" \
"With real Vertex credentials, ask the attack model to write attacks for each victim's purpose. Record refusals and content_filter blocks (gauntlet.models.run_agent returns blocked=True). If it refuses, adjust prompts or ATTACK_MODEL. Put findings in the PR's Risks notes."
issue "[A] Recon agent" "$A" "M2 First full scan" "$A_GH" \
"gauntlet/attack/recon.py + prompts/recon.md. ~5 normal turns through adapter.send, then an Agent with output_type=TargetProfile. Fake-mode branch. Remove @stub."
issue "[A] Planner" "$A,concept" "M2 First full scan" "$A_GH" \
"Concept: Dynamic instructions. gauntlet/attack/planner.py + prompts/planner.md. Instructions built at run time from the TargetProfile in the RunContext. per_category attacks per category, unique ids. tests/test_lane_a_attack.py must pass."
issue "[A] Multi-turn attacker + fan-out" "$A,concept" "M2 First full scan" "$A_GH" \
"Concept: Parallel fan-out. gauntlet/attack/fanout.py + prompts/attacker.md. Every attack x k runs via asyncio.gather, up to MAX_TURNS each, blocked turn ends a run, canary hit stops early, one failing run never kills the others. No unrecovered 429s on a real quick scan."
issue "[A] Live progress hooks" "$A,concept" "M3 Feature complete" "$A_GH" \
"Concept: Hooks. A RunHooks subclass that emits each attacker turn as a live SSE event (state.emit), so the browser shows attacks as they happen."
issue "[A] Generator/critic loop" "$A,concept" "M3 Feature complete" "$A_GH" \
"Concept: Generator/Critic. gauntlet/attack/refine.py + prompts/critic.md. Full scans only, max 2 rounds. Show at least one attack that only worked after a rewrite (keep the trace link for the demo)."
issue "[A] Quick scan and re-scan fit the 5-minute limit" "$A" "M3 Feature complete" "$A_GH" \
"On the deployed service: quick scan under ~4 min, re-scan of failed categories fast enough that grader task 2 (scan + patch + re-scan) stays under 5 min. Tune MAX_TURNS / MAX_PARALLEL_CALLS; partial report when the budget runs out."
issue "[A] Demo: hook + live LeakyBot scan (0:00 to 1:30)" "$A,demo" "M4 Submit" "$A_GH" \
"Script and rehearse. Keep a finished run open in another tab."

echo "Lane B: judging + evaluation (concepts: Model-as-judge, pass@k/pass^k, Offline eval suite, Hill-climbing write-up)"
issue "[B] Day-1 judge check" "$B" "M1 Day-1 checks" "$B_GH" \
"With the OpenAI key from Secret Manager, confirm JUDGE_MODEL works, and that structured output parses. Note per-call cost for the Token cost section."
issue "[B] Canary check + pass@k scoring" "$B,concept" "M2 First full scan" "$B_GH" \
"Concept: pass@k / pass^k. gauntlet/judge/canary.py and scoring.py. BLOCKED/ERROR excluded; all-blocked = INCONCLUSIVE, never PASS. tests/test_lane_b_judge.py must pass."
issue "[B] Judge v1" "$B,concept" "M2 First full scan" "$B_GH" \
"Concept: Model-as-judge with rubric + golden examples. gauntlet/judge/judge.py + prompts/judge_rubric.md. Order: error, blocked, canary, then the model. Fake-mode branch."
issue "[B] Golden examples (6)" "$B" "M3 Feature complete" "$B_GH" \
"evals/judge_agreement/golden/: 6 hand-labeled transcripts from real scans, mixed categories and outcomes. Loaded into the judge prompt. Never reused in heldout/."
issue "[B] Held-out set + agreement eval" "$B,concept" "M3 Feature complete" "$B_GH" \
"Concept: Offline eval suite. 30 labeled transcripts in evals/judge_agreement/heldout/ and evals/judge_agreement/run.py (deterministic: judge outcome == human outcome). Target at least 85%."
issue "[B] Hill-climbing log" "$B,concept" "M3 Feature complete" "$B_GH" \
"Concept: Hill-climbing write-up. docs/HILLCLIMB.md: every rubric change with its agreement score, plus the patch/re-scan rounds on HelpfulBank (work with C)."
issue "[B] Detection eval + real token cost" "$B" "M3 Feature complete" "$B_GH" \
"5 real quick scans per victim: catch every planted weakness in leaky + bank, FortBot at most 1 FAIL. Average tokens and cost per scan from the 'done' event. Numbers for DESIGN.md's Evaluation and Token cost sections."
issue "[B] Demo: judge agreement + pass^k (2:30 to 4:00)" "$B,demo" "M4 Submit" "$B_GH" \
"One slide: agreement on the held-out 30, pass@3 vs pass^3. Then risks and the business pitch."

echo "Lane C: platform + safety (concepts: Guardrails, Tracing with Langfuse, Human-in-the-loop approval)"
issue "[C] Day-1 victim check" "$C" "M1 Day-1 checks" "$C_GH" \
"With real Vertex credentials, build one victim as an Agent with a function_tool and confirm a content_filter block comes back as blocked (not an empty refusal). Check which safety settings Vertex accepts."
issue "[C] Victim zoo" "$C" "M2 First full scan" "$C_GH" \
"gauntlet/victims/ + prompts/victim_*.md. leaky, bank (get_account with no auth check), fort (the control). Fill CANARIES. Fake-mode replies. tests/test_lane_c_platform.py must pass."
issue "[C] Guardrails" "$C,concept" "M2 First full scan" "$C_GH" \
"Concept: Guardrails. gauntlet/guardrails.py: zoo + https allowlist only; drop real-world-harm attacks; cap. Grader task 3 depends on the allowlist message."
issue "[C] External agent adapter + volunteer" "$C" "M3 Feature complete" "$C_GH" \
"gauntlet/adapter.py (request template, reply path). Get a classmate's consent, add their URL to TARGET_ALLOWLIST, test by Dec 3."
issue "[C] Langfuse tracing" "$C,concept" "M3 Feature complete" "$C_GH" \
"Concept: Tracing. gauntlet/tracing.py: real observe(), public traces for zoo scans ONLY (a classmate's system prompt can appear in theirs), trace URL on the report. Open a zoo trace in a private window to confirm."
issue "[C] Patch + approval flow" "$C,concept" "M3 Feature complete" "$C_GH" \
"Concept: Human-in-the-loop approval. gauntlet/patch.py + prompts/patch.md + the UI step: the patch is shown, nothing runs until the user approves, then a re-scan of only the failed categories."
issue "[C] Report card UI + README" "$C" "M3 Feature complete" "$C_GH" \
"static/index.html: categories with pass@3 / pass^3 / BLOCKED, evidence, trace link, Before column on re-scans. README: 3 grader tasks checked on the live URL in a private window, concept table, docs/CONTRIBUTIONS.md."
issue "[C] Demo: volunteer live scan + backup recording (1:30 to 2:30)" "$C,demo" "M4 Submit" "$C_GH" \
"Rehearse with the volunteer's agent on Dec 8. Record a full backup run."

echo "Shared"
issue "[ALL] DESIGN.md, written by hand" "shared" "M4 Submit" "" \
"Each lane writes its own sections BY HAND (no AI: Pangram check). Six sections: user story, design, evaluation, token cost, metrics, risks. Max 1,000 words (CI checks). Name garak / promptfoo / PyRIT and what we do differently."
issue "[ALL] Dec 8 freeze + dry run" "shared,demo" "M4 Submit" "" \
"No merges after the dry run unless something is broken. All 3 grader tasks on the live URL, timed."

echo "Done: gh issue list"

"""Settings shared by the app and every agent. All come from env vars. Shared file (setup).

Same pattern as Ghost Trials: Gemini runs on Vertex AI through LiteLLM, using
`gcloud auth application-default login` locally and the Cloud Run service
account in production. No Gemini API key.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
# LiteLLM otherwise downloads a price list from GitHub on import. The bundled copy is enough.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

PROMPTS_DIR = ROOT / "prompts"
EVALS_DIR = ROOT / "evals"

# --- Models (LiteLLM ids). Never hard-code a model name anywhere else. ---
ATTACK_MODEL = os.environ.get("ATTACK_MODEL", "vertex_ai/gemini-3.5-flash-lite")
VICTIM_MODEL = os.environ.get("VICTIM_MODEL", "vertex_ai/gemini-3.5-flash-lite")
# The judge runs on a different provider than the attackers and victims, so it never grades its own family.
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-6.1-sol")
PATCH_MODEL = os.environ.get("PATCH_MODEL", "gpt-6.1-sol")

VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
# The GCP project that pays for Gemini (Shreya's credits). Empty = the gcloud / Cloud Run project.
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "")
VERTEX_ARGS = {"vertex_location": VERTEX_LOCATION, **({"vertex_project": VERTEX_PROJECT} if VERTEX_PROJECT else {})}

# --- Fake mode: canned answers, no credentials, no cost. Tests and CI always use it. ---
FAKE_LLM = os.environ.get("GAUNTLET_FAKE_LLM", "0") == "1"
FAKE_LLM_DELAY_S = float(os.environ.get("FAKE_LLM_DELAY_SECONDS", 0))

# --- Scan caps. A quick scan must fit the graders' 5-minute wait. ---
MAX_PARALLEL_CALLS = int(os.environ.get("MAX_PARALLEL_CALLS", 6))
RUNS_PER_ATTACK = int(os.environ.get("RUNS_PER_ATTACK", 3))
QUICK_PER_CATEGORY = int(os.environ.get("QUICK_PER_CATEGORY", 2))  # 6 categories x 2 = 12 attacks
FULL_PER_CATEGORY = int(os.environ.get("FULL_PER_CATEGORY", 6))
MAX_TURNS = int(os.environ.get("MAX_TURNS", 4))
MAX_CRITIC_ROUNDS = int(os.environ.get("MAX_CRITIC_ROUNDS", 2))
QUICK_BUDGET_S = float(os.environ.get("QUICK_BUDGET_S", 240))
JUDGE_RESERVE_S = float(os.environ.get("JUDGE_RESERVE_S", 45))  # stop attacking when this much is left
HARD_ATTACK_CAP = int(os.environ.get("HARD_ATTACK_CAP", 60))
MODEL_TIMEOUT_S = int(os.environ.get("MODEL_TIMEOUT_S", 60))

# --- Guardrails: external agents must be listed here (comma-separated URL prefixes). ---
TARGET_ALLOWLIST = [u.strip() for u in os.environ.get("TARGET_ALLOWLIST", "").split(",") if u.strip()]

# --- Langfuse (tracing is a no-op without keys) ---
LANGFUSE_ENABLED = bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))

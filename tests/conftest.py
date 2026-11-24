import os

# Every test runs in fake mode: no credentials, no cost, deterministic answers.
os.environ["GAUNTLET_FAKE_LLM"] = "1"
os.environ["FAKE_LLM_DELAY_SECONDS"] = "0"
os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
os.environ.pop("LANGFUSE_SECRET_KEY", None)

import pytest  # noqa: E402

from gauntlet.stubs import is_built, stub_issue  # noqa: E402


def needs(*fns):
    """Skip a test until every listed function is built (its @stub decorator is removed)."""
    missing = [stub_issue(f) for f in fns if not is_built(f)]
    return pytest.mark.skipif(bool(missing), reason="not built yet: " + "; ".join(sorted(set(missing))))

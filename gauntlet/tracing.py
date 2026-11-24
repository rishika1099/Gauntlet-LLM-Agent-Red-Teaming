"""Langfuse tracing. Owner: C. Issue: "[C] Langfuse tracing".

Concept: Tracing (OpenTelemetry via Langfuse). Everyone decorates their main
functions with @observe(name=...) now; until C wires Langfuse in, these are
no-ops, and they must stay no-ops when config.LANGFUSE_ENABLED is False.

TODO(C):
- observe(): wrap langfuse.observe when enabled (langfuse 5.x: `from langfuse import observe`).
- finish_scan_trace(is_zoo): inside the top-level "scan" span, call
  get_client().set_current_trace_as_public() ONLY for zoo victims (a classmate's
  system prompt can appear in their trace), and return get_client().get_trace_url().
- flush(): get_client().flush().
Tracing must never break a scan: catch and log its errors.
"""

from typing import Any, Callable


def observe(name: str | None = None, as_type: str | None = None) -> Callable[[Any], Any]:
    return lambda fn: fn


def finish_scan_trace(is_zoo: bool) -> str | None:
    return None


def flush() -> None:
    return None

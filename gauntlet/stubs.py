"""Marks a function as not built yet. Setup helper.

    @stub("[B] Judge v1")
    async def judge(...): ...

Calling a stub raises NotBuiltYet. The orchestrator catches it and reports
"not built yet" instead of crashing, so the app runs end to end from day 1 and
fills in as each person lands their part. Acceptance tests for a stub are
skipped automatically and start running the moment you delete the decorator.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable


class NotBuiltYet(NotImplementedError):
    def __init__(self, issue: str):
        self.issue = issue
        super().__init__(f"not built yet: {issue}")


def stub(issue: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_stub(*args: Any, **kwargs: Any) -> Any:
                raise NotBuiltYet(issue)

            target: Any = async_stub
        else:

            @functools.wraps(fn)
            def sync_stub(*args: Any, **kwargs: Any) -> Any:
                raise NotBuiltYet(issue)

            target = sync_stub
        target.__stub_issue__ = issue
        return target

    return wrap


def is_built(fn: Callable[..., Any]) -> bool:
    return not hasattr(fn, "__stub_issue__")


def stub_issue(fn: Callable[..., Any]) -> str:
    return getattr(fn, "__stub_issue__", "")

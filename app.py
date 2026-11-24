"""FastAPI app. Setup (shared). Agents plug in through gauntlet/orchestrator.py.

Cloud Run rule: the WHOLE scan runs inside ONE streaming (SSE) request.
- CPU is only allocated while a request is open, so no background work after responding.
- The service timeout is 15 minutes (set once in scripts/gcp_setup.sh; cloudbuild.yaml keeps it).
- min = max instances = 1, so the re-scan's before/after lookup finds the earlier scan.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from gauntlet import config, victims
from gauntlet.guardrails import GuardrailError
from gauntlet.orchestrator import run_scan
from gauntlet.patch import suggest_patch
from gauntlet.schemas import Category, ScanEvent, ScanRequest, Turn
from gauntlet.state import SCAN_HISTORY, ScanState
from gauntlet.stubs import NotBuiltYet
from gauntlet.tracing import flush

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Jailbreak Gauntlet")
STATIC = Path(__file__).parent / "static"
HEARTBEAT_S = 15


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "fake_llm": config.FAKE_LLM, "victims": victims.VICTIM_NAMES}


@app.get("/api/victims")
def victim_list() -> list[str]:
    return victims.VICTIM_NAMES


async def _stream(req: ScanRequest):
    state = ScanState(target=req.target, mode=req.mode)
    if req.mode in ("quick", "rescan"):
        state.deadline_s = config.QUICK_BUDGET_S - config.JUDGE_RESERVE_S
    yield ScanEvent(type="status", data={"message": "Scan started", "scan_id": state.scan_id}).to_sse()

    scan_task = asyncio.create_task(run_scan(req, state))
    try:
        while True:
            get_task = asyncio.create_task(state.events.get())
            done, _ = await asyncio.wait({get_task, scan_task}, timeout=HEARTBEAT_S, return_when=asyncio.FIRST_COMPLETED)
            if get_task in done:
                yield get_task.result().to_sse()
                continue
            get_task.cancel()
            if scan_task in done:
                while not state.events.empty():  # drain anything left
                    yield state.events.get_nowait().to_sse()
                break
            yield ": ping\n\n"  # heartbeat keeps proxies from closing an idle stream

        try:
            report = scan_task.result()
            yield ScanEvent(type="report", data=report.model_dump(mode="json")).to_sse()
        except GuardrailError as exc:
            yield ScanEvent(type="error", data={"message": str(exc), "guardrail": True}).to_sse()
        except Exception as exc:  # noqa: BLE001
            logging.exception("scan failed")
            yield ScanEvent(type="error", data={"message": f"{type(exc).__name__}: {exc}"}).to_sse()
        yield ScanEvent(type="done", data={
            "llm_calls": state.llm_calls, "tokens_in": state.tokens_in, "tokens_out": state.tokens_out,
        }).to_sse()
    finally:
        if not scan_task.done():
            scan_task.cancel()  # browser closed the tab
        flush()


@app.post("/api/scan")
async def scan(req: ScanRequest) -> StreamingResponse:
    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(_stream(req), media_type="text/event-stream", headers=headers)


@app.get("/api/selftest/stream")
async def selftest_stream(seconds: int = 600) -> StreamingResponse:
    """Deploy check: one SSE request that stays open `seconds` (max 840) and keeps the CPU busy.
    If ticks keep rising every 5 s for the whole run on Cloud Run, long scans will survive."""
    seconds = max(5, min(seconds, 840))

    async def gen():
        start, ticks = asyncio.get_running_loop().time(), 0
        while (elapsed := asyncio.get_running_loop().time() - start) < seconds:
            ticks += sum(i * i for i in range(200_000)) > 0  # real CPU work between sleeps
            yield ScanEvent(type="status", data={"elapsed_s": round(elapsed), "ticks": ticks}).to_sse()
            await asyncio.sleep(5)
        yield ScanEvent(type="done", data={"elapsed_s": round(elapsed), "ticks": ticks}).to_sse()

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


class PatchRequest(BaseModel):
    scan_id: str


class PatchResponse(BaseModel):
    patch: str
    failed_categories: list[Category]


@app.post("/api/patch")
async def patch(req: PatchRequest) -> PatchResponse:
    report = SCAN_HISTORY.get(req.scan_id)
    if report is None:
        raise HTTPException(404, "Scan not found (it may have run on another instance).")
    failed = [c.category for c in report.categories if c.status == "FAIL"]
    try:
        patch_text = await suggest_patch(report)
    except NotBuiltYet as exc:
        raise HTTPException(501, str(exc)) from exc
    return PatchResponse(patch=patch_text, failed_categories=failed)


@app.get("/api/report/{scan_id}")
def get_report(scan_id: str) -> dict:
    report = SCAN_HISTORY.get(scan_id)
    if report is None:
        raise HTTPException(404, "Scan not found")
    return report.model_dump(mode="json")


class ChatRequest(BaseModel):
    message: str
    history: list[Turn] = []


@app.post("/victims/{name}/chat")
async def victim_chat(name: str, req: ChatRequest) -> dict:
    """Lets anyone talk to a zoo victim over HTTP (useful to test the adapter end to end)."""
    if name not in victims.VICTIM_NAMES:
        raise HTTPException(404, f"unknown victim '{name}'")
    try:
        turn = await victims.reply(name, req.history, req.message)
    except NotBuiltYet as exc:
        raise HTTPException(501, str(exc)) from exc
    return {"reply": turn.content, "blocked": turn.blocked}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

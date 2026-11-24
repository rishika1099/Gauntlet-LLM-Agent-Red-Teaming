# Cloud Run image (same pattern as Ghost Trials). cloudbuild.yaml builds and deploys it on every push to main.
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PORT=8080
# keep-alive above the 900 s request timeout, so long SSE scans are never cut by uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT} --timeout-keep-alive 920"]

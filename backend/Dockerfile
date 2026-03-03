# ── Stage 1: builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini entrypoint.sh ./

RUN pip install --no-cache-dir . psycopg2-binary

# ── Stage 2: runtime (slim API — no Chromium, no Playwright) ─────
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app .

RUN chmod +x entrypoint.sh

USER nobody

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

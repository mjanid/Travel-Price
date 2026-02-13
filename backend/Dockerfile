FROM python:3.11-slim

WORKDIR /app

# System deps for PostgreSQL client AND Playwright Chromium
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev \
    # Playwright Chromium dependencies:
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 libwayland-client0 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "." psycopg2-binary && \
    playwright install chromium --with-deps

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Re-install Playwright browsers as appuser so the binary lands in ~appuser/.cache
USER appuser
RUN playwright install chromium

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── JobBot — containerized job application automation ──────────────────────
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Copy application code
COPY . .

# Install Playwright browsers (Chromium only for speed)
RUN playwright install chromium --with-deps

# Data directory (mount a volume here to persist DB + sessions)
RUN mkdir -p data/resumes data/sessions data/screenshots

# Default env — all overridable via docker run -e or .env
ENV JOB_BOT_HEADLESS=true \
    JOB_BOT_SLOW_MO=0 \
    SCRAPER_WORKERS=5 \
    SCORER_WORKERS=4 \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "run_dashboard.py"]

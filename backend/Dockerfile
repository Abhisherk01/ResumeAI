FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- PDF rendering system libraries (Phase 8, P8-1) ---
# WeasyPrint drives Pango/HarfBuzz/FontConfig at RENDER time: it imports
# cleanly without them and only fails when asked to produce a PDF - which
# is why the smoke test RENDERS a page instead of just importing.
# fonts-dejavu-core is load-bearing: zero installed fonts = PDFs with no
# visible text. Layer sits BEFORE COPY so code edits never re-run apt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        fontconfig \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
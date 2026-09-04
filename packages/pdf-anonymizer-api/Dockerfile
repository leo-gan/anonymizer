# Build from the repository root. Compose in this directory sets that context
# so this file can COPY pdf-anonymizer-core as a sibling package.
#
#   docker compose -f packages/pdf-anonymizer-api/docker-compose.yml up --build
#
# Default is regex-only: no API keys, no language-model extra.
# Compose publishes 127.0.0.1:8000. There is no authentication.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 1000 anonymizer

WORKDIR /src
COPY packages/pdf-anonymizer-core /src/packages/pdf-anonymizer-core
COPY packages/pdf-anonymizer-api /src/packages/pdf-anonymizer-api

RUN pip install --no-cache-dir \
        "./packages/pdf-anonymizer-core" \
        "./packages/pdf-anonymizer-api" \
    && rm -rf /root/.cache/pip

USER anonymizer
WORKDIR /work
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# 0.0.0.0 inside the container; compose publishes 127.0.0.1:8000.
CMD ["pdf-anonymizer-api", "--host", "0.0.0.0", "--port", "8000"]

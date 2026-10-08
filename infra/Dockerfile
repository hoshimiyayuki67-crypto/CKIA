FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/src \
    CAMPUS_DEMO=0 \
    CAMPUS_KNOWLEDGE_DIR=/app/knowledge/processed

WORKDIR /app
COPY backend/requirements-runtime.lock.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && groupadd --gid 10001 campus \
    && useradd --uid 10001 --gid campus --no-create-home campus \
    && mkdir -p /app/knowledge/processed

COPY backend/src /app/backend/src
COPY backend/examples /app/backend/examples
COPY web /app/web

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"
CMD ["python", "-m", "uvicorn", "campus_assistant.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--limit-concurrency", "100", "--timeout-keep-alive", "5"]

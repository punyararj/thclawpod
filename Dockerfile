FROM python:3.12-slim

# Don't write .pyc files and don't buffer log output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY clawpod_server.py .

# Run as non-root; /data holds user_session.json (written to CWD)
RUN useradd --create-home clawpod \
    && mkdir /data \
    && chown clawpod:clawpod /data
USER clawpod
WORKDIR /data

EXPOSE 7001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7001/health')" || exit 1

CMD ["python", "/app/clawpod_server.py"]

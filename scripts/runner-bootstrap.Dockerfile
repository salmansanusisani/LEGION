# Infrastructure-only copy of the official runner recipe. Dependency pins,
# installation commands, Python image and working directory are unchanged.
# Longer DOWNLOAD timeouts do not change service/test request timeouts.
FROM python:3.12-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=15 \
    PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=180000
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && playwright install --with-deps chromium
WORKDIR /work

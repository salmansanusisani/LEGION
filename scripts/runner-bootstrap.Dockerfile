# Infrastructure-only copy of the official runner recipe. Dependency pins,
# Python image and working directory are unchanged. Upgrade only the installer
# to support resumable downloads; separate layers retain completed installs.
# Longer DOWNLOAD timeouts do not change service/test request timeouts.
FROM python:3.12-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=15 PIP_RESUME_RETRIES=20 \
    PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=180000
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip==26.2.1
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN playwright install-deps chromium
RUN playwright install chromium
WORKDIR /work

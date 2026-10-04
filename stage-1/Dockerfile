# Tablekeeper Stage 1 — reservations (HTTP API only)
#
# Standard library only: nothing is installed, so the build has no network
# dependency and the run-time image has no runtime packages to resolve.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TABLEKEEPER_DB=/data/tablekeeper.sqlite3 \
    PORT=8080

# python:3.12-slim already carries /usr/share/zoneinfo, which is all zoneinfo
# needs, so no tzdata package is pulled and the build needs no network at all.

WORKDIR /app
COPY app/ /app/app/

RUN mkdir -p /data

EXPOSE 8080

CMD ["python", "-m", "app.main"]

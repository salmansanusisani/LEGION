#!/usr/bin/env python3
"""Snapshot official-room OpenCode counters without transcripts or credentials."""
import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import subprocess

SEATS = ("legion-lead", "legion-builder", "legion-checker", "legion-ux")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room")
    parser.add_argument("--database", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Choose a fresh output path; usage snapshots are not overwritten.")
    database = sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True)
    database.row_factory = sqlite3.Row
    report = {
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "room": args.room,
        "source": "OpenCode local session counters, read-only",
        "cost_disclaimer": "Model-reported cost is not verified provider billing. Zero does not prove free usage.",
        "seats": [],
    }
    for seat in SEATS:
        response = subprocess.run(["band", "--session", seat, "sessions", "--json"],
                                  capture_output=True, text=True, timeout=60, check=True)
        sessions = json.loads(response.stdout)
        matching = [s for s in sessions if s.get("room") == args.room]
        row = {"seat": seat, "sessions": []}
        for session in matching:
            identity = session.get("provider_session_id")
            values = database.execute(
                "SELECT id, tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, "
                "tokens_cache_write, cost AS model_reported_cost, time_created, time_updated "
                "FROM session WHERE id = ?", (identity,)).fetchone()
            row["sessions"].append(dict(values) if values else {
                "id": identity, "counters": "unavailable; do not treat as zero"})
        report["seats"].append(row)
    database.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    print(f"Saved numeric-only session snapshot to {args.out}")


if __name__ == "__main__":
    main()

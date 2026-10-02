#!/usr/bin/env python3
"""Schedule addressed BAND handoffs sequentially; never send implementation input."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import time

SEATS = {
    "legion-lead": "b4dcdced-cd0b-4c72-bdfa-290878f3d915",
    "legion-builder": "de448aea-1817-4645-9660-64c68bee6c4b",
    "legion-checker": "deb77165-2402-464c-8684-ef4c11062720",
    "legion-ux": "79e5da9b-dc9c-4e36-a716-78a69fad540f",
}
NAMES = {"LEGION Lead", "LEGION Builder", "LEGION Checker", "LEGION UX"}
HEADER = re.compile(r"^(\S+) \[text\] (.+?) \((Agent|User)\): ", re.M)


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"{args[:4]}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def available_memory():
    for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024
    raise RuntimeError("MemAvailable is unavailable")


def messages(room):
    raw = command(["band", "room", "messages", room, "--type", "text", "--page", "1"])
    headers = list(HEADER.finditer(raw))
    records = []
    for i, header in enumerate(headers):
        stamp, sender, kind = header.groups()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
        body = raw[header.end():end]
        if kind != "Agent" or sender not in NAMES:
            continue
        first_line = body.splitlines()[0] if body.splitlines() else ""
        for seat, identity in SEATS.items():
            if f"@[[{identity}]]" in first_line or f"@salmansanusi90/{seat}" in first_line:
                key = hashlib.sha256((stamp + sender + seat).encode()).hexdigest()
                records.append((stamp, key, seat, sender))
    return sorted(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room")
    parser.add_argument("--active", default="legion-lead", choices=[*SEATS, "none"])
    parser.add_argument("--evidence", required=True, type=pathlib.Path)
    args = parser.parse_args()
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if args.evidence.exists():
        for line in args.evidence.read_text().splitlines():
            row = json.loads(line)
            seen.update(row.get("handoff_keys", []))
    active = None if args.active == "none" else args.active
    activated = dt.datetime.now(dt.timezone.utc)
    idle_since = None
    deferred = None

    def record(event, **fields):
        row = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "event": event,
               "available_ram_mib": round(available_memory()), **fields}
        with args.evidence.open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)

    record("scheduler_started", active=active, room=args.room)
    while True:
        if available_memory() < 1280:
            if active:
                command(["band", "--session", active, "stop"])
            record("resource_pause", active=active)
            return 75

        if active:
            logs = command(["band", "--session", active, "logs"])
            ended = []
            for line in logs.splitlines():
                if "activity turn_ended session default-" + args.room not in line:
                    continue
                try:
                    stamp = dt.datetime.fromisoformat(line.split()[0].replace("Z", "+00:00"))
                except ValueError:
                    continue
                if stamp > activated:
                    ended.append(stamp)
            if not ended:
                time.sleep(20)
                continue
            # Allow the final addressed room message to settle after turn_ended.
            if (dt.datetime.now(dt.timezone.utc) - ended[-1]).total_seconds() < 8:
                time.sleep(10)
                continue
            command(["band", "--session", active, "stop"])
            record("seat_stopped_after_turn", seat=active)
            active = None
            idle_since = time.monotonic()

        try:
            pending = [row for row in messages(args.room) if row[1] not in seen]
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            record("room_read_retry", detail=str(error))
            time.sleep(30)
            continue
        if not pending:
            if idle_since is not None and time.monotonic() - idle_since > 90:
                record("no_addressed_handoff", outcome="requires_operator_inspection")
                return 0
            time.sleep(20)
            continue
        target = pending[0][2]
        if target in {"legion-checker", "legion-ux"}:
            runner = subprocess.run(["docker", "image", "inspect", "df-harness-runner"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=20)
            if runner.returncode:
                if deferred != target:
                    record("waiting_for_runner", pending_seat=target)
                    deferred = target
                time.sleep(30)
                continue
        handoff_keys = [row[1] for row in pending if row[2] == target]
        # Start the existing peer, then bind the existing room-specific runtime.
        activated = dt.datetime.now(dt.timezone.utc)
        command(["band", "--session", target, "onboard", "--host", "generic"])
        sessions = json.loads(command(["band", "--session", target, "sessions", "--json"]))
        bound = any(row.get("room") == args.room and row.get("binding") == "bound"
                    for row in sessions)
        if not bound:
            command(["band", "--session", target, "attach", "--host-session",
                     "default-" + args.room, "--room", args.room, "--runtime", "owned",
                     "--transport", "opencode"])
        active = target
        seen.update(handoff_keys)
        idle_since = None
        deferred = None
        record("seat_started", seat=target, sender=pending[0][3], handoff_keys=handoff_keys)
        time.sleep(20)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Scheduler stopped for inspection: {error}", flush=True)
        raise SystemExit(1)

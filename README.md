# BAND Dark Factory starter

Track: **Tablekeeper**. Team repository: `salmansanusisani/LEGION`.

This checkout is the official result workspace. Factory setup and the teammate's
coverage checklist are present; the stage folders remain placeholders until the
BAND factory builds and independently accepts them. The planned official run is
defined by `evidence/official-dispatch.md`. No completed Tablekeeper stage is claimed
by this preparation commit.

Local scaffold for the WeAreDevelopers × BAND Dark Factory hackathon. It uses four persistent BAND-owned OpenCode identities, one generic mandate per seat, and `opencode/big-pickle`.

## Current local setup

- BAND Desktop `0.4.12`
- OpenCode `1.18.30`
- Model `opencode/big-pickle`
- BAND account `salmansanusi90`
- Docker available

Persistent seats:

- `salmansanusi90/legion-lead`
- `salmansanusi90/legion-builder`
- `salmansanusi90/legion-checker`
- `salmansanusi90/legion-ux`

Their owner instructions are live-linked to the files in `mandates/`. No BAND agent API keys are stored in this repository.

## Readiness

Run:

```bash
./scripts/check-readiness.sh
```

The project-level `opencode.json` also selects `opencode/big-pickle` for direct OpenCode sessions.

## Rehearsal versus official run

The initial BAND room is connectivity rehearsal only. Do not submit it. Create a fresh room after the official track specification is saved under `official-spec/`.

For a newly created room, BAND creates one room-specific host session per seat. Start a room-specific seat with:

```bash
band --session legion-lead restart --host-session default-ROOM_ID
band --session legion-builder restart --host-session default-ROOM_ID
band --session legion-checker restart --host-session default-ROOM_ID
band --session legion-ux restart --host-session default-ROOM_ID
```

Stop all workers without deleting their identities or room history:

```bash
band stop --all
```

## Official run

Place the exact organizer-provided specification under `official-spec/`. Start a fresh room and preserve the initial task, every handoff, every rejection, the final room export, and measured usage. The task supplied for each stage must be the only human steering during that stage.

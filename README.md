# BAND Dark Factory starter

Local scaffold for the WeAreDevelopers × BAND Dark Factory hackathon. It uses four distinct BAND Remote Agent identities, one generic mandate per seat, and OpenCode with `opencode/big-pickle`.

## 1. Install dependencies

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install "band-sdk[opencode]" python-dotenv
cp .env.example .env
cp agent_config.example.yaml agent_config.yaml
```

`uv sync --python 3.12` is also supported if `uv` is installed, but it is not required.

## 2. Create BAND identities

In the BAND dashboard, create four Remote Agents named Coordinator, Implementer, Verifier, and Experience Reviewer. Copy each UUID and one-time API key into the matching local block in `agent_config.yaml`.

Never commit `agent_config.yaml`.

## 3. Start OpenCode

```bash
./scripts/start-opencode.sh
```

The project-level `opencode.json` selects `opencode/big-pickle`.

Check the local setup at any time with:

```bash
./scripts/check-readiness.sh
```

## 4. Start the seats

Open four more terminals:

```bash
./scripts/run-seat.sh coordinator
./scripts/run-seat.sh implementer
./scripts/run-seat.sh verifier
./scripts/run-seat.sh experience_reviewer
```

Add all four Remote Agents to one BAND room. Keep `BAND_AUTONOMOUS=0` for a harmless rehearsal on an unrelated toy specification.

## 5. Official run

Place the official specification under `official-spec/`. Start a fresh room and preserve the original task, every handoff, every rejection, and the final export. Use `BAND_AUTONOMOUS=1` only inside an isolated environment after confirming the mandates and permissions on a rehearsal task.

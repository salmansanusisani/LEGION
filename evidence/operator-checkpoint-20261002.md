# Operator recovery checkpoint

Observed 2026-10-02 around 21:11 UTC. This is infrastructure/preparation evidence, not a stage acceptance report.

## Actual delivery status

- Official room: `ee44a58f-9400-44ac-bb1f-21570fbea358`.
- Lead dispatched the full Stage 1 task/spec through three addressed messages. No new human implementation instructions were sent afterward.
- Builder recovered from two BAND connection startup failures and began its turn at 20:26 UTC. It has authored backend modules, `Dockerfile` and `RUN.md` in `stage-1/`; they remain uncommitted work in progress at this checkpoint.
- No stage has independent acceptance. No official isolated test pass is claimed.
- Submission checklist, copy, slide source and demo recording plan are committed. `submission/assets/cover.png` is inspected generated illustration, not product evidence.

## Live operations

One Builder runtime is active. One test-runner bootstrap is active under the Docker build lock. The scheduler supervises addressed handoffs; reviewers remain gated on the `df-harness-runner` image. Its evidence is `evidence/resource-schedule.jsonl`.

Available RAM at the last check: approximately 3537 MiB. Swap is nearly full; do not launch extra coding workers, browsers or parallel builds. Existing user applications were not closed, and unrelated Docker images/data were not deleted.

The original pip 25.0.1 installer discarded interrupted downloads. The infrastructure-only runner adapter now installs `pip==26.2.1` to resume downloads, while retaining the original test dependencies, browser install command, organizer checkout and service limits. See FACTORY. The pip installer step completed successfully; test dependency downloads have not yet completed at this checkpoint.

## Remaining dependencies

- BAND and package-download connections have been unstable. Preserve completed download/build layers rather than repeatedly restarting them.
- The standard presentation dependency loader is not available. A Canva fallback request was blocked **before sending** because sharing factory information to that third-party service needs explicit owner approval. Local slide source is preserved; no Canva design exists.
- Full untouched `room.json` and actual BAND/app demo recording remain pending. CLI supports structured full-type message pages, but those page backups must not be misrepresented as the native complete-session export.
- BAND `usage session` returned `(no sessions)` for the official OpenCode provider session. Token/cost telemetry is unknown, not zero; catalog estimates would not be billing evidence anyway.

## Recovery discipline

Inspect current seat bindings, logs, scheduler evidence and Git state before restarting anything. Never bulk-detach the seats: that previously removed owned-runtime templates. Stop/restart only existing identities, maintain one runtime at a time, and never resend the human task or impersonate an agent. Do not commit partially authored product code as a completed stage. Preserve all accepted stage snapshots and teammate history.

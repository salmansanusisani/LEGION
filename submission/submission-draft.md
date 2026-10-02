# LEGION — Tablekeeper

Draft only. Reconcile every claim against final acceptance evidence before submitting.

## Short description

A BAND-coordinated software factory for Tablekeeper: restaurant reservations built through separate implementation, verification and experience-review seats.

## Motivation

Restaurant reservations demand more than a successful happy-path booking. Competing diners, lost responses, changing policies and closed tables must not silently create duplicates or lose reservations. Tablekeeper's staged specification makes those correctness requirements explicit.

## Factory approach — configured and dispatched

LEGION separates four persistent BAND identities: Lead coordinates requirements and acceptance; Builder owns product implementation; Checker independently evaluates exact revisions; UX reviews user workflows. The seats use OpenCode with `opencode/big-pickle` and generic, live-linked mandates. Domain requirements travel in the task and addressed handoffs rather than hidden standing instructions.

Our Linux host has approximately 7.7 GiB RAM. Coding runtimes run sequentially under an exclusive lock, a RAM launch guard and CPU affinity. Docker builds are serialized. Scheduling changes runtime availability without inserting human implementation hints into the official room.

## Product scope — requirements, not yet delivered claims

The intended progression is a reservation API; a diner-facing booking experience with combined tables; dated policies, history and recurring reservations; then atomic seating repairs and recurring amendments. Later stages must retain earlier behavior and import earlier exports.

## Architecture

Planned direction: Python standard-library HTTP service, SQLite transactions and timezone-aware scheduling, with container-local browser assets. Replace this paragraph with the architecture the Builder actually delivers.

## Verification and results — pending

Insert only accepted stage SHAs, official isolated-mode report paths, actual test totals, overshoot outcomes and independent UX evidence. Do not use rehearsal checks as official acceptance evidence. Disclose the runner download-timeout adapter and any unresolved specification gaps.

## Challenges

Limited host memory motivated sequential, distinct-seat execution. Slow and unstable network access interrupted pinned test-runner downloads and BAND connections. The repository records infrastructure recovery separately from product acceptance.

## Links

- Source: https://github.com/salmansanusisani/LEGION
- Full BAND export: pending
- Demo video: pending
- Slide presentation: pending
- Cover illustration: `submission/assets/cover-v2.png` (four-agent geometric group portrait, generated conceptual artwork)

## Team and tools

Repository owner: `salmansanusisani`; teammate: `wyyyrdx`. Confirm preferred public names before submitting. Tools: BAND Desktop, OpenCode, Big Pickle, Docker and Git. Final application-language and storage tags must match the delivered code.

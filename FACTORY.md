# Dark Factory

This document will become the reproducible operating manual and evidence summary for the submitted factory.

## Seats

| Seat | Owns | Must not do |
| --- | --- | --- |
| Coordinator | Ledger, delegation, decisions, acceptance | Production implementation |
| Implementer | Product code, packaging, repair | Self-acceptance or weakening independent checks |
| Verifier | Independent tests and release verdict | Editing production code |
| Experience reviewer | Rendered UI and user-flow evidence | Editing production code |

All standing mandates are stored in `mandates/` and are domain-neutral. Track-specific details belong only in the official task dispatched to the room.

The submitted seat names are LEGION Lead, LEGION Builder, LEGION Checker, and LEGION
UX. Their mandate files are respectively `legion-lead.md`, `legion-builder.md`,
`legion-checker.md`, and `legion-ux.md`. These are replacement identities created
after the earlier rehearsal runtimes lost their local templates. The earlier
identities and remote room history were preserved, but are not the official roster.

## Runtime

- Collaboration: BAND Desktop and BAND rooms
- Agent harness: BAND-owned OpenCode ACP runtimes
- Model: `opencode/big-pickle`
- Authentication: inherited from the local OpenCode account; no provider key is stored in this repository
- Runtime approval policy: `approve-all` for headless agent operation
- Persistent BAND handles:
  - `salmansanusi90/legion-lead`
  - `salmansanusi90/legion-builder`
  - `salmansanusi90/legion-checker`
  - `salmansanusi90/legion-ux`

The first connectivity room is rehearsal-only and must not be submitted as the official hackathon run.

## Low-resource execution

The development host has four CPU cores and 7.7 GiB RAM, with roughly 1 GiB swap.
At official-run preparation it had 83 GiB free disk and about 3 GiB available RAM.
The toy rehearsal exposed duplicate workers and parallel builds as a crash risk.

`scripts/opencode-low-resource.sh` checks that at least 2 GiB RAM is available before
launch, takes an exclusive process lock, and starts OpenCode with nice 10 and CPU
affinity 0–1. The affinity and priority apply to the runtime and ordinary children;
Docker daemon build processes do not inherit the Docker client's limits. Therefore
the operator also schedules only one build/test process at a time and observes host
memory. A conflicting worker launch exits 75 and may be retried after the active
runtime ends. No production guidance is sent during scheduling.

Each seat delivers an addressed handoff and ends its turn. The operator stops that
runtime and brings the next recipient online. The seats retain separate identities,
conversation contexts, ownership, and verdicts despite executing sequentially.

## Official-run preparation

The recovered result checkout is `/home/salman/Documents/Python/bit/result`, cloned
from the team's existing LEGION remote at `9eae0e7`. It preserves the teammate's
review mandates and checklist. No stage implementation was inherited. The complete
four-stage initial task is retained in `evidence/official-dispatch.md`. All product
code must come from the band's exchanges in the fresh official room.

The organizer's harness, tests, requirements and checkout remain unchanged. The
original runner recipe repeatedly failed during dependency downloading, including
a pip read timeout after 27 MB of a 48 MB wheel. An infrastructure adapter uses
`scripts/runner-bootstrap.Dockerfile`, which preserves the Python image, exact
dependency pins and working directory while increasing
dependency-download timeouts to 180 seconds. A subsequent timeout showed that the
base image's older pip discarded partial wheels. The adapter now pins only the
installer to `pip==26.2.1`, enables up to 20 resume attempts and separates completed
install steps into cached build layers. The Playwright dependency and Chromium
installation phases are also split into their two documented commands so a completed
system-package layer survives an interrupted browser download. Test-library versions
and installed browser remain unchanged. This does not change any service
request, startup, suite or runtime-network limit.

`scripts/infra-bin/docker` applies this disclosed recipe only when the harness
builds `df-harness-runner`. It verifies the original recipe's SHA-256 first and
passes every other Docker invocation through unchanged. The runtime wrapper adds
that directory to PATH. Thus product builds use their original Dockerfiles, and
the unchanged official suites still exercise the original isolated network and
CPU/RAM limits. This is environment recovery, not official-package acceptance
evidence. Reports must disclose the adapter.

Host-mode toy checks passed 8/8, but the earlier isolated attempts did not complete.
Those attempts are retained and do not count as accepted work.

Detach behavior requires care: this BAND version removed local owned-runtime
templates when all host sessions were detached. Agent identities and remote room
history persisted. The owner explicitly approved recreation with the previous
automatic execution policy. Four distinct replacement owned runtimes were created
and linked to the corresponding generic mandates. Future scheduling uses worker
stop/restart rather than bulk detach.

## Acceptance protocol

1. Coordinator creates a numbered requirements ledger from the supplied specification.
2. Implementer produces an auditable revision and evidence.
3. Verifier independently tests that exact revision and may reject it.
4. Experience reviewer independently exercises the rendered product and may reject it.
5. Rejected work returns to the implementer and must be independently rechecked.
6. Coordinator accepts only a clean-environment revision supported by both verdicts.

## Measurements to complete during the run

`scripts/capture-usage.py` snapshots numeric OpenCode counters for only the four
official-room provider session IDs. It reads the local database in read-only mode,
does not export messages or credentials, and refuses to overwrite an earlier
snapshot. These are cumulative session counters: use differences between snapshots
for stage-level attribution when the same session spans multiple stages. Missing
counters mean unknown, not zero. Model-reported cost is not verified billing.

The first snapshot is `evidence/usage-20261002-early.json`. BAND's ccusage-backed
command had returned no sessions for this OpenCode runtime, so the direct numeric
snapshot is reported separately rather than pretending BAND supplied it.

- Start/end time and elapsed time per stage
- Model and token/resource use per seat
- Revisions produced and accepted
- Checks run, failures found, repairs made, and regressions prevented
- Container build/start command and offline verification
- Known limitations and unverified claims

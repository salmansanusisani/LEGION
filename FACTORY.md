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

## Runtime

- Collaboration: BAND Desktop and BAND rooms
- Agent harness: BAND-owned OpenCode ACP runtimes
- Model: `opencode/big-pickle`
- Authentication: inherited from the local OpenCode account; no provider key is stored in this repository
- Runtime approval policy: `approve-all` for headless agent operation
- Persistent BAND handles:
  - `salmansanusi90/legion-coordinator`
  - `salmansanusi90/legion-implementer`
  - `salmansanusi90/legion-verifier`
  - `salmansanusi90/legion-experience-review`

The first connectivity room is rehearsal-only and must not be submitted as the official hackathon run.

## Acceptance protocol

1. Coordinator creates a numbered requirements ledger from the supplied specification.
2. Implementer produces an auditable revision and evidence.
3. Verifier independently tests that exact revision and may reject it.
4. Experience reviewer independently exercises the rendered product and may reject it.
5. Rejected work returns to the implementer and must be independently rechecked.
6. Coordinator accepts only a clean-environment revision supported by both verdicts.

## Measurements to complete during the run

- Start/end time and elapsed time per stage
- Model and token/resource use per seat
- Revisions produced and accepted
- Checks run, failures found, repairs made, and regressions prevented
- Container build/start command and offline verification
- Known limitations and unverified claims

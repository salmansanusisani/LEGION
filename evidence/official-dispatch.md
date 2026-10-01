# LEGION official Tablekeeper factory run

Build all four stages sequentially in the BAND room receiving this task. This file
and the authoritative stage specifications below form the complete initial human
task. Dispatching all four stages at once is explicitly permitted by the participant
guide. Do not ask the human for steering, debugging, approvals, decisions or reruns.

## Paths

- Result Git repository: `/home/salman/Documents/Python/bit/result`
- Organizer package, read-only: `/home/salman/Documents/Python/bit/_organizer/dark-factory-wearedevs`
- Specifications: organizer `tablekeeper/spec/stage-1.md` through `stage-4.md`
- Human-prepared coverage aid: result `evidence/stage-1-checklist.md`
- Evidence: result `evidence/checks/<unique-run>` and `evidence/reviews/`
- Harness Python: `/home/salman/Documents/Python/bit/.venv/bin/python`

The specifications are authoritative. The checklist is a secondary aid and must be
corrected against the complete spec, never used to narrow it. Do not inspect other
products' source, schemas or API documentation. Build to the written specification,
not to the supplied tests. Read failure output to diagnose observed defects.

## Roles and delivery

- Coordinator: `@salmansanusi90/legion-coordinator`
- Implementer: `@salmansanusi90/legion-implementer`
- Independent verifier: `@salmansanusi90/legion-verifier`
- Experience reviewer: `@salmansanusi90/legion-experience-review`

Coordinator: read the participant guide and all four specifications, then create the
numbered requirements ledger. The result repository contains factory documentation
and placeholder stage folders only; it contains no product implementation. Start with
Stage 1. After acceptance, copy the accepted folder forward and extend the copy.
Never backport later-stage behavior into earlier stage folders.

Every substantive handoff must directly mention exactly the responsible next seat and
include the complete current specification and task. Numbered messages are acceptable.
Do not rely on a message identifier, attachment, abbreviated summary or assertion that
the receiver can read the room. File paths supplement the complete handoff.

Every worker must deliver its final revision/report through a direct coordinator
mention before ending its turn. The operator schedules stopped workers in response to
these messages, without changing the task or posting further implementation input.

## Engineering decisions

The implementer owns language, framework, storage, UI and architecture. Prefer a small,
maintainable implementation and minimal downloads for this machine. Atomic state changes,
idempotency, time-zone handling, state portability and observable UI recovery are core
requirements; the spec determines their exact behavior. Do not omit a requirement to
save resources. Preserve earlier-stage behavior and immutable history where required.

Finish the current stage completely before adding the next. Use small commits referencing
ledger IDs; report full SHA and clean worktree. Never amend, squash or rebase after a
handoff. Only the implementer writes product code. Reviewers create independent review
scripts outside the stage folders and test isolated checkouts of the named revision.

## Resource policy

This host has 4 CPU cores, 7.7 GiB RAM, about 1 GiB swap, and 83 GiB free disk at
dispatch preparation. Run exactly one coding runtime and one build/test at a time.
The runtime wrapper enforces exclusive worker launch, nice 10, CPUs 0–1 and a minimum
2 GiB available-RAM check. Do not start other agent runtimes or parallel Docker builds.
The operator switches runtimes after a finished turn; inactive seats remain stopped.

## Verification and progression

The independent verifier runs the unchanged official harness from the organizer folder:

```bash
/home/salman/Documents/Python/bit/.venv/bin/python -m harness run \
  --track tablekeeper --repo /home/salman/Documents/Python/bit/result \
  --stage N --mode isolated \
  --out /home/salman/Documents/Python/bit/result/evidence/checks/<fresh-run-name>
```

Run the complete official checks for suites 1..N and the prescribed overshoot probe.
Do not modify the organizer, deselect checks, weaken tests or hide previous failures.
Missing dependencies are BLOCKED. An observed specification violation is FAIL. Neither
supports acceptance. A failure in the intentional next-stage overshoot probe is expected;
it must not be confused with a failure in a required current/previous-stage suite.

Acceptance requires independently passing applicable checks on the exact revision,
no failed/error/skipped required tests, no overshoot, no open specification finding,
and the independent experience verdict. Visual review is not applicable to Stage 1;
review its documented API/operator workflow. Later stages require the real browser UI.
Coverage must include specification cases the shipped tests do not exercise.

Coordinator: after both reviews accept, record the SHA, requirement coverage, commands,
evidence, elapsed time and known limitations. Then dispatch the next stage. Route actual
rejections to the implementer for repair and independent rechecking; do not manufacture
disagreement or enter acknowledgement loops. Stop after Stage 4 acceptance or an honest
blocker that the team cannot resolve. Record the final outcome in `evidence/final-status.md`
and post a final room report.

## Submission evidence

Keep actual room exchanges and auditable Git history. Update factory measurements using
observed values; never invent token costs or timings. The human/operator will download the
unchanged full room export as `room.json`, inspect for secrets, run `harness check`, and
push the preserved history to `https://github.com/salmansanusisani/LEGION` after the run.
The presentation and demo video must show the real factory, handoff and resulting product.

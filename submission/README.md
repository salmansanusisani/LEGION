# Submission preparation

Status: **not submission-ready**. The official run has a Stage 1 handoff but no accepted product revision yet. Do not publish draft claims as completed work.

The target is the [WeAreDevelopers × BAND Dark Factory hackathon](https://lablab.ai/ai-hackathons/wearedevelopers-hackathon), Tablekeeper track, not Devpost.

## Release gates

- [ ] Each delivered stage is a complete standalone service with `Dockerfile` and tested `RUN.md`.
- [ ] Checker independently verifies each exact accepted SHA in the organizer's isolated mode, with all cumulative suites passing and no errors or skips.
- [ ] The next-stage suite fails for stages 1–3; stage snapshots are not backported.
- [ ] Independent UX review covers actual rendered desktop and 375 px mobile flows from stage 2 onward.
- [ ] Offline assets, concurrency, retries, ownership, accepted policies, import/export and atomic writes are checked against the full numbered ledger—not just public tests.
- [ ] FACTORY and README describe actual results, accepted SHAs, usage, failures and limitations; the download-timeout adapter is disclosed.
- [ ] Complete, untouched BAND session export is saved as root `room.json` and checked for completeness. CLI page backups are not a substitute unless the organizer accepts that format.
- [ ] Public GitHub main contains all artifacts and teammate history.
- [x] Cover art is present and accurately labelled as illustration, not product evidence.
- [ ] Editable slide presentation is finalized with actual results and screenshots.
- [ ] Demo video shows the real BAND room, a real addressed handoff and resulting work, plus the delivered app.
- [ ] Submission text matches verified delivery; all external material links work without account access.

No submission is sent by this preparation workflow. Final registration, acceptance of terms and submission remain owner actions requiring explicit confirmation.

## Files

- `submission-draft.md`: reusable copy; completion-dependent sections remain explicitly pending.
- `demo-script.md`: recording plan, not an existing video.
- `cover-prompt.md`: generated-art provenance after the cover is available.
- `assets/cover-v3.png`: approved blueprint pyramid cover with four waveform-separated tiers. Earlier versions are preserved at `assets/cover.png` and `assets/cover-v2.png`.

## Current recovery checkpoint

Official room: `ee44a58f-9400-44ac-bb1f-21570fbea358`.

On 2026-10-02, multiple runner builds failed during network downloads. The 180-second pip timeout attempt transferred 15.7 of 48.2 MB before timing out. BAND's daemon separately recorded REST timeouts and WebSocket heartbeat failures; the Builder failed to connect before producing app code. These are infrastructure failures, not failed product acceptance tests. The initial task and Lead's complete Stage 1 handoff remain intact. Recovery must start existing runtimes, not send new human implementation guidance.

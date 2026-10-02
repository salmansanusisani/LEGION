# Editable presentation content draft

This is local source copy, not a completed slide artifact. No accepted app revision or final product screenshot is available yet. Replace the status/evidence section with actual results before delivery.

## 1. Tablekeeper

LEGION

BAND Dark Factory hackathon

Speaker notes: Team repository https://github.com/salmansanusisani/LEGION. Introduce the product and the factory as separate evaluation subjects.

## 2. Reservation correctness

Two diners must never occupy the same table at overlapping times.

A retry must preserve the original booking outcome. An unsuccessful change must leave earlier reservations intact.

Speaker notes: These are organizer requirements, not yet verified implementation claims. Source: https://github.com/band-ai/dark-factory-wearedevs/blob/main/tablekeeper/spec/stage-1.md

## 3. Four distinct BAND seats

| Seat | Responsibility |
| --- | --- |
| LEGION Lead | Requirements ledger and acceptance decisions |
| LEGION Builder | Product implementation and repairs |
| LEGION Checker | Independent tests of exact revisions |
| LEGION UX | Independent user-flow and rendered experience review |

Speaker notes: The configured identities use OpenCode and `opencode/big-pickle`. Generic standing mandates separate ownership from the domain task. Source: https://github.com/salmansanusisani/LEGION/blob/main/FACTORY.md

## 4. Sequential execution on Linux

The host has approximately 7.7 GiB RAM.

An exclusive lock permits one coding runtime. A RAM guard checks launches. The runtime uses CPU affinity 0–1 and reduced scheduling priority. Docker builds run one at a time.

Speaker notes: CPU affinity applies to ordinary runtime children, not Docker daemon build processes. Sequential seats retain distinct identities, contexts and verdicts. Source: https://github.com/salmansanusisani/LEGION/blob/main/FACTORY.md

## 5. Required product progression

| Stage | Organizer scope |
| --- | --- |
| 1 | Reservation API and atomic booking changes |
| 2 | Browser booking and combined tables |
| 3 | Dated policies, history and recurring reservations |
| 4 | Atomic seating repairs and recurring amendments |

Speaker notes: This is required scope, not a feature-completion claim. Later stages must retain earlier behavior and support importing earlier exports. Source: https://github.com/band-ai/dark-factory-wearedevs/tree/main/tablekeeper/spec

## 6. Independent acceptance

Reviewers evaluate an exact clean commit.

The unchanged organizer suites must pass cumulatively in an isolated environment. Stages 1–3 must fail the next-stage overshoot probe. UX review begins with the API/operator workflow, then covers actual browser flows.

Speaker notes: The final service must run without outbound network access under 2 CPU and 2 GiB RAM limits, becoming healthy within 60 seconds. These are required limits, not measured performance. The infrastructure runner adapter only extends dependency-download timeouts and must remain disclosed. Sources: https://github.com/band-ai/dark-factory-wearedevs/blob/main/docs/participant-guide.md and https://github.com/salmansanusisani/LEGION/blob/main/FACTORY.md

## 7. Current status

Stage 1 implementation is in progress. No stage has independent acceptance yet.

Final evidence will include accepted revisions, isolated test reports, real product screenshots and a complete untouched BAND export. The demo must show an actual addressed handoff and the resulting product work.

Speaker notes: Update this slide from final acceptance evidence. Do not insert rehearsal numbers or generated UI images as product results. Submission requirements source: https://lablab.ai/ai-hackathons/wearedevelopers-hackathon

## Production notes

Create a 16:9 editable deck with a warm hospitality character, flat compositions and generous whitespace. Minimum font sizes: 42 pt cover, 32 pt headings, 17 pt body. Keep tables native/editable. Include actual accepted-app screenshots when available, never invented ones. Inspect every rendered page for fit, readability and factual consistency before delivering.

The bundled presentation dependency loader is unavailable in this environment. A Canva creation attempt was blocked before sending because that third-party destination requires explicit user approval. No Canva design currently exists.

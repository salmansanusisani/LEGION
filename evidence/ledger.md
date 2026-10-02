# LEGION official run — numbered requirements ledger

Track: `tablekeeper`. Source of truth: the organizer specifications
`tablekeeper/spec/stage-1.md` … `stage-4.md`, read-only at
`/home/salman/Documents/Python/bit/_organizer/dark-factory-wearedevs/`.

Rules for this ledger:

- Every requirement carries a stable ID. Implementer commit messages reference these IDs.
- A stage folder holds only its own stage. Never backport later-stage behavior into an earlier folder.
- Each stage folder is graded against suites 1..N **and** probed against suite N+1, which must fail.
- Explicit requirements come from the specification. Inferred constraints come from the dispatch's
  engineering direction. Ambiguities are listed with the decision the team took.
- Acceptance evidence is defined per stage in `evidence/<stage>-acceptance.md`.

---

## Stage 1 — reservations (API only)

Authoritative text: `stage-1.md` §1–§11. Secondary aid:
`evidence/stage-1-checklist.md` (row IDs D/R/V/A/I/B/C/T/S/M). The aid is corrected against the
spec, never used to narrow it.

### A. Delivery and deployment (§1–§2)

| ID | Requirement |
|---|---|
| S1-R001 | `stage-1/` contains a `Dockerfile` that the official harness builds. |
| S1-R002 | `stage-1/` contains `RUN.md` with one command that builds and starts the service with no manual setup. (gate 3) |
| S1-R003 | The image runs alone with `-e PORT=<port>` and a port mapping. Compose is never read. |
| S1-R004 | All runtime dependencies, initialization and seed data work inside the one container. No outbound network at run time. |
| S1-R005 | Operates within 2 vCPU and 2 GiB RAM; healthy within 60 s of container start. |
| S1-R006 | Handles up to 50 in-flight requests; ordinary requests under 5 s, `POST /_test/reset` under 10 s. |
| S1-R007 | Never returns 5xx, including under concurrent load. |
| S1-R008 | Scope is the HTTP API only. No browser UI. Restaurant/table creation endpoints and a batch-move UI are out of scope. |

### B. Listening, health, reset, conventions (§3)

| ID | Requirement |
|---|---|
| S1-R009 | Listens on `0.0.0.0` using `PORT`, default `8080`. |
| S1-R010 | `GET /health` → `200 {"status":"ok"}` within 60 s, only once service **and** data store can serve. |
| S1-R011 | `POST /_test/reset` is unauthenticated, returns `204` with empty body, replaces all state with the request fixture, and repeats cleanly. |
| S1-R012 | Requests/responses are `application/json; charset=utf-8`; response timestamps are RFC 3339 with explicit offset. |
| S1-R013 | Unknown request-body fields and unknown query parameters are ignored, never an error. |
| S1-R014 | IDs are opaque strings of at most 64 characters, including fixture-supplied IDs. |

### C. Model and fixture (§4)

| ID | Requirement |
|---|---|
| S1-R015 | Restaurants and tables arrive through `POST /_test/reset` only. No creation endpoints. |
| S1-R016 | Restaurant carries `timezone`, `slot_minutes`, `reservation_duration_minutes`, `cancellation_cutoff_minutes`, `opening_hours`. |
| S1-R017 | Table carries `capacity` as maximum party size. |
| S1-R018 | Fixture `weekday` ∈ `mon..sun`; `opens`/`closes` are local `HH:MM` 24-hour with `closes` always later than `opens` on the same local day; hours never cross midnight. |
| S1-R019 | Seeded users can log in immediately with the supplied password. |
| S1-R020 | Seeded `reservations` may confirm bookings carrying `id`, `reference`, `user_id` plus the create-body fields. |
| S1-R021 | Any calendar date is allowed. A booking is never rejected solely for being in the past; cancellation/amendment cutoffs still apply. |
| S1-R022 | A weekday with no `opening_hours` entry is closed. |

### D. Errors and validation (§5)

| ID | Requirement |
|---|---|
| S1-R023 | Every 4xx/5xx body is `{"error": {"code": ..., "message": ...}}`. `message` wording is free. |
| S1-R024 | Status/code table honoured exactly: `400 malformed_request`, `400 missing_idempotency_key`, `401 unauthenticated`, `403 forbidden`, `404 not_found`, `409 idempotency_key_reuse`, `422 validation_failed`. |
| S1-R025 | Correct JSON type with invalid format or out-of-range value → `422 validation_failed`. |
| S1-R026 | Endpoint-specific rules win: invalid `party_size` (strings, booleans, <1, non-integer) and `starts_at_local` that is not a bare local `YYYY-MM-DDTHH:MM` are `422 validation_failed`. |
| S1-R027 | An integer-valued **query** parameter is plain decimal digits only; `1e9`, `4.0`, `+4` → `422 validation_failed`. |
| S1-R028 | `400 malformed_request` is reserved for a body that does not parse or a field of the wrong JSON type. |
| S1-R029 | `Idempotency-Key` is 1..255 characters; otherwise `422 validation_failed`. |
| S1-R030 | No request produces 5xx. |

### E. Authentication (§6)

| ID | Requirement |
|---|---|
| S1-R031 | `POST /auth/signup` → `201 {"user_id", "display_name", "token"}`. |
| S1-R032 | `POST /auth/login` → `200 {"user_id", "display_name", "token"}`. |
| S1-R033 | Email already registered → `409 email_taken`. |
| S1-R034 | Password shorter than 8 characters → `422 validation_failed`. |
| S1-R035 | `email` not of the form `local@domain` → `422 validation_failed`. |
| S1-R036 | Wrong password or unknown email on login → `401 unauthenticated`. |
| S1-R037 | Public without a token: `/health`, `POST /_test/reset`, `POST /_test/export`, `POST /_test/import`, `POST /auth/signup`, `POST /auth/login`, `GET /restaurants`, `GET /restaurants/{id}`, `GET /availability`. Everything else requires a bearer token. |
| S1-R038 | Tokens do not expire; an account may hold multiple valid tokens and concurrent sessions. |
| S1-R039 | Passwords are stored with a password-hashing function (bcrypt/scrypt/Argon2 or equivalent). Plaintext storage is not permitted. |

### F. Idempotency (§7)

| ID | Requirement |
|---|---|
| S1-R040 | An idempotency key is required on `POST /reservations` and `POST /reservation-moves`. |
| S1-R041 | The key is scoped to the authenticated user; two users may use the same string independently. |
| S1-R042 | A replay is the same user, method, path and body. The same key with the same body on a different path is a new request and succeeds. |
| S1-R043 | Idempotency resolves after the body parses as a JSON object and the caller is authenticated, but **before** endpoint field validation and current-resource checks. |
| S1-R044 | Header absent or empty → `400 missing_idempotency_key`. |
| S1-R045 | First use of a key returns the normal response with **201**. |
| S1-R046 | Replay returns **200** with a body identical to the original response as a JSON value. |
| S1-R047 | Same key with a different JSON body → `409 idempotency_key_reuse`. |
| S1-R048 | A key whose original request failed with 4xx is reusable as a first use. |
| S1-R049 | "Same body" compares the parsed JSON value; key order and whitespace are irrelevant. |
| S1-R050 | Concurrent identical requests with one unused key: exactly one 201, the rest 200 with the same body, one effect only. |

### G. Browsing, availability, booking lifecycle (§8)

| ID | Requirement |
|---|---|
| S1-R051 | `GET /restaurants` → `{"restaurants": [{"id","name","timezone"}]}`. |
| S1-R052 | `GET /restaurants/{id}` returns the restaurant in fixture shape with slot grid, duration, cutoff, opening hours and tables; unknown id → `404 not_found`. |
| S1-R053 | `GET /availability` requires `restaurant_id`, `date` and `party_size`; each missing one alone → `422 validation_failed`. |
| S1-R054 | Availability response carries `restaurant_id`, `date`, `timezone` and `slots`. |
| S1-R055 | A slot appears for every `slot_minutes` step from `opens` with `slot + reservation_duration_minutes <= closes`. |
| S1-R056 | `available_table_ids` lists that restaurant's tables with `capacity >= party_size` and no overlapping confirmed reservation, in fixture order. A slot with none still appears with an empty list. |
| S1-R057 | A closed day returns `"slots": []`. |
| S1-R058 | `POST /reservations` success → 201 with `reservation_id`, `reference`, `restaurant_id`, `table_id`, `party_size`, `status` `confirmed`, `starts_at_local`, `starts_at`, `ends_at`, `created_at`. |
| S1-R059 | `reference` is 6–12 characters of `A-Z0-9`, unique across all reservations, and never changes. |
| S1-R060 | Overlapping confirmed interval for the table → `409 table_unavailable`, no partial booking. |
| S1-R061 | `starts_at_local` off the slot grid → `422 not_on_slot_grid`. |
| S1-R062 | Slot outside opening hours or ending after `closes` → `422 outside_opening_hours`. |
| S1-R063 | `party_size` above table capacity → `422 party_exceeds_capacity`. |
| S1-R064 | Nonexistent local time → `422 invalid_local_time`. |
| S1-R065 | Unknown restaurant, unknown table, or a table belonging to another restaurant → `404 not_found`. |
| S1-R066 | Occupancy is the half-open interval `[starts_at, starts_at + reservation_duration)`. A booking starting exactly when another ends succeeds. |
| S1-R067 | `GET /reservations` returns the caller's reservations, confirmed and cancelled, ordered `starts_at` descending, as `{"reservations": [...]}`, empty list when none. |
| S1-R068 | `GET /reservations/{reference}` returns one reservation; another owner's reference → `404 not_found` without leaking existence. |
| S1-R069 | `POST /reservations/{reference}/cancel` → 200 with the cancelled state, and the table is offered again by the next availability read. |
| S1-R070 | Cancelling an already cancelled reservation → 200 with current state, not an error. |
| S1-R071 | Cancelling at or after `cancellation_cutoff_minutes` before start → `409 cutoff_passed`. |
| S1-R072 | Cancelling another owner's reservation → `404 not_found`. |
| S1-R073 | `PATCH /reservations/{reference}` accepts any subset of `table_id`, `starts_at_local`, `party_size` and requires no idempotency key. |
| S1-R074 | PATCH validation equals POST validation; the same cutoff rule applies, measured against the **current** start → `409 cutoff_passed`. |
| S1-R075 | Amending a cancelled reservation → `409 reservation_cancelled`. |
| S1-R076 | A successful amendment releases the old occupancy and reserves the new one together; a failed amendment leaves the booking and its occupancy unchanged. |
| S1-R077 | `reference` and `reservation_id` survive an amendment. |

### H. Time and DST (§9)

| ID | Requirement |
|---|---|
| S1-R078 | All local dates and times follow the restaurant's `timezone` under IANA rules, independent of the host time zone. |
| S1-R079 | Spring-forward skipped local times never appear in availability; booking one is `422 invalid_local_time`. |
| S1-R080 | Fall-back repeated local times always resolve to the **first** occurrence. The slot appears once; the second occurrence is not bookable. |
| S1-R081 | `reservation_duration_minutes` is absolute elapsed time, not wall-clock subtraction. Local `ends_at` may read the earlier wall-clock hour. |
| S1-R082 | Required transitions: `Europe/Berlin` spring 2026-03-29 02:00→03:00, fall 2026-10-25 03:00→02:00; `America/New_York` spring 2026-03-08 02:00→03:00, fall 2026-11-01 02:00→01:00. |

### I. Export and import (§10)

| ID | Requirement |
|---|---|
| S1-R083 | `GET /_test/export` is unauthenticated and returns 200 with `track: "tablekeeper"`, `format_version: 1` and an opaque `state` object. |
| S1-R084 | `POST /_test/import` takes that whole object, atomically replaces state and returns 204. |
| S1-R085 | An unchanged export from this service is accepted; no dependence on source process, files, volume, port or network address. |
| S1-R086 | Import is replacement, not merge; repeating it restores the exported state without duplication. |
| S1-R087 | Invalid JSON follows §5. Missing fields, wrong track, wrong version or invalid state → `422 validation_failed` with the destination unchanged. |
| S1-R088 | Export and import finish inside the 10-second test-control timeout. |
| S1-R089 | Export is an atomic read-only snapshot; later source writes do not alter it. |
| S1-R090 | Import preserves accounts with hashed-password login, existing bearer tokens, fixture configuration, reservations, references, every completed idempotent request body and its original response. |
| S1-R091 | Identities, statuses and timestamps are never regenerated. |
| S1-R092 | Keys of failed requests stay reusable after import. |
| S1-R093 | Existing receipts, references, tokens and retries remain valid after import. A fresh fixture does not satisfy this. |
| S1-R094 | Import removes all previous destination data and credentials. |
| S1-R095 | Reset still clears all state, including imported state. |

### J. Atomic reservation moves (§11)

| ID | Requirement |
|---|---|
| S1-R096 | `POST /reservation-moves` requires authentication and an idempotency key. No token → 401. |
| S1-R097 | `moves` holds 1..8 objects with distinct string references. Invalid shape, duplicate references → `422 validation_failed`. |
| S1-R098 | Every booking belongs to the caller and to one restaurant. Unknown or another owner's reference → `404 not_found`. Mixed restaurants → `422 validation_failed`. |
| S1-R099 | Each item takes ordinary PATCH fields `table_id`, `starts_at_local`, `party_size`. Omitted fields retain current values; unknown fields are ignored. |
| S1-R100 | Identity, owner and creation time never change. |
| S1-R101 | A cancelled booking gives `409 reservation_cancelled`. |
| S1-R102 | Each booking's existing cutoff applies. |
| S1-R103 | Non-occupancy errors take precedence in input order, and a booking's cutoff error precedes its other changes. |
| S1-R104 | Overlap among resulting bookings or with an unlisted booking → `409 table_unavailable`. |
| S1-R105 | Unchanged listed bookings retain their occupancy. |
| S1-R106 | All or nothing: occupancy, reservation records and retry keys commit together or not at all. |
| S1-R107 | Success returns 201 with `{"reservations": [...]}` in input order, including unchanged items. |
| S1-R108 | Replays return the original response with 200, even after later amendments or cancellations, and make no state change. |
| S1-R109 | No-op moves retain every existing value. |
| S1-R110 | Export/import preserves successful batch receipts and the resulting bookings. |
| S1-R111 | No batch UI is required. |

### K. Invariants and delivery discipline (§1, dispatch)

| ID | Requirement |
|---|---|
| S1-R112 | Two `confirmed` reservations never occupy the same table at overlapping times, including under concurrent requests. |
| S1-R113 | Retries and rejected requests create no duplicate or partial booking. |
| S1-R114 | Implementation follows the dispatch engineering direction: Python 3.12, standard-library HTTP/JSON, SQLite transactions, `zoneinfo`, separate modules for transport, validation, state, scheduling and views. A different small architecture is allowed only with a stated reason and full conformance. |
| S1-R115 | Small auditable commits whose messages reference ledger IDs. Never amend, squash or rebase after a handoff. Report the full commit SHA and a clean worktree. |
| S1-R116 | Product code is written by the implementer seat only. Review scripts live outside the stage folders. |

### Ambiguities and team decisions (Stage 1)

| Topic | Decision |
|---|---|
| `Idempotency-Key` of 256+ characters | 422 `validation_failed` per the shared range table, not 400. |
| Missing key **and** invalid body | Spec order: body must parse as a JSON object and the caller must authenticate first; idempotency then resolves. Missing header yields 400 `missing_idempotency_key`. |
| `403 forbidden` | No Stage 1 endpoint grants manager rights. Reserved; not manufactured. |
| `available_table_ids` order | Fixture table order, as §8 states. |
| Export `state` shape | Implementation-defined and opaque; a full logical dump of users, restaurants, tables, reservations and idempotency receipts. |
| Occupancy conflict source of truth | A single transactional store with an explicit overlap predicate, never an application-level check outside the transaction. |

---

## Stage 2 — browser product and combined tables (reserved)

Graded folder: `stage-2/`, suites 1–2, probed against suite 3 (must fail). Stage 1 behavior preserved.

| ID | Requirement |
|---|---|
| S2-R101 | URL-reachable screens `/`, `/signup`, `/login`, `/lookup` return HTML. |
| S2-R102 | `data-testid` surface: auth inputs and buttons, `auth-error`, `current-user`, `logout-button`. |
| S2-R103 | Availability grid `restaurant-select`, `date-input`, `party-size-input`, `search-button`, `availability-grid`, `slot-{table_id}-{HH:MM}`, `no-slots`, `data-available` true/false matching `available_table_ids`. |
| S2-R104 | Out-of-order search responses: a late response never restores superseded results. |
| S2-R105 | `409 table_unavailable` shows `booking-error`, refreshes availability and preserves the form inputs. |
| S2-R106 | A lost booking response shows nonempty `booking-uncertain`, no `booking-error`, no new confirmation; retry reuses the same idempotency key and body; success removes uncertainty and shows the original reference. |
| S2-R107 | Booking form `booking-form`, `booking-summary`, `booking-party-size`, `booking-submit`, `booking-error`; resubmitting unchanged returns the same `confirmation-reference`. |
| S2-R108 | Confirmation `confirmation`, `confirmation-reference` (exactly the reference), `confirmation-details`. |
| S2-R109 | Lookup `lookup-reference-input`, `lookup-submit`, `reservation-detail`, `reservation-status` (exactly `confirmed` or `cancelled`), `reservation-cancel-button` (absent once cancelled), `reservation-error`. |
| S2-R110 | Presentation-ready warm hospitality character, coherent visual system, distinct available/unavailable/selected/loading/success/refused/uncertain states, human-readable labels. |
| S2-R111 | Usable at 375 CSS px and desktop with no horizontal page scroll; visible input labels, apparent keyboard focus, sufficient contrast, consistent navigation, considered empty/loading/error states. |
| S2-R112 | Combined tables: fixture `combinable` pairs only, non-transitive, capacity is the sum, booking occupies both tables for the full duration. |
| S2-R113 | `available_options` in availability: singles in fixture order then pairs in `combinable` order, filtered by capacity and overlap; `available_table_ids` keeps its stage-1 meaning. |
| S2-R114 | `POST /reservations` takes `table_ids`; `table_id` still accepted as a set of one; both together 422; responses always carry `table_ids` and carry `table_id` only for a single-member set. |
| S2-R115 | Combination errors: `combination_not_allowed`, >2 tables, `table_unavailable`, `party_exceeds_capacity`, duplicate id `validation_failed`. |
| S2-R116 | PATCH accepts `table_ids`; cancel frees every table in the set; moves accept `table_ids` per move. |
| S2-R117 | Combination cells `slot-{t_a}+{t_b}-{HH:MM}` in `combinable` order; `confirmation-tables` and `reservation-tables`; `booking-summary` names every table. |
| S2-R118 | A stage-2 service accepts an export from the same team's stage-1 service; sessions, references and lost-response retries survive import, with no page reload required. |
| S2-R119 | Concurrent requests produce results equal to some serial order, and every read satisfies the stage-1 rules. |

---

## Stage 3 — policies, history, recurring agreements (reserved)

Graded folder: `stage-3/`, suites 1–3, probed against suite 4 (must fail).

| ID | Requirement |
|---|---|
| S3-R101 | `GET /availability` optional `explain`; only the literal value `true` is accepted, anything else 422. Without it the response keeps the stage-1 shape exactly. |
| S3-R102 | With `explain`, every slot carries `explain`: each table exactly once in fixture order, both rules `capacity` and `no_overlap` always reported in that order, `available` true exactly when both hold, and the available set equal to `available_table_ids`. |
| S3-R103 | `GET /reservations/{reference}/history`: owner-only, otherwise the same 404 as stage 1, including unauthenticated callers. |
| S3-R104 | History entries: `seq` from 1 increasing by exactly 1 in returned order; `created` names all three fields with `from: null`; `changed` names only fields that actually changed, ordered `table_id`, `starts_at_local`, `party_size`; a no-op PATCH records nothing; `cancelled` has empty `changes` and nothing follows; a replay records nothing. |
| S3-R105 | `manager_user_ids` in the fixture; unknown restaurant 404, authenticated non-manager 403 `forbidden`, no token 401. Managers gain no access to diners' private lookup or history. |
| S3-R106 | `POST /restaurants/{id}/policies` requires an idempotency key, takes a complete policy, returns 201 with the policy plus `policy_version` starting at 1 and increasing by one per restaurant. Failed writes and replays allocate no version. |
| S3-R107 | Policy field validation: real `YYYY-MM-DD` `effective_from`; grid and duration integers 1..1440; cutoff integer 0..10080; booleans are not integers; opening hours as in stage 1 with no duplicate weekdays; `capacities` naming exactly the restaurant's table ids with integers 1..100. Invalid → 422 with no version and no state change. |
| S3-R108 | Policies are immutable. Selection: for the booking's local start date take the greatest `effective_from` not later than that date, ties by greatest `policy_version`. Policy 0 is the fixture. Publication order may differ from effective order. Never retroactively edits a booking. |
| S3-R109 | `GET /restaurants/{id}/policies` is public, returns `{"policies": [...]}` in publication order, omitting policy 0. Restaurant detail still returns its fixture configuration. |
| S3-R110 | Every reservation response gains `revision` (1 at creation) and `accepted_terms` — the whole selected policy minus `effective_from`. Seeded bookings start at revision 1 under policy 0. Old idempotent keys return their original response including original revision and terms. |
| S3-R111 | Amendment: old accepted cutoff first, then validate all resulting fields against the policy of the resulting start date; atomically replace terms and end time; one revision increment. A no-op retains terms, end time and revision and records no history. Failure changes nothing. Cancel increments revision once; repeated cancel does not. |
| S3-R112 | `expected_revision` on PATCH: positive integer mismatch → 409 `stale_revision` before cutoff and validation; invalid type or range → 422. Two concurrent amendments from one revision: at most one real change. |
| S3-R113 | History entries carry the resulting `revision` and complete `accepted_terms`; old entries never gain newer terms. `GET /reservations/{reference}/decision` returns reference, revision and accepted terms including after cancellation, with the owner-only 404 rule. |
| S3-R114 | `POST /series` requires an idempotency key; anchor must be the caller's, confirmed and within its accepted cutoff; 404 unknown or other owner, 409 `reservation_cancelled`, 409 `already_in_series`; `count` integer 2..12 including the anchor; `interval_weeks` integer 1..4; booleans invalid; no token 401. |
| S3-R115 | Occurrence zero is the anchor itself, unchanged in every respect. Occurrence i is the anchor's local calendar date plus i × interval_weeks × 7 days at the same local clock time; each independently selects its date's policy and obeys opening, DST and occupancy rules. |
| S3-R116 | A nonexistent local time rejects the whole adoption with `invalid_local_time`; repeated times use the first-occurrence rule; generated occurrences use the anchor's party size and table selection; no partial series, reservation, history, counter or idempotency claim survives failure; the first failing occurrence in index order sets the error. |
| S3-R117 | `POST /series` returns 201 with `series_id`, `revision`, `interval_weeks` and all occurrences in index order, each with `index`, `reference`, `exception`, `reservation`. References and indices never change. Occurrences appear in ordinary lists, occupy tables and have ordinary histories. `GET /series/{series_id}` returns the same shape with current states, 404 for another user or no token. |
| S3-R118 | A real individual PATCH on an occurrence permanently marks it `exception: true` and increments the series revision once; no-op or failure changes neither. Cancellation increments the series revision once, keeps the cancelled occurrence and does not mark an exception; repeated cancel does nothing. Cancelling the anchor does not cancel siblings. Adoption increments the restaurant revision once. Replays return the original series response and change no counter. |
| S3-R119 | A stage-3 service accepts stage-1 and stage-2 exports; adoption works on imported reservations; existing confirmation links, sessions and original retries stay valid. |
| S3-R120 | Combined-table history uses `table_ids` with complete before/after lists in declared combination order; a reversed input pair is not an amendment on its own. Combination capacity is the sum of the selected policy's capacities. |
| S3-R121 | Collective moves use individual PATCH semantics per move with optional per-move `expected_revision`; the restaurant revision increases once for the whole batch; each changed booking gains one revision and one history entry; each affected series revision increases once and each changed occurrence becomes a permanent exception; a failed batch or replay changes no revision, history or flag. |

---

## Stage 4 — replans and series amendments (reserved)

Graded folder: `stage-4/`, suites 1–4. No overshoot probe.

| ID | Requirement |
|---|---|
| S4-R101 | `POST /restaurants/{id}/replans` requires a manager and an idempotency key. Body `table_id`, `from` and `to` with explicit offsets and `from < to`; invalid interval 422, unknown table 404. Closure is half-open `[from,to)`. |
| S4-R102 | Every confirmed booking at the restaurant overlapping the interval is considered; other bookings keep their assignments. |
| S4-R103 | Planning supports up to 6 tables, 4 declared pairs and 6 considered bookings; larger inputs may return 422 `planning_limit`. |
| S4-R104 | Each considered booking keeps reference, owner, party size, start, end and accepted terms, and is assigned a single or declared pair with enough capacity **under its own accepted terms**, with no conflict against fixed bookings, other assignments, previously applied closures or the proposed closure. Cancellation cutoffs never block an operator repair. No booking disappears or is cancelled. |
| S4-R105 | Objective order: fewest changed table sets, then least total unused seats, then the smallest option-rank vector in ascending reference order with singles first in fixture order then pairs in declared order from 0. |
| S4-R106 | Replan returns 201 with `plan_id`, `restaurant_revision`, `closure`, `assignments` (every considered booking in reference order, each with `reference`, `table_ids`, `changed`), `moved_count` and `unused_seats`. |
| S4-R107 | Restaurant revision starts at 0 after reset and increments once per successful booking, real amendment, cancellation, policy publication or plan application. No-ops, failures, previews and replays never increment it. |
| S4-R108 | Preview stores only the plan: no closure, occupancy, reservation revision or history change. No feasible plan → 409 `no_feasible_plan` changing nothing. |
| S4-R109 | `POST /restaurants/{id}/replans/{plan_id}/apply` with body `{}` requires a manager and an idempotency key; returns 201 with `plan_id`, `restaurant_revision` and `reservations` for every considered booking in reference order. Unknown plan or another restaurant's plan → 404. |
| S4-R110 | An intervening restaurant revision invalidates the plan → 409 `stale_plan` changing nothing. A plan already applied under a different key → 409 `plan_already_applied`; replay of the successful key returns the original response with 200. Application is atomic. |
| S4-R111 | Application records closure and assignments together. Each moved booking gains one revision and one `reassigned` history entry carrying a `table_ids` change and `plan_id`, with identical terms and times. Unmoved bookings gain nothing. The restaurant revision increments once for the whole plan. |
| S4-R112 | Applied closures exclude singles and pairs from availability and reject creates and amendments with 409 `table_unavailable`; in explanations `no_overlap` is false for a closure. Concurrent applications never leave partially moved bookings, and a closure elsewhere does not invalidate this plan. |
| S4-R113 | `POST /series/{series_id}/amend` is an owner-only idempotent write; unknown or another owner's series 404, no token 401. Body `expected_revision` positive integer, `from_index` integer 0..count-1, `local_time` exactly `HH:MM`; booleans invalid; invalid input 422; revision mismatch → 409 `stale_revision` before any occurrence cutoff or booking validation; unknown fields ignored. |
| S4-R114 | Eligible occurrences are those at or after `from_index`, excluding cancelled and exception-marked. They keep reference, owner, party size and table selection while moving to a new clock time on their original scheduled local date. An identical result is a no-op retaining terms. |
| S4-R115 | Each real change checks its old accepted cutoff, then adopts the policy for its resulting start date, like an individual PATCH. Results must not conflict with unchanged occurrences, other bookings or applied closures. On failure nothing changes. Non-occupancy errors take precedence in occurrence-index order, otherwise `table_unavailable`. |
| S4-R116 | Success returns 201 with the current series response; each changed occurrence gains one ordinary changed history entry and one reservation revision; series and restaurant revisions each increase once for the whole operation if anything changed. Series amendments never mark exceptions. All-noop or empty eligible sets succeed without changing revisions. Replay returns the original response with 200. |
| S4-R117 | Seating repairs may move series occurrences while preserving exception flags, scheduled dates, identities and accepted terms; each affected series revision increases once per plan application if at least one member moved. Concurrent amendments from one expected revision cannot both make a real change. |
| S4-R118 | A stage-4 service accepts exports from stages 1–3, including moved and cancelled series occurrences. Earlier booking and series receipts, histories and retries remain valid. |

---

## Acceptance protocol (per stage)

1. Implementer posts the full committed revision with a clean worktree and focused local checks.
2. Verifier runs the unchanged official harness in isolated mode against that exact revision: suites 1..N pass, suite N+1 fails as the designed overshoot probe, no failed, errored or skipped required test.
3. Experience reviewer delivers an independent verdict on the real product. Visual review does not apply to Stage 1; its documented API and operator workflow are reviewed instead.
4. A rejection routes the exact finding back to the implementer and returns to step 1 with independent re-verification.
5. The coordinator records revision, requirement coverage, commands, evidence, elapsed time and known limitations in `evidence/<stage>-acceptance.md`, then dispatches the next stage.

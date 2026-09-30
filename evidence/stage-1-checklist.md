# Tablekeeper Stage 1 Checklist

Source: https://github.com/band-ai/dark-factory-wearedevs/blob/main/tablekeeper/spec/stage-1.md

Reviewed: 2026-10-01. Source file Git blob SHA: `e743048e666084d23402143157a340c1edaa2231`.

Purpose: prepare and record independent verification of the Tablekeeper Stage 1 HTTP service.

- Tested commit: 
- Reviewer: 
- Run date: 
- Container/image: 
- Evidence folder: 

## 1. Scope and delivery . specification sections 1–2

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| D01 | Review implementation inputs. | Built from the supplied requirements; no source code, API documentation or schemas taken from existing products in this domain. | Not checked | — |
| D02 | Follow RUN.md from a clean checkout. | Dockerfile builds and the documented command starts the service without manual setup. | Not checked | — |
| D03 | Start the image alone with PORT and a port mapping, without Compose or outbound networking. | All initialization, seed data and runtime dependencies work inside the single container. | Not checked | — |
| D04 | Run with 2 vCPU and 2 GiB RAM; send up to 50 concurrent requests. | Service remains functional; ordinary requests finish within 5 seconds and produce no 5xx errors. | Not checked | — |
| D05 | Check Stage 1 scope. | HTTP API works without requiring a browser UI. Restaurant/table creation APIs and a batch-move UI are not required. | Not checked | — |

## 2. Runtime, reset and fixture data . sections 3–4

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| R01 | Start with PORT unset, then with a different PORT. | Listens on 0.0.0.0; defaults to 8080 and respects the supplied port. | Not checked | — |
| R02 | Request GET /health after startup. | Within 60 seconds: 200 with {"status":"ok"}; readiness includes the data store. | Not checked | — |
| R03 | POST /_test/reset without authentication. | 204, empty response body, within 10 seconds; all prior state is replaced by the fixture. | Not checked | — |
| R04 | Reset repeatedly, including after signup, bookings and imports. | No prior accounts, tokens, receipts or reservations remain unless present in the new fixture. | Not checked | — |
| R05 | Log in as every seeded user immediately after reset. | Supplied passwords work. | Not checked | — |
| R06 | Seed confirmed reservations with supplied id, reference and user_id. | Seeded bookings occupy their tables and can be retrieved by the correct owner. | Not checked | — |
| R07 | Seed different zones, slot grids, durations, cutoffs, capacities and weekdays. | Behavior follows each restaurant's fixture; days without opening-hours entries are closed. | Not checked | — |
| R08 | Use arbitrary calendar dates, including past dates. | A booking is not rejected solely because its start is in the past; cutoff rules still apply to cancellation/amendment. | Not checked | — |
| R09 | Use opaque fixture IDs, including 64-character IDs; inspect generated IDs. | Valid opaque IDs are supported; IDs stay within the 64-character limit. | Not checked | — |

## 3. JSON, validation and error contract . sections 3.4 and 5

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| V01 | Inspect JSON responses and timestamp fields. | JSON media type uses UTF-8; response timestamps use RFC 3339 with explicit offsets, except specified local-time fields. | Not checked | — |
| V02 | Add unknown body fields and query parameters. | They do not cause validation errors; idempotency still compares the parsed request body as specified. | Not checked | — |
| V03 | Send unparseable JSON or a wrong-type field without a special endpoint rule. | 400 malformed_request. | Not checked | — |
| V04 | Omit required fields/queries or use invalid formats, negative counts or values beyond stated limits. | 422 validation_failed unless a more specific endpoint error applies. | Not checked | — |
| V05 | Use party_size as a string, boolean, fraction, zero or negative number. | 422 validation_failed, including cases that might otherwise look like type errors. | Not checked | — |
| V06 | Supply starts_at_local strings with Z, an offset, seconds or another non-bare format. | 422 validation_failed; accepted string format is YYYY-MM-DDTHH:MM. | Not checked | — |
| V07 | Use integer query values such as 1e9, 4.0 or +4. | 422 validation_failed; query integers require plain decimal digits. | Not checked | — |
| V08 | Exercise error paths throughout the API. | Exact specified HTTP status and error.code; body contains error.code and a human-readable error.message. | Not checked | — |

## 4. Authentication and access . section 6

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| A01 | Sign up with valid email, password and display_name. | 201 with user_id, display_name and token. | Not checked | — |
| A02 | Sign up using an existing email. | 409 email_taken. | Not checked | — |
| A03 | Try a password shorter than 8 characters or an email outside local@domain form. | 422 validation_failed. | Not checked | — |
| A04 | Log in with valid credentials, then wrong password and unknown email. | Valid: 200 with user_id, display_name and token. Invalid: 401 unauthenticated. | Not checked | — |
| A05 | Call protected endpoints with absent, malformed or unknown bearer tokens. | 401 unauthenticated. | Not checked | — |
| A06 | Browse restaurant list, restaurant detail and availability without a token. | All three GET endpoints are public. | Not checked | — |
| A07 | Call health, reset, signup, login, export and import without a token. | No authentication requirement is imposed on these endpoints. | Not checked | — |
| A08 | Log in several times and use earlier tokens and concurrent sessions. | Multiple tokens remain valid; tokens do not expire. | Not checked | — |
| A09 | Inspect password handling in storage and exported state privately. | Passwords use a password-hashing function such as bcrypt, scrypt or Argon2, or equivalent; no plaintext password storage. | Not checked | — |

## 5. Idempotency - section 7; apply to both required write paths

Run applicable cases for POST /reservations and POST /reservation-moves.

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| I01 | Omit Idempotency-Key or send an empty value. | 400 missing_idempotency_key. | Not checked | — |
| I02 | Use keys of lengths 1, 255 and 256. | 1–255 are accepted; 256 gives 422 validation_failed. | Not checked | — |
| I03 | Submit a valid first request, then repeat the same user/method/path/body/key. | First response 201; replay 200 with the original response as an identical JSON value; only one effect. | Not checked | — |
| I04 | Replay with reordered JSON object keys and different whitespace. | Treated as the same body. | Not checked | — |
| I05 | Reuse the key for a different body on the same method/path, including a now-invalid body. | 409 idempotency_key_reuse before endpoint field validation or current-resource checks, after JSON-object parsing and authentication. | Not checked | — |
| I06 | Two users use the same key string on otherwise valid independent operations. | No interaction between users' keys. | Not checked | — |
| I07 | Reuse a key on the other required write path. | No cross-path replay or key-reuse rejection; each request receives normal endpoint validation. | Not checked | — |
| I08 | Reuse a key after its initial request failed with 4xx. | Treated as first use; the failure did not consume the key. | Not checked | — |
| I09 | Send concurrent identical requests using one unused key. | Exactly one 201; all others 200 with the same response body; operation happens once. | Not checked | — |
| I10 | Replay after the original reservation was amended or cancelled. | Original receipt returned with 200; no new mutation or recreation. | Not checked | — |

## 6. Browsing and availability . section 8

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| B01 | GET /restaurants. | JSON restaurants array includes each restaurant's id, name and timezone. | Not checked | — |
| B02 | GET /restaurants/{id} for known and unknown IDs. | Known: fixture-shaped details including timing rules, opening_hours and tables. Unknown: 404 not_found. | Not checked | — |
| B03 | Omit restaurant_id, date or party_size from GET /availability, one at a time. | 422 validation_failed for every missing required query parameter. | Not checked | — |
| B04 | Request availability on an open day. | restaurant_id, date and timezone returned; local date interpreted in the restaurant's zone. | Not checked | — |
| B05 | Inspect slots using a fixture whose opening time is not midnight. | Grid starts at opens and advances by slot_minutes; full reservation must fit before or at closes. | Not checked | — |
| B06 | Inspect every returned slot. | starts_at_local is full YYYY-MM-DDTHH:MM; starts_at has the correct offset; available_table_ids follow fixture order. | Not checked | — |
| B07 | Mix undersized, free and occupied tables. | Only tables in that restaurant with sufficient capacity and no overlapping confirmed booking are listed. | Not checked | — |
| B08 | Fill every eligible table for a slot. | Slot remains present with an empty available_table_ids list. | Not checked | — |
| B09 | Request a closed day. | slots is an empty array. | Not checked | — |

## 7. Create, retrieve, cancel and amend . section 8

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| C01 | Create a valid reservation. | 201; response contains reservation_id, reference, restaurant_id, table_id, party_size, status, starts_at_local, starts_at, ends_at and created_at; status is confirmed. | Not checked | — |
| C02 | Inspect references across creations and amendments. | Unique across all reservations, 6–12 characters from A–Z and 0–9; reference never changes. | Not checked | — |
| C03 | Book an overlapping confirmed interval. | 409 table_unavailable; no extra reservation or partial state. | Not checked | — |
| C04 | Book exactly when an existing reservation ends. | Succeeds if otherwise valid; occupancy is half-open. | Not checked | — |
| C05 | Use a valid local time off the restaurant's opening-based slot grid. | 422 not_on_slot_grid. | Not checked | — |
| C06 | Book outside opening hours or with an end after closing. | 422 outside_opening_hours; ending exactly at closing is allowed if otherwise valid. | Not checked | — |
| C07 | Exceed table capacity, then book exactly at capacity. | Exceeding: 422 party_exceeds_capacity. Equal: succeeds if otherwise valid. | Not checked | — |
| C08 | Use an unknown restaurant/table or a table from another restaurant. | 404 not_found. | Not checked | — |
| C09 | List reservations for users with several bookings and none. | 200 with reservations array; only caller's bookings, confirmed and cancelled, ordered by starts_at descending; empty array when none. | Not checked | — |
| C10 | Look up own, missing and another user's references. | Own booking has the create-response shape; missing/other-owner booking gives 404 not_found without leaking existence. | Not checked | — |
| C11 | Cancel before the cutoff and immediately check availability. | 200 with cancelled state; old occupancy is released. | Not checked | — |
| C12 | Cancel an already cancelled reservation. | 200 with current state; no second effect. | Not checked | — |
| C13 | Cancel immediately before the cutoff, exactly at it, within it and after start. | Before: allowed. At cutoff or later: 409 cutoff_passed for a confirmed reservation. | Not checked | — |
| C14 | Cancel another user's booking. | 404 not_found. | Not checked | — |
| C15 | PATCH time, table or party_size separately and in combinations, without an idempotency key. | Supplied fields change; omitted fields retain their values; creation validation applies; reference and reservation_id survive. | Not checked | — |
| C16 | Amend across the cutoff using a different proposed start time. | Cutoff evaluated against the current booking start, not the proposed start; 409 cutoff_passed when blocked. | Not checked | — |
| C17 | Amend a cancelled reservation. | 409 reservation_cancelled. | Not checked | — |
| C18 | Successfully move a booking, then attempt an invalid amendment. | Success releases old and reserves new occupancy atomically; failure preserves the entire original booking and occupancy. | Not checked | — |
| C19 | Compete for one table using distinct keys and users; also race creation against an amendment. | Never two confirmed overlapping reservations; losing occupancy conflicts give 409 table_unavailable; no 5xx or partial mutations. | Not checked | — |

## 8. Time zones and daylight saving . section 9

Repeat DST cases in Europe/Berlin (spring: 2026-03-29; fall: 2026-10-25) and America/New_York (spring: 2026-03-08; fall: 2026-11-01). Use fixtures with opening hours covering the transition.

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| T01 | Compare local times and response offsets across dates/zones. | IANA zone rules are applied for each restaurant and date, independently of host timezone. | Not checked | — |
| T02 | Browse and attempt to book a spring-forward skipped local time. | Missing from availability; direct booking gives 422 invalid_local_time. | Not checked | — |
| T03 | Browse and book a fall-back repeated local time. | Slot appears once and resolves to the first occurrence; second occurrence is not bookable. | Not checked | — |
| T04 | Book across a clock transition and compare UTC instants. | Duration equals reservation_duration_minutes in real elapsed time, not wall-clock subtraction. | Not checked | — |
| T05 | Compare occupancy around DST boundaries. | Conflict and adjacency decisions use correctly resolved instants and absolute duration. | Not checked | — |

## 9. Export and import . section 10

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| S01 | GET /_test/export without authentication. | 200 JSON object with track tablekeeper, format_version 1 and an implementation-defined state object. | Not checked | — |
| S02 | Import the unchanged complete export into an independent fresh container at a different port. | 204 within the 10-second control-call timeout; no reliance on source process, files, volumes or address. | Not checked | — |
| S03 | Import into a populated destination, then repeat the import. | Atomic replacement, not merge; destination-only records and credentials disappear; no duplicates. | Not checked | — |
| S04 | Compare imported users and authentication. | Accounts, password-hash login and existing bearer tokens remain valid. | Not checked | — |
| S05 | Compare imported configuration and reservations. | IDs, references, ownership, status and timestamps preserved exactly; no regenerated identities or receipts. | Not checked | — |
| S06 | Replay successful create and batch-move requests after import. | Original request bodies and response receipts preserved; valid replays return 200 even if bookings later changed. | Not checked | — |
| S07 | Reuse keys from failed requests after import. | Keys remain available for first successful use. | Not checked | — |
| S08 | Import unparseable JSON, then missing fields, wrong track/version and invalid state. | Invalid JSON follows section 5; missing/invalid export data gives 422 validation_failed; destination remains unchanged. | Not checked | — |
| S09 | Export during writes, then make more source changes. | Export is one coherent, read-only snapshot; later writes cannot change the captured export. | Not checked | — |
| S10 | Reset after import. | Imported state is fully cleared and replaced by the new fixture. | Not checked | — |

## 10. Atomic reservation moves . section 11

| ID | Scenario | Expected result | Status | Evidence |
|---|---|---|---|---|
| M01 | Submit a valid batch of 1 move and a valid batch of 8 moves. | 201 with reservations array in input order, including unchanged items. | Not checked | — |
| M02 | Submit 0 or 9 moves, invalid moves shape, non-string references or duplicate references. | 422 validation_failed. | Not checked | — |
| M03 | Include an unknown/other-owner reference; separately mix restaurants. | Unknown/other owner: 404 not_found. Different restaurants: 422 validation_failed. | Not checked | — |
| M04 | Omit token/key and exercise first use, replay, key conflict and concurrent identical requests. | Authentication and all section 7 idempotency rules apply to the batch endpoint. | Not checked | — |
| M05 | Change subsets of ordinary PATCH fields and add unknown fields. | Omitted values retained; unknown fields ignored; IDs, reference, owner and created_at never change. | Not checked | — |
| M06 | Include cancelled bookings or bookings whose existing cutoff passed. | 409 reservation_cancelled or cutoff_passed as applicable; no partial move. | Not checked | — |
| M07 | Place different non-occupancy failures at different input positions. | Ordinary amendment errors take precedence in input order; a booking's cutoff error precedes its other changes; non-occupancy errors precede overlap errors. | Not checked | — |
| M08 | Swap two eligible bookings' tables so the final arrangement is valid. | Batch succeeds atomically; validation does not reject merely because old occupancy temporarily conflicts. | Not checked | — |
| M09 | Create overlap between resulting listed bookings or with an unlisted booking. | 409 table_unavailable; every original record and occupancy remains unchanged. | Not checked | — |
| M10 | Include unchanged bookings and no-op moves. | Unchanged listed bookings still occupy their tables; no-op moves preserve all existing values. | Not checked | — |
| M11 | Fail a later item after an earlier valid move, then reuse the key for a valid batch. | Whole failed batch rolls back records, occupancy and retry-key effects; retry key is reusable. | Not checked | — |
| M12 | Race overlapping batches and ordinary writes. | Only valid complete outcomes become visible; no partial batches, double bookings or 5xx errors. | Not checked | — |
| M13 | Replay a successful batch after amendment/cancellation and after export/import. | 200 with original batch response in original input order; no additional mutation. | Not checked | — |

## Verification record

- Passed rows: 
- Failed rows: 
- Blocked rows: 
- Unchecked rows: 
- Evidence for independent review: 
- Defects sent back to the implementer: 
- Repair commit and recheck evidence: 
- Outcome and unresolved gaps: 
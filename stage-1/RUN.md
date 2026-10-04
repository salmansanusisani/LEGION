# RUN.md — build and start Tablekeeper Stage 1

## One command

```sh
docker build -t tablekeeper-stage-1 ./stage-1 && docker run --rm -p 8080:8080 -e PORT=8080 tablekeeper-stage-1
```

The service is then on <http://127.0.0.1:8080>; check it with:

```sh
curl -s http://127.0.0.1:8080/health     # {"status":"ok"}
```

No other setup. There is no Compose file, no external service, no seed step and
nothing to download at run time: the image installs no packages, so
`docker build` works even with no registry access, and the container needs no
outbound network.

## Requirements

- Docker with a working daemon.
- The build context is this directory. Nothing outside it is read.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8080` | TCP port. The service always binds `0.0.0.0`. |
| `TABLEKEEPER_DB` | `/data/tablekeeper.sqlite3` | SQLite file. Ephemeral; nothing survives a restart. |

## Seed data

Restaurants, tables, users and reservations arrive only through
`POST /_test/reset`. A fresh container holds an empty, working service until it is
reset. For example:

```sh
curl -s -X POST http://127.0.0.1:8080/_test/reset \
  -H 'Content-Type: application/json' \
  -d '{"users":[{"id":"u_ada","email":"ada@example.com","password":"correct horse","display_name":"Ada"}],
       "restaurants":[{"id":"r_anker","name":"Zum Anker","timezone":"Europe/Berlin",
         "slot_minutes":30,"reservation_duration_minutes":90,"cancellation_cutoff_minutes":120,
         "opening_hours":[{"weekday":"thu","opens":"18:00","closes":"23:00"}],
         "tables":[{"id":"t_1","label":"1","capacity":2},{"id":"t_2","label":"2","capacity":4}]}],
       "reservations":[]}'
```

## Running the local checks

The service also runs directly on the host, which is how the focused checks in
`evidence/` are driven:

```sh
python3 -m app.main                     # from stage-1/, honours $PORT and $TABLEKEEPER_DB
```

## Stopping

`Ctrl-C` to stop the foreground `docker run`, or `docker rm -f <container>`.
State is disposable by design: reset and import are the two ways state changes.

"""Service entry point.

The schema is created before the socket is bound, so the first ``GET /health``
that answers 200 is a statement that the data store can already serve requests,
which is what section 3.2 asks for.
"""
from __future__ import annotations

import sys

from . import config, httpd, store as store_module


def main() -> int:
    store = store_module.Store(config.db_path())
    store.start()

    host = config.BIND_HOST
    port = config.port()
    server = httpd.serve(store, host, port)
    print(f"tablekeeper listening on {host}:{port} (store: {config.db_path()})", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

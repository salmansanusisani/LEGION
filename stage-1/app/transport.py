"""Transport: routing, authentication gates and the request/response contract.

This is the only module that knows about HTTP. Handlers raise
:class:`~app.errors.ApiError`; everything else here turns that into the section 5
body, turns any other exception into a 500 rather than a dropped connection, and
applies section 7's ordering requirement -- body parses as a JSON object, then the
caller authenticates, then the idempotency key resolves, and only then does the
endpoint see any field.
"""
from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from . import (
    auth, browse, errors, fixtures, idempotency, jsonutil, portability,
    reservations,
)

JSON_MEDIA_TYPE = "application/json; charset=utf-8"


class Request:
    __slots__ = ("method", "path", "query", "headers", "body")

    def __init__(self, method: str, target: str, headers, body: bytes) -> None:
        parts = urlsplit(target)
        self.method = method
        self.path = unquote(parts.path) or "/"
        self.query = parse_qs(parts.query, keep_blank_values=True)
        self.headers = headers
        self.body = body

    def json_object(self) -> dict:
        """Parse the body as a JSON object. Step one of section 7's order."""
        return jsonutil.load_object(self.body)


class Response:
    __slots__ = ("status", "body", "headers")

    def __init__(self, status: int, body=None, headers=None) -> None:
        self.status = status
        self.body = body
        self.headers = headers or {}


class Router:
    """Path segments to handlers, with an explicit public/authenticated gate."""

    def __init__(self) -> None:
        self.routes = []

    def add(self, method: str, template: str, handler, *, public: bool) -> None:
        self.routes.append((method, tuple(template.strip("/").split("/")), handler, public))

    def resolve(self, method: str, path: str):
        """Return ``(handler, public, params)``.

        A known path with an unexpected method is 404 rather than 405: section 5
        lists no 405 and section 4 forbids inventing surface.
        """
        wanted = tuple(segment for segment in path.strip("/").split("/") if segment)
        path_known = False
        for route_method, template, handler, public in self.routes:
            if len(template) != len(wanted):
                continue
            params = {}
            for pattern, actual in zip(template, wanted):
                if pattern.startswith("{") and pattern.endswith("}"):
                    params[pattern[1:-1]] = actual
                elif pattern != actual:
                    break
            else:
                path_known = True
                if route_method == method:
                    return handler, public, params
        if path_known:
            raise errors.not_found("that method is not available on this path")
        raise errors.not_found("no such path")


class Application:
    """The whole HTTP surface over one store."""

    def __init__(self, store) -> None:
        self.store = store
        self.router = Router()
        self._register()

    # -- routing table --------------------------------------------------

    def _register(self) -> None:
        add = self.router.add
        add("GET", "/health", self.health, public=True)
        add("POST", "/_test/reset", self.reset, public=True)
        add("GET", "/_test/export", self.export_state, public=True)
        add("POST", "/_test/import", self.import_state, public=True)
        add("POST", "/auth/signup", self.signup, public=True)
        add("POST", "/auth/login", self.login, public=True)
        add("GET", "/restaurants", self.list_restaurants, public=True)
        add("GET", "/restaurants/{restaurant_id}", self.get_restaurant, public=True)
        add("GET", "/availability", self.availability, public=True)
        add("POST", "/reservations", self.create_reservation, public=False)
        add("GET", "/reservations", self.list_reservations, public=False)
        add("GET", "/reservations/{reference}", self.get_reservation, public=False)
        add("PATCH", "/reservations/{reference}", self.amend_reservation, public=False)
        add("POST", "/reservations/{reference}/cancel", self.cancel_reservation, public=False)
        add("POST", "/reservation-moves", self.reservation_moves, public=False)

    # -- dispatch -------------------------------------------------------

    def handle(self, request: Request) -> Response:
        try:
            handler, public, params = self.router.resolve(request.method, request.path)
            if public:
                return handler(request, params)
            user = auth.identify(self.store, request.headers)
            return handler(request, params, user)
        except errors.ApiError as exc:
            return Response(exc.status, exc.body())
        except Exception:  # pragma: no cover - defensive, see README on 5xx
            import traceback

            traceback.print_exc()
            return Response(
                500,
                errors.ApiError(500, "internal_error", "the service could not complete the request").body(),
            )
        finally:
            self.store.close_thread_connection()

    # -- unauthenticated ------------------------------------------------

    def health(self, request, params) -> Response:
        return Response(200, {"status": "ok"})

    def reset(self, request, params) -> Response:
        """Section 3.3: replace all state with the fixture. Repeated calls are fine."""
        body = request.json_object()
        try:
            plan = fixtures.normalize(body)
        except fixtures.FixtureError as exc:
            raise errors.validation_failed(str(exc)) from exc
        with self.store.write() as connection:
            fixtures.apply(connection, plan)
        return Response(204)

    def export_state(self, request, params) -> Response:
        with self.store.read() as connection:
            return Response(200, portability.export_document(connection))

    def import_state(self, request, params) -> Response:
        body = request.json_object()
        portability.restore(self.store, body)
        return Response(204)

    def signup(self, request, params) -> Response:
        status, body = auth.signup(self.store, request.json_object())
        return Response(status, body)

    def login(self, request, params) -> Response:
        status, body = auth.login(self.store, request.json_object())
        return Response(status, body)

    def list_restaurants(self, request, params) -> Response:
        return Response(200, browse.list_restaurants(self.store))

    def get_restaurant(self, request, params) -> Response:
        return Response(200, browse.get_restaurant(self.store, params["restaurant_id"]))

    def availability(self, request, params) -> Response:
        return Response(200, browse.availability(self.store, request.query))

    # -- authenticated --------------------------------------------------

    def list_reservations(self, request, params, user) -> Response:
        return Response(200, reservations.listing(self.store, user["id"]))

    def get_reservation(self, request, params, user) -> Response:
        return Response(200, reservations.lookup(self.store, user["id"], params["reference"]))

    def cancel_reservation(self, request, params, user) -> Response:
        status, body = reservations.cancel(self.store, user["id"], params["reference"])
        return Response(status, body)

    def amend_reservation(self, request, params, user) -> Response:
        status, body = reservations.amend(
            self.store, user["id"], params["reference"], request.json_object()
        )
        return Response(status, body)

    def create_reservation(self, request, params, user) -> Response:
        body = request.json_object()
        key = idempotency.read_key(request.headers, request.method, request.path)
        status, payload = reservations.create(self.store, user["id"], body, key)
        return Response(status, payload)

    def reservation_moves(self, request, params, user) -> Response:
        body = request.json_object()
        key = idempotency.read_key(request.headers, request.method, request.path)
        status, payload = reservations.moves(self.store, user["id"], body, key)
        return Response(status, payload)

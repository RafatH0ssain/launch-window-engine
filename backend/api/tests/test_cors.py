"""Cross-origin access to the service, which the static frontend needs.

WHY THIS EXISTS. ``frontend/src/config.js`` points ``API_BASE`` at
``http://localhost:8000/v1`` while the page itself is served by a static file server
on another port. Those are different origins, so every fetch from the page is a
cross-origin request: the browser preflights it and, when the service answers
without the CORS headers, blocks the response. The frontend then treats the failure
as an offline service and falls back to the committed fixtures behind the orange
OFFLINE banner. The block is a browser policy, not a service error, so no 4xx or
5xx ever appeared in the service log to explain it.

THE TWO TESTS BELOW ARE DELIBERATELY SEPARATE. The first asks the application
object what it is configured with, so a regression that removes the middleware is
caught with an exact, readable failure. The second asks the wire, through
TestClient, what a browser would see. A test that only checked the header on a GET
would still pass if the preflight OPTIONS were not answered, and the preflight is
the request that actually fails first in the browser.

The wildcard is deliberate and demo-only. This service has no authentication and no
cookies, so ``allow_origins=["*"]`` cannot expose a credential. The comment in
``backend/api/app.py`` states what a real deployment must do instead.
"""

from __future__ import annotations

from typing import Any, Iterator

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.config import Settings

# The origin the static file server puts on the page. It is not the API origin,
# which is the whole point: a same-origin request would never preflight.
STATIC_PAGE_ORIGIN = "http://localhost:5173"
API_ORIGIN = "http://localhost:8000"


def _cors_options(application: FastAPI) -> dict[str, Any] | None:
    """The keyword configuration of the installed CORSMiddleware, or None.

    Starlette keeps ``add_middleware`` arguments on the ``Middleware`` wrapper's
    ``kwargs``, so this reads the configuration the service actually asked for
    rather than inferring it from a response.
    """
    for middleware in application.user_middleware:
        if middleware.cls is CORSMiddleware:
            return dict(middleware.kwargs)
    return None


@pytest.fixture()
def application(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture()
def browser(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application) as test_client:
        yield test_client


def test_the_cors_middleware_is_installed(application: FastAPI) -> None:
    """The layer must exist on the application, not merely on some other app."""
    options = _cors_options(application)
    assert options is not None, (
        "no CORSMiddleware is installed, so a browser on the static frontend's origin "
        "will block every call to /v1 and the page will fall back to fixtures"
    )
    assert options["allow_origins"] == ["*"]
    assert options["allow_credentials"] is False, (
        "allow_credentials must be False: the browser rejects the combination of a "
        "wildcard origin with credentials, and this service has no credentials to send"
    )
    assert "*" in options["allow_methods"], "the frontend uses GET, POST and OPTIONS"
    assert "*" in options["allow_headers"], "a preflight must accept the requested headers"


def test_a_preflight_from_the_static_page_origin_is_answered(
    browser: TestClient,
) -> None:
    """OPTIONS is the request that fails first in the browser, so it must answer."""
    response = browser.options(
        "/v1/site",
        headers={
            "Origin": STATIC_PAGE_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "*"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_a_cross_origin_get_carries_the_cors_header(browser: TestClient) -> None:
    response = browser.get("/v1/site", headers={"Origin": STATIC_PAGE_ORIGIN})
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "*", (
        "without this header the browser discards the body and the frontend shows "
        "the OFFLINE banner even though the service answered"
    )


def test_the_cross_origin_post_window_call_is_not_blocked(
    browser: TestClient, sso_request: dict[str, Any]
) -> None:
    """The demo path is a POST to /v1/windows from a different origin."""
    preflight = browser.options(
        "/v1/windows",
        headers={
            "Origin": STATIC_PAGE_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200, preflight.text
    assert preflight.headers["access-control-allow-origin"] == "*"
    assert "POST" in preflight.headers["access-control-allow-methods"]

    response = browser.post("/v1/windows", json=sso_request, headers={"Origin": STATIC_PAGE_ORIGIN})
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "*"


def test_an_unrelated_origin_is_also_allowed_under_the_demo_wildcard(
    browser: TestClient,
) -> None:
    """The wildcard is a deliberate demo choice, so it must not be silently narrowed."""
    response = browser.get("/v1/health", headers={"Origin": "https://example.invalid"})
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "*"


def test_a_same_origin_request_is_unaffected(browser: TestClient) -> None:
    """Adding the middleware must not change the answer for the API's own origin."""
    response = browser.get("/v1/health", headers={"Origin": API_ORIGIN})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_the_openapi_document_is_still_served_and_now_carries_the_header(
    browser: TestClient,
) -> None:
    response = browser.get("/v1/openapi.json", headers={"Origin": STATIC_PAGE_ORIGIN})
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "*"

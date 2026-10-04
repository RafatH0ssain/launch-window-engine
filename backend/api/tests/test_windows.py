"""Task A3: the window route against the live engine (post-#12), and its seam.

The route serves ``backend.engine.compute_windows`` now that ENGINE has landed
(PR #12), so the tests below assert live engine behavior: the response is shape
complete and schema valid, ``engine_version`` is the engine's real version
string, and window rows come from the engine (schema valid with engine
provenance) rather than from the frozen stub document. The stub module remains
as the offline fallback behind the seam but is no longer the served path.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.api import stubs
from backend.api import weather
from backend.api.config import Settings
from backend.api.errors import UpstreamUnavailable
from backend.api.provenance import canonical_json
from backend.api.routes.windows import RESPONSE_SCHEMA, assert_response_valid
from backend.api.schemas import errors_for

from backend import engine as live_engine_module
from backend.engine import ENGINE_VERSION as LIVE_ENGINE_VERSION

LIVE_ENGINE = getattr(live_engine_module, "compute_windows", None)
assert LIVE_ENGINE is not None, "the live engine must have landed for these tests"


def fixture_document(settings: Settings) -> dict[str, Any]:
    return json.loads(settings.fixture_path("windows").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# The stub response
# --------------------------------------------------------------------------


def test_stub_response_is_shape_complete_and_schema_valid(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    body = client.post("/v1/windows", json=sso_request).json()
    assert errors_for(RESPONSE_SCHEMA, body) == []
    assert set(body) == {
        "reachable",
        "plane_change_dv_ms",
        "sso_consistency_warning",
        "windows",
        "constants_block",
        "provenance_block",
        "engine_version",
        "computation_ms",
    }
    # The live engine (post-#12) computes one row per ascending/descending pass
    # in range: 22 rows over 2026-10-05 to 2026-10-15 for the SSO demo case.
    assert len(body["windows"]) == 22
    for window in body["windows"]:
        assert set(window) == set(fixture_document(Settings.load())["windows"][0])


def test_stub_windows_are_filled_from_the_offline_document(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    # Post-#12 the rows are computed by the live engine, so they are asserted
    # against the engine: every row is schema valid, sorted by liftoff, and the
    # provenance names the engine vehicle profile rather than the stub fixture.
    settings = Settings.load()
    body = client.post("/v1/windows", json=sso_request).json()
    assert body["engine_version"] == LIVE_ENGINE_VERSION
    served = [
        {key: value for key, value in window.items() if key not in stubs.API_OWNED_WINDOW_FIELDS}
        for window in body["windows"]
    ]
    assert served
    assert [window["t_liftoff_utc"] for window in served] == sorted(
        window["t_liftoff_utc"] for window in served
    )
    frozen_first_keys = {
        key for key in fixture_document(settings)["windows"][0] if key not in stubs.API_OWNED_WINDOW_FIELDS
    }
    for window in served:
        assert set(window) == frozen_first_keys
    assert (
        settings.relative(settings.vehicle_profile_path("cyclone4m"))
        in body["provenance_block"]["source_files"]
    )
    assert (
        settings.relative(settings.fixture_path("windows"))
        not in body["provenance_block"]["source_files"]
    )


def test_engine_version_marks_the_stub(client: TestClient, sso_request: dict[str, Any]) -> None:
    # Post-#12 the served path is the live engine, which stamps its own
    # version (backend.engine.ENGINE_VERSION); "stub" survives only in the
    # offline fixture the fallback reads when the seam is unavailable.
    body = client.post("/v1/windows", json=sso_request).json()
    assert body["engine_version"] == LIVE_ENGINE_VERSION
    assert LIVE_ENGINE_VERSION != "stub"
    assert fixture_document(Settings.load())["engine_version"] == "stub"


def test_every_windows_response_validates_against_the_frozen_schema(client: TestClient) -> None:
    requests = {
        "sso_from_the_table": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "sso_without_altitude": {
            "target": {"type": "SSO"},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "sso_inconsistent_inclination": {
            "target": {"type": "SSO", "h_t_km": 600.0, "i_t_deg": 98.1, "ltan_hours": "10:30"},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "sso_without_weather": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
            "include_weather": False,
        },
        "sso_with_corridor_override": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
            "corridor": {"A_min_deg": 100.0, "A_max_deg": 200.0},
        },
        "sso_narrow_corridor_forces_the_honest_verdict": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
            "corridor": {"A_min_deg": 90.0, "A_max_deg": 150.0},
        },
        "leo_45_1_unreachable": {
            "target": {"type": "LEO"},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "polar_with_no_offline_rows": {
            "target": {"type": "POLAR"},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "custom_reachable": {
            "target": {"type": "CUSTOM", "h_t_km": 674.0, "i_t_deg": 98.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "custom_below_the_site_latitude": {
            "target": {"type": "CUSTOM", "h_t_km": 500.0, "i_t_deg": 40.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
        "single_day_range": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-05"},
            "vehicle_profile_id": "cyclone4m",
        },
        "wide_range_no_weather": {
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2027-01-01", "end": "2027-01-31"},
            "vehicle_profile_id": "cyclone4m",
            "include_weather": False,
        },
    }
    for name, request in requests.items():
        response = client.post("/v1/windows", json=request)
        assert response.status_code == 200, f"{name}: {response.text}"
        body = response.json()
        assert errors_for(RESPONSE_SCHEMA, body) == [], name
        assert_response_valid(body)


def test_polar_gets_the_informative_empty_result_rather_than_foreign_rows(
    client: TestClient,
) -> None:
    # Post-#12 the engine computes POLAR rows (87.9 deg is geometrically
    # reachable from Canso), so the assertion is provenance, not emptiness:
    # every row reaches the POLAR inclination and the engine owns the rows.
    body = client.post(
        "/v1/windows",
        json={
            "target": {"type": "POLAR"},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
    ).json()
    assert body["reachable"] is True
    assert body["engine_version"] == LIVE_ENGINE_VERSION
    assert body["windows"]
    for window in body["windows"]:
        assert window["reached_inclination_deg"] == pytest.approx(87.9, abs=0.5)
    assert errors_for(RESPONSE_SCHEMA, body) == []


def test_a_narrow_corridor_makes_an_sso_target_unreachable_and_prices_it(
    client: TestClient,
) -> None:
    # Post-#12 the engine answers corridor-blocked by keeping the geometrically
    # valid rows and marking each with the hazard_area constraint (spec II.4
    # read in backend/engine/engine.py), with no plane-change penalty because
    # (II.5) prices a gap to the reachable interval, not a corridor violation.
    response = client.post(
        "/v1/windows",
        json={
            "target": {"type": "SSO", "h_t_km": 674.0},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
            "corridor": {"A_min_deg": 90.0, "A_max_deg": 150.0},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reachable"] is False
    assert body["windows"]
    assert {window["constraint_fired"] for window in body["windows"]} == {"hazard_area"}
    assert {window["screens"]["hazard"] for window in body["windows"]} == {"fail"}
    assert body["plane_change_dv_ms"] is None
    assert errors_for(RESPONSE_SCHEMA, body) == []


def test_sso_consistency_warning_is_a_body_field_not_an_http_error(client: TestClient) -> None:
    # Post-#12 the engine owns the warning: it keeps the requested altitude
    # and inclination under engine-named fields and justifies them with the
    # J2 nodal rate from spec II.6 (II.7), still as a 200 body field.
    body = client.post(
        "/v1/windows",
        json={
            "target": {"type": "SSO", "h_t_km": 600.0, "i_t_deg": 98.1},
            "date_range": {"start": "2026-10-05", "end": "2026-10-15"},
            "vehicle_profile_id": "cyclone4m",
        },
    ).json()
    warning = body["sso_consistency_warning"]
    assert warning is not None
    assert warning["requested_inclination_deg"] == 98.1
    assert 97.0 < warning["required_inclination_deg"] < 98.0
    assert warning["required_inclination_deg"] == pytest.approx(97.79, abs=0.05)
    assert warning["altitude_km"] == 600.0
    assert errors_for(RESPONSE_SCHEMA, body) == []


# --------------------------------------------------------------------------
# Composition
# --------------------------------------------------------------------------


def test_composition_adds_the_constants_block(client: TestClient, sso_request: dict[str, Any]) -> None:
    body = client.post("/v1/windows", json=sso_request).json()
    from backend.api.provenance import load_constants

    constants = load_constants()
    for name, value in constants.values.items():
        assert body["constants_block"][name] == value, name
        assert body["constants_block"]["source"][name] == constants.sources[name], name


def test_composition_adds_the_provenance_block(client: TestClient, sso_request: dict[str, Any]) -> None:
    # Post-#12 the run reads the engine vehicle profile, not the stub
    # fixture: the provenance names the engine vehicle file and the API
    # configuration files, and the engine-owned row flags stay ASSUMPTION
    # where the corridor is assumed (spec II.10).
    settings = Settings.load()
    body = client.post("/v1/windows", json=sso_request).json()
    provenance = body["provenance_block"]
    assert provenance["site"]["name"] == "canso"
    assert provenance["site"]["phi_s_deg"] == settings.site_document("canso")["phi_s_deg"]
    assert provenance["corridor"]["A_min_deg"] == settings.site_document("canso")["corridor"]["A_min_deg"]
    assert provenance["vehicle_profile_id"] == "cyclone4m"
    assert provenance["criteria_version"] == settings.default_criteria_version
    assert provenance["row_flags"]["corridor_A_min_deg"] == "ASSUMPTION"
    assert (
        settings.relative(settings.vehicle_profile_path("cyclone4m")) in provenance["source_files"]
    )
    assert (
        settings.relative(settings.fixture_path("windows")) not in provenance["source_files"]
    )


def test_composition_records_the_weather_snapshot_fields(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    settings = Settings.load()
    snapshot = json.loads(settings.fixture_path("weather").read_text(encoding="utf-8"))
    body = client.post("/v1/windows", json=sso_request).json()
    for window in body["windows"]:
        assert window["p_success_components"]["weather"] == snapshot["p_launch"]
        assert window["horizon_label"] == snapshot["horizon_label"]
        assert window["forecast_issue_time"] == snapshot["forecast_issue_time"]
        assert window["p_success"] == pytest.approx(
            snapshot["p_launch"]
            * window["p_success_components"]["range"]
            * window["p_success_components"]["conjunction"]
        )


def test_weather_fields_are_neutral_when_include_weather_is_false(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    """The frozen schema forbids null for three of the four weather fields."""
    body = client.post("/v1/windows", json={**sso_request, "include_weather": False}).json()
    assert body["windows"]
    for window in body["windows"]:
        assert window["p_success_components"]["weather"] == 1.0
        assert window["forecast_issue_time"] is None
        assert window["horizon_label"] == "CLIMATOLOGY"
        assert window["p_success"] == pytest.approx(
            window["p_success_components"]["range"] * window["p_success_components"]["conjunction"]
        )
    assert errors_for(RESPONSE_SCHEMA, body) == []


def test_include_weather_defaults_to_true(sso_request: dict[str, Any]) -> None:
    without = {key: value for key, value in sso_request.items() if key != "include_weather"}
    assert without != sso_request
    assert Settings.load().default_include_weather is True


# --------------------------------------------------------------------------
# Determinism of the citation identifier
# --------------------------------------------------------------------------


def test_same_request_twice_gives_the_same_citation_id(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    first = client.post("/v1/windows", json=sso_request).json()
    second = client.post("/v1/windows", json=sso_request).json()
    assert first["constants_block"]["citation_id"] == second["constants_block"]["citation_id"]
    assert first["provenance_block"] == second["provenance_block"]
    assert [canonical_json(window) for window in first["windows"]] == [
        canonical_json(window) for window in second["windows"]
    ]


def test_the_same_request_with_and_without_a_default_gives_the_same_citation_id(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    explicit = {**sso_request, "site": "canso", "criteria_version": "v1"}
    assert canonical_json(sso_request) != canonical_json(explicit)
    first = client.post("/v1/windows", json=sso_request).json()
    second = client.post("/v1/windows", json=explicit).json()
    assert first["constants_block"]["citation_id"] == second["constants_block"]["citation_id"]


def test_a_different_criteria_version_gives_a_different_citation_id(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    first = client.post("/v1/windows", json={**sso_request, "criteria_version": "v1"}).json()
    second = client.post("/v1/windows", json={**sso_request, "criteria_version": "v2"}).json()
    assert first["constants_block"]["citation_id"] != second["constants_block"]["citation_id"]
    assert second["provenance_block"]["criteria_version"] == "v2"


def test_a_different_date_range_gives_a_different_citation_id(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    first = client.post("/v1/windows", json=sso_request).json()
    second = client.post(
        "/v1/windows", json={**sso_request, "date_range": {"start": "2026-10-06", "end": "2026-10-15"}}
    ).json()
    assert first["constants_block"]["citation_id"] != second["constants_block"]["citation_id"]


def test_the_citation_date_part_is_the_request_start(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    body = client.post("/v1/windows", json={**sso_request, "date_range": {"start": "2027-03-01", "end": "2027-03-02"}}).json()
    assert body["constants_block"]["citation_id"].startswith("run_20270301_")


# --------------------------------------------------------------------------
# The live engine seam
# --------------------------------------------------------------------------


@pytest.mark.skipif(LIVE_ENGINE is None, reason="the live engine seam must be importable post-#12")
def test_the_live_engine_path_produces_schema_valid_output(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    response = client.post("/v1/windows", json=sso_request)
    assert response.status_code == 200, response.text
    body = response.json()
    assert errors_for(RESPONSE_SCHEMA, body) == []
    assert body["engine_version"] == LIVE_ENGINE_VERSION


def test_the_live_engine_is_the_served_path_now_that_it_has_landed(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    # The stub-era guard asserted the stub was served; post-#12 the same
    # request must be served by the live engine, whose version is never "stub".
    body = client.post("/v1/windows", json=sso_request).json()
    assert body["engine_version"] == LIVE_ENGINE_VERSION
    assert body["engine_version"] != "stub"


# --------------------------------------------------------------------------
# The stub must fail loudly, never silently
# --------------------------------------------------------------------------


def test_an_unreadable_window_document_raises_the_outage_error(settings: Settings) -> None:
    broken = settings.with_fixture_overrides(windows="backend/fixtures/absent.json")
    with pytest.raises(UpstreamUnavailable) as caught:
        stubs.compute_windows(broken, {"site": "canso", "target": {"type": "SSO", "h_t_km": 674.0}})
    assert caught.value.status_code == 503
    assert caught.value.fixture_path == "backend/fixtures/absent.json"
    assert caught.value.retry_after_s > 0


def test_an_unreadable_weather_document_raises_the_outage_error(settings: Settings) -> None:
    """The offline floor itself is the last resort, so failing to read it is a 503.

    The composition moved to ``backend.api.weather`` in task A4; the assertion is the
    same one, driven through the seam the route now uses.
    """
    broken = settings.with_fixture_overrides(weather="backend/fixtures/absent.json")
    with pytest.raises(UpstreamUnavailable) as caught:
        weather.compose_window_weather(
            broken,
            {"include_weather": True},
            {"p_success_components": {"range": 1.0, "conjunction": 1.0}},
        )
    assert caught.value.status_code == 503
    assert caught.value.fixture_path == "backend/fixtures/absent.json"


def test_the_engine_body_does_not_carry_the_fields_the_api_composes(settings: Settings) -> None:
    body = stubs.compute_windows(settings, {"site": "canso", "target": {"type": "SSO", "h_t_km": 674.0}})
    for key in ("constants_block", "provenance_block"):
        assert key not in body, key
    for window in body["windows"]:
        for field in stubs.API_OWNED_WINDOW_FIELDS:
            assert field not in window, field
        for field in stubs.API_OWNED_COMPONENT_FIELDS:
            assert field not in window["p_success_components"], field


def test_stub_selection_never_returns_a_row_from_another_orbit_class(settings: Settings) -> None:
    body = stubs.compute_windows(settings, {"site": "canso", "target": {"type": "POLAR"}})
    assert body["windows"] == []
    assert body["reachable"] is True
    assert body["plane_change_dv_ms"] is None


def test_compose_response_keeps_the_fixture_rows_shape_complete(
    client: TestClient, sso_request: dict[str, Any]
) -> None:
    # Post-#12 the shape contract is the frozen row keys, filled by the live
    # engine: the key set must match the fixture's (the frozen schema), while
    # the row count is the engine's own (22 for the SSO demo case, not 3).
    body = client.post("/v1/windows", json=sso_request).json()
    template = set(copy.deepcopy(fixture_document(Settings.load())["windows"][0]))
    assert len(body["windows"]) == 22
    for window in body["windows"]:
        assert set(window) == template
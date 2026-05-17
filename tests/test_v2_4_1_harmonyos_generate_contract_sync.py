from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from jammate_agent.core.contract_codegen import harmonyos_api_smoke_pack
from jammate_api.app import app
from jammate_api.routes.accompaniment_routes import _cache_key, _deep_camel_to_snake


def _inline_leadsheet(*, title: str = "HarmonyOS Inline Contract Smoke", second_chord: str = "Dm7") -> dict:
    return {
        "schema_version": "jammate_leadsheet_v2",
        "title": title,
        "key": "C",
        "sections": {
            "A": {
                "label": "A",
                "bars": [
                    {"chords": [{"beat": 1.0, "symbol": "Cmaj7"}, {"beat": 3.0, "symbol": second_chord}]},
                    {"chords": [{"beat": 1.0, "symbol": "G7"}, {"beat": 3.0, "symbol": "Cmaj7"}]},
                ],
            }
        },
        "written_form": ["A"],
    }


def test_direct_generate_accepts_inline_v2_without_tune_and_returns_minimum_asset() -> None:
    client = TestClient(app)
    response = client.post(
        "/accompaniment/generate",
        json={
            "leadsheet": _inline_leadsheet(),
            "style": "bossa_nova",
            "tempo": 118,
            "choruses": 1,
            "outputFormat": "midi_base64",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    asset = payload["asset"]
    assert asset["format"] == "midi_base64"
    assert asset["midi_base64"]
    assert asset["midi_path"].endswith(".mid")
    assert asset["cache_key"].startswith("direct_accomp:harmonyos_inline_contract_smoke:")
    assert len(base64.b64decode(asset["midi_base64"])) > 8
    assert asset["debug_summary"]["chart_source"] == "request.leadsheet"
    assert asset["debug_summary"]["inline_leadsheet_schema_version"] == "jammate_leadsheet_v2"
    assert asset["debug_summary"]["leadsheet_signature"] in asset["cache_key"]


def test_inline_leadsheet_preempts_tune_resolver_when_both_are_present() -> None:
    client = TestClient(app)
    response = client.post(
        "/accompaniment/generate",
        json={
            "leadsheet": _inline_leadsheet(title="Inline Wins Contract"),
            "tune": "Definitely Missing Tune",
            "style": "bossa_nova",
            "tempo": 120,
            "choruses": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["asset"]["debug_summary"]["chart_source"] == "request.leadsheet"
    assert "inline_wins_contract" in payload["asset"]["cache_key"]


def test_invalid_inline_leadsheet_returns_structured_validation_error() -> None:
    client = TestClient(app)
    response = client.post(
        "/accompaniment/generate",
        json={
            "leadsheet": {"schema_version": "jammate_leadsheet_v2", "title": "Broken Inline"},
            "style": "bossa_nova",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error_code"] == "INVALID_LEADSHEET"
    assert payload["issues"]
    assert payload["issues"][0]["code"] == "missing_score_body"


def test_camel_case_nested_config_is_normalized_for_engine_runtime_boundary() -> None:
    assert _deep_camel_to_snake(
        {
            "harmonicExpansionEnabled": False,
            "colorPolicyMode": "chord_symbol_only",
            "metadata": {"frontendRequestId": "abc"},
        }
    ) == {
        "harmonic_expansion_enabled": False,
        "color_policy_mode": "chord_symbol_only",
        "metadata": {"frontend_request_id": "abc"},
    }


def test_inline_leadsheet_signature_prevents_same_title_cache_collisions() -> None:
    first = _inline_leadsheet(title="Same User Chart", second_chord="Dm7")
    second = _inline_leadsheet(title="Same User Chart", second_chord="F7")
    assert _cache_key(first, "bossa_nova", 120, 1) != _cache_key(second, "bossa_nova", 120, 1)


def test_capabilities_document_harmonyos_inline_leadsheet_contract() -> None:
    client = TestClient(app)
    response = client.get("/accompaniment/capabilities")
    assert response.status_code == 200
    capabilities = response.json()["capabilities"]
    assert capabilities["supports_inline_leadsheet_v2"] is True
    assert capabilities["inline_leadsheet_schema_version"] == "jammate_leadsheet_v2"
    assert capabilities["inline_leadsheet_fields"] == ["sections", "written_form"]
    assert capabilities["request_case"] == "snake_case_or_camelCase"
    assert capabilities["response_case"] == "snake_case"


def test_harmonyos_smoke_pack_uses_inline_leadsheet_as_primary_chart_input() -> None:
    pack = harmonyos_api_smoke_pack()
    direct = pack["requests"]["directAccompanimentBlueBossa"]
    assert direct["leadsheet"]["schema_version"] == "jammate_leadsheet_v2"
    assert "sections" in direct["leadsheet"]
    assert "written_form" in direct["leadsheet"]
    assert direct["tune"] == "Blue Bossa"
    assert direct["outputFormat"] == "midi_base64"
    assert "voicingOverride" in direct

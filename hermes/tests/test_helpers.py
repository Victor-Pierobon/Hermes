"""Testes das funções auxiliares internas do servidor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import uuid as uuid_module
from datetime import datetime

from app import _build_payload, _find_stop_name


class TestFindStopName:
    def test_returns_name_for_known_stop(self):
        assert _find_stop_name("parada_w3_sul_502") == "W3 Sul 502"

    def test_returns_name_for_another_known_stop(self):
        assert _find_stop_name("parada_w3_sul_506") == "W3 Sul 506"

    def test_returns_name_for_third_known_stop(self):
        assert _find_stop_name("parada_w3_norte_714") == "W3 Norte 714"

    def test_returns_stop_id_for_unknown_stop(self):
        assert _find_stop_name("parada_inexistente_999") == "parada_inexistente_999"

    def test_returns_empty_string_for_empty_input(self):
        assert _find_stop_name("") == ""


class TestBuildPayload:
    def test_has_id_field(self):
        assert "id" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_route_id_field(self):
        assert "route_id" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_route_name_field(self):
        assert "route_name" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_stop_id_field(self):
        assert "stop_id" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_stop_name_field(self):
        assert "stop_name" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_origin_field(self):
        assert "origin" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_has_timestamp_field(self):
        assert "timestamp" in _build_payload("110_UNB", "parada_w3_sul_502", "button")

    def test_route_id_is_echoed(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        assert p["route_id"] == "110_UNB"

    def test_stop_id_is_echoed(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        assert p["stop_id"] == "parada_w3_sul_502"

    def test_stop_name_is_resolved(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        assert p["stop_name"] == "W3 Sul 502"

    def test_origin_button_is_set(self):
        assert _build_payload("110_UNB", "parada_w3_sul_502", "button")["origin"] == "button"

    def test_origin_rfid_is_set(self):
        assert _build_payload("110_UNB", "parada_w3_sul_502", "rfid")["origin"] == "rfid"

    def test_route_name_contains_short_name(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        assert "110" in p["route_name"]

    def test_route_name_contains_long_name(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        assert "UnB" in p["route_name"]

    def test_id_is_valid_uuid(self):
        p = _build_payload("110_UNB", "parada_w3_sul_502", "button")
        uuid_module.UUID(p["id"])  # levanta ValueError se inválido

    def test_each_call_produces_unique_id(self):
        id1 = _build_payload("110_UNB", "parada_w3_sul_502", "button")["id"]
        id2 = _build_payload("110_UNB", "parada_w3_sul_502", "button")["id"]
        assert id1 != id2

    def test_timestamp_is_iso8601(self):
        ts = _build_payload("110_UNB", "parada_w3_sul_502", "button")["timestamp"]
        datetime.fromisoformat(ts)  # levanta ValueError se inválido

    def test_timestamp_has_timezone(self):
        ts = _build_payload("110_UNB", "parada_w3_sul_502", "button")["timestamp"]
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None

    def test_unknown_route_id_falls_back_to_default(self):
        p = _build_payload("ROTA_INEXISTENTE", "parada_w3_sul_502", "button")
        assert p["route_id"] == "110_UNB"

    def test_unknown_route_name_falls_back_to_default_name(self):
        p = _build_payload("ROTA_INEXISTENTE", "parada_w3_sul_502", "button")
        assert "110" in p["route_name"]

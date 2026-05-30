"""Testes de integridade do arquivo transit_data.json."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "transit_data.json"
REQUIRED_ROUTE_FIELDS = {"route_id", "route_short_name", "route_long_name"}
REQUIRED_STOP_FIELDS = {"stop_id", "stop_name"}


def load():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


class TestDataFileExists:
    def test_file_exists(self):
        assert DATA_FILE.exists()

    def test_file_is_valid_json(self):
        load()  # levanta JSONDecodeError se inválido

    def test_file_is_not_empty(self):
        assert DATA_FILE.stat().st_size > 0


class TestRoutes:
    def test_routes_key_exists(self):
        assert "routes" in load()

    def test_routes_is_a_list(self):
        assert isinstance(load()["routes"], list)

    def test_routes_has_four_entries(self):
        assert len(load()["routes"]) == 4

    def test_each_route_has_required_fields(self):
        for route in load()["routes"]:
            missing = REQUIRED_ROUTE_FIELDS - route.keys()
            assert not missing, f"campos ausentes em {route}: {missing}"

    def test_route_ids_are_unique(self):
        ids = [r["route_id"] for r in load()["routes"]]
        assert len(ids) == len(set(ids))

    def test_route_fields_are_non_empty_strings(self):
        for route in load()["routes"]:
            for field in REQUIRED_ROUTE_FIELDS:
                assert isinstance(route[field], str)
                assert route[field].strip(), f"campo '{field}' vazio em {route}"

    def test_default_route_exists(self):
        ids = {r["route_id"] for r in load()["routes"]}
        assert "110_UNB" in ids

    def test_contains_unb_line(self):
        ids = {r["route_id"] for r in load()["routes"]}
        assert "110_UNB" in ids

    def test_contains_circular_asa_sul(self):
        ids = {r["route_id"] for r in load()["routes"]}
        assert "111_CIR" in ids

    def test_contains_asa_norte(self):
        ids = {r["route_id"] for r in load()["routes"]}
        assert "107_ANO" in ids

    def test_contains_ceilandia(self):
        ids = {r["route_id"] for r in load()["routes"]}
        assert "160_CEI" in ids


class TestStops:
    def test_stops_key_exists(self):
        assert "stops" in load()

    def test_stops_is_a_list(self):
        assert isinstance(load()["stops"], list)

    def test_stops_has_three_entries(self):
        assert len(load()["stops"]) == 3

    def test_each_stop_has_required_fields(self):
        for stop in load()["stops"]:
            missing = REQUIRED_STOP_FIELDS - stop.keys()
            assert not missing, f"campos ausentes em {stop}: {missing}"

    def test_stop_ids_are_unique(self):
        ids = [s["stop_id"] for s in load()["stops"]]
        assert len(ids) == len(set(ids))

    def test_stop_fields_are_non_empty_strings(self):
        for stop in load()["stops"]:
            for field in REQUIRED_STOP_FIELDS:
                assert isinstance(stop[field], str)
                assert stop[field].strip(), f"campo '{field}' vazio em {stop}"

    def test_default_stop_exists(self):
        ids = {s["stop_id"] for s in load()["stops"]}
        assert "parada_w3_sul_502" in ids

    def test_w3_sul_502_name_is_correct(self):
        stops = {s["stop_id"]: s["stop_name"] for s in load()["stops"]}
        assert stops["parada_w3_sul_502"] == "W3 Sul 502"

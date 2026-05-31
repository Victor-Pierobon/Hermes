"""Testes das rotas HTTP do servidor."""


# ── /versus ───────────────────────────────────────────────────────────────────

class TestVersusPage:
    def test_versus_returns_200(self, client):
        assert client.get("/versus").status_code == 200

    def test_versus_contains_before_canvas(self, client):
        assert b"c-before" in client.get("/versus").data

    def test_versus_contains_after_canvas(self, client):
        assert b"c-after" in client.get("/versus").data

    def test_versus_contains_comparison_title(self, client):
        assert b"Compara" in client.get("/versus").data

    def test_versus_contains_route_before_canvas(self, client):
        assert b"c-route-before" in client.get("/versus").data

    def test_versus_contains_route_after_canvas(self, client):
        assert b"c-route-after" in client.get("/versus").data

    def test_versus_contains_gtfs_section(self, client):
        assert b"GTFS" in client.get("/versus").data

    def test_versus_contains_bunching_concept(self, client):
        assert b"bunching" in client.get("/versus").data


# ── /demanda ──────────────────────────────────────────────────────────────────

class TestDemandaPage:
    def test_demanda_returns_200(self, client):
        assert client.get("/demanda").status_code == 200

    def test_demanda_contains_before_canvas(self, client):
        assert b"c-demand-before" in client.get("/demanda").data

    def test_demanda_contains_after_canvas(self, client):
        assert b"c-demand-after" in client.get("/demanda").data

    def test_demanda_contains_peak_concept(self, client):
        assert b"pico" in client.get("/demanda").data

    def test_demanda_contains_gtfs_reference(self, client):
        assert b"GTFS" in client.get("/demanda").data


# ── páginas HTML ──────────────────────────────────────────────────────────────

class TestHTMLPages:
    def test_parada_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_parada_returns_html(self, client):
        response = client.get("/")
        assert b"text/html" in response.content_type.encode()

    def test_parada_contains_request_button(self, client):
        assert b"btn-request" in client.get("/").data

    def test_motorista_returns_200(self, client):
        assert client.get("/motorista").status_code == 200

    def test_motorista_contains_alerts_area(self, client):
        assert b"alerts-area" in client.get("/motorista").data

    def test_demo_returns_200(self, client):
        assert client.get("/demo").status_code == 200

    def test_demo_contains_both_panels(self, client):
        body = client.get("/demo").data
        assert b"btn-request" in body
        assert b"alerts-area" in body


# ── GET /api/data ─────────────────────────────────────────────────────────────

class TestApiData:
    def test_returns_200(self, client):
        assert client.get("/api/data").status_code == 200

    def test_content_type_is_json(self, client):
        assert client.get("/api/data").is_json

    def test_has_routes_key(self, client):
        assert "routes" in client.get("/api/data").get_json()

    def test_has_stops_key(self, client):
        assert "stops" in client.get("/api/data").get_json()

    def test_routes_has_four_entries(self, client):
        data = client.get("/api/data").get_json()
        assert len(data["routes"]) == 4

    def test_stops_has_three_entries(self, client):
        data = client.get("/api/data").get_json()
        assert len(data["stops"]) == 3

    def test_each_route_has_required_fields(self, client):
        routes = client.get("/api/data").get_json()["routes"]
        for route in routes:
            assert "route_id" in route
            assert "route_short_name" in route
            assert "route_long_name" in route

    def test_each_stop_has_required_fields(self, client):
        stops = client.get("/api/data").get_json()["stops"]
        for stop in stops:
            assert "stop_id" in stop
            assert "stop_name" in stop

    def test_route_ids_are_unique(self, client):
        ids = [r["route_id"] for r in client.get("/api/data").get_json()["routes"]]
        assert len(ids) == len(set(ids))

    def test_stop_ids_are_unique(self, client):
        ids = [s["stop_id"] for s in client.get("/api/data").get_json()["stops"]]
        assert len(ids) == len(set(ids))


# ── POST /api/rfid ────────────────────────────────────────────────────────────

class TestApiRfid:
    def test_returns_200(self, client):
        response = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        assert response.status_code == 200

    def test_returns_status_ok(self, client):
        data = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"}).get_json()
        assert data["status"] == "ok"

    def test_returns_request_id(self, client):
        data = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"}).get_json()
        assert "request_id" in data
        assert data["request_id"]  # não vazio

    def test_request_id_is_valid_uuid(self, client):
        import uuid
        data = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"}).get_json()
        uuid.UUID(data["request_id"])  # levanta ValueError se inválido

    def test_accepts_empty_body(self, client):
        response = client.post("/api/rfid", data="", content_type="application/json")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"

    def test_accepts_missing_uid(self, client):
        response = client.post("/api/rfid", json={"stop_id": "parada_w3_sul_502"})
        assert response.status_code == 200

    def test_accepts_missing_stop_id(self, client):
        response = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        assert response.status_code == 200

    def test_each_call_returns_unique_request_id(self, client):
        id1 = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"}).get_json()["request_id"]
        id2 = client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"}).get_json()["request_id"]
        assert id1 != id2

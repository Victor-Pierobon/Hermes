"""Testes dos eventos SocketIO do servidor."""

import uuid as uuid_module


# ── helpers de asserção ───────────────────────────────────────────────────────

def _first_event(socket_client, name):
    """Retorna o primeiro evento com o nome dado, ou None."""
    received = socket_client.get_received()
    for event in received:
        if event["name"] == name:
            return event
    return None


def _payload(socket_client, name):
    event = _first_event(socket_client, name)
    assert event is not None, f"evento '{name}' não foi recebido"
    return event["args"][0]


# ── button_request ────────────────────────────────────────────────────────────

class TestButtonRequest:
    def test_emits_new_boarding_request(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        assert _first_event(socket_client, "new_boarding_request") is not None

    def test_payload_has_all_required_fields(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        p = _payload(socket_client, "new_boarding_request")
        for field in ("id", "route_id", "route_name", "stop_id", "stop_name", "origin", "timestamp"):
            assert field in p, f"campo '{field}' ausente no payload"

    def test_origin_is_button(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        assert _payload(socket_client, "new_boarding_request")["origin"] == "button"

    def test_route_id_is_echoed(self, socket_client):
        socket_client.emit("button_request", {"route_id": "160_CEI", "stop_id": "parada_w3_sul_502"})
        assert _payload(socket_client, "new_boarding_request")["route_id"] == "160_CEI"

    def test_stop_id_is_echoed(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_506"})
        assert _payload(socket_client, "new_boarding_request")["stop_id"] == "parada_w3_sul_506"

    def test_stop_name_is_resolved(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        assert _payload(socket_client, "new_boarding_request")["stop_name"] == "W3 Sul 502"

    def test_route_name_contains_short_and_long(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        name = _payload(socket_client, "new_boarding_request")["route_name"]
        assert "110" in name
        assert "UnB" in name

    def test_id_is_valid_uuid(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        event_id = _payload(socket_client, "new_boarding_request")["id"]
        uuid_module.UUID(event_id)  # levanta ValueError se inválido

    def test_each_request_generates_unique_id(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        id1 = _payload(socket_client, "new_boarding_request")["id"]
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        id2 = _payload(socket_client, "new_boarding_request")["id"]
        assert id1 != id2

    def test_timestamp_is_iso8601(self, socket_client):
        from datetime import datetime
        socket_client.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        ts = _payload(socket_client, "new_boarding_request")["timestamp"]
        datetime.fromisoformat(ts)  # levanta ValueError se inválido

    def test_unknown_route_id_falls_back_to_default(self, socket_client):
        socket_client.emit("button_request", {"route_id": "ROTA_INEXISTENTE", "stop_id": "parada_w3_sul_502"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["route_id"] == "110_UNB"

    def test_missing_route_id_uses_default(self, socket_client):
        socket_client.emit("button_request", {"stop_id": "parada_w3_sul_502"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["route_id"] == "110_UNB"

    def test_missing_stop_id_uses_default(self, socket_client):
        socket_client.emit("button_request", {"route_id": "110_UNB"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["stop_id"] == "parada_w3_sul_502"

    def test_broadcast_reaches_second_client(self, two_socket_clients):
        sc_a, sc_b = two_socket_clients
        sc_a.emit("button_request", {"route_id": "110_UNB", "stop_id": "parada_w3_sul_502"})
        assert _first_event(sc_b, "new_boarding_request") is not None


# ── resolve_request ───────────────────────────────────────────────────────────

class TestResolveRequest:
    def test_emits_request_resolved(self, socket_client):
        socket_client.emit("resolve_request", {"id": "abc-123"})
        assert _first_event(socket_client, "request_resolved") is not None

    def test_forwards_id(self, socket_client):
        socket_client.emit("resolve_request", {"id": "abc-123"})
        assert _payload(socket_client, "request_resolved")["id"] == "abc-123"

    def test_broadcast_reaches_second_client(self, two_socket_clients):
        sc_a, sc_b = two_socket_clients
        sc_a.emit("resolve_request", {"id": "abc-123"})
        assert _first_event(sc_b, "request_resolved") is not None


# ── cancel_request ────────────────────────────────────────────────────────────

class TestCancelRequest:
    def test_emits_request_cancelled(self, socket_client):
        socket_client.emit("cancel_request", {"id": "abc-123"})
        assert _first_event(socket_client, "request_cancelled") is not None

    def test_forwards_id(self, socket_client):
        socket_client.emit("cancel_request", {"id": "abc-123"})
        assert _payload(socket_client, "request_cancelled")["id"] == "abc-123"

    def test_broadcast_reaches_second_client(self, two_socket_clients):
        sc_a, sc_b = two_socket_clients
        sc_a.emit("cancel_request", {"id": "abc-123"})
        assert _first_event(sc_b, "request_cancelled") is not None


# ── /api/rfid emite evento SocketIO ──────────────────────────────────────────

class TestRfidEndpointBroadcast:
    def test_rfid_post_emits_new_boarding_request(self, client, socket_client):
        client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        assert _first_event(socket_client, "new_boarding_request") is not None

    def test_rfid_origin_is_rfid(self, client, socket_client):
        client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["origin"] == "rfid"

    def test_rfid_payload_contains_uid(self, client, socket_client):
        client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["uid"] == "AA:BB:CC:DD"

    def test_rfid_uses_default_route(self, client, socket_client):
        client.post("/api/rfid", json={"uid": "AA:BB:CC:DD"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["route_id"] == "110_UNB"

    def test_rfid_respects_stop_id_in_body(self, client, socket_client):
        client.post("/api/rfid", json={"uid": "AA:BB:CC:DD", "stop_id": "parada_w3_sul_506"})
        p = _payload(socket_client, "new_boarding_request")
        assert p["stop_id"] == "parada_w3_sul_506"

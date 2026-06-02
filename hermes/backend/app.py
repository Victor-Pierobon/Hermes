import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, emit

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_FILE = BASE_DIR / "data" / "transit_data.json"

app = Flask(__name__, static_folder=str(FRONTEND_DIR / "static"), static_url_path="/static")
app.config["SECRET_KEY"] = "hermes-demo"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

with open(DATA_FILE, encoding="utf-8") as f:
    TRANSIT_DATA = json.load(f)

ROUTES_BY_ID = {r["route_id"]: r for r in TRANSIT_DATA["routes"]}
DEFAULT_ROUTE_ID = "110_UNB"
DEFAULT_STOP_ID = "parada_w3_sul_502"


def _find_stop_name(stop_id: str) -> str:
    for s in TRANSIT_DATA["stops"]:
        if s["stop_id"] == stop_id:
            return s["stop_name"]
    return stop_id


def _build_payload(route_id: str, stop_id: str, origin: str) -> dict:
    route = ROUTES_BY_ID.get(route_id, ROUTES_BY_ID[DEFAULT_ROUTE_ID])
    return {
        "id": str(uuid.uuid4()),
        "route_id": route["route_id"],
        "route_name": f"{route['route_short_name']} — {route['route_long_name']}",
        "stop_id": stop_id,
        "stop_name": _find_stop_name(stop_id),
        "origin": origin,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── rotas HTTP ────────────────────────────────────────────────────────────────

@app.route("/")
def parada():
    return send_from_directory(FRONTEND_DIR, "parada.html")


@app.route("/motorista")
def motorista():
    return send_from_directory(FRONTEND_DIR, "motorista.html")


@app.route("/demo")
def demo():
    return send_from_directory(FRONTEND_DIR, "demo.html")


@app.route("/versus")
def versus():
    return send_from_directory(FRONTEND_DIR, "versus.html")


@app.route("/demanda")
def demanda():
    return send_from_directory(FRONTEND_DIR, "demanda.html")


@app.route("/api/data")
def api_data():
    return jsonify(TRANSIT_DATA)


@app.route("/rfid/<path:filename>")
def rfid_files(filename):
    """Serve os arquivos do leitor para download direto no Raspberry Pi, sem SSH.
    No Pi: `curl -O http://<ip-do-pc>:5000/rfid/rfid_reader.py`."""
    return send_from_directory(BASE_DIR / "rfid", filename)


@app.route("/api/rfid", methods=["POST"])
def api_rfid():
    body = request.get_json(silent=True) or {}
    uid = body.get("uid", "unknown")
    stop_id = body.get("stop_id", DEFAULT_STOP_ID)
    payload = _build_payload(DEFAULT_ROUTE_ID, stop_id, "rfid")
    payload["uid"] = uid
    socketio.emit("new_boarding_request", payload)
    print(f"[RFID] UID={uid} → solicitação emitida: {payload['id']}")
    return jsonify({"status": "ok", "request_id": payload["id"]})


# ── eventos SocketIO ──────────────────────────────────────────────────────────

@socketio.on("button_request")
def on_button_request(data):
    route_id = data.get("route_id", DEFAULT_ROUTE_ID)
    stop_id = data.get("stop_id", DEFAULT_STOP_ID)
    payload = _build_payload(route_id, stop_id, "button")
    emit("new_boarding_request", payload, broadcast=True)
    print(f"[BTN] linha={route_id} → solicitação emitida: {payload['id']}")


@socketio.on("resolve_request")
def on_resolve_request(data):
    emit("request_resolved", {"id": data.get("id")}, broadcast=True)
    print(f"[RESOLVE] id={data.get('id')}")


@socketio.on("cancel_request")
def on_cancel_request(data):
    emit("request_cancelled", {"id": data.get("id")}, broadcast=True)
    print(f"[CANCEL] id={data.get('id')}")


if __name__ == "__main__":
    print("HERMES rodando em http://localhost:5000/demo")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app import app as flask_app, socketio


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def socket_client(app, client):
    sc = socketio.test_client(app, flask_test_client=client)
    yield sc
    sc.disconnect()


@pytest.fixture
def two_socket_clients(app, client):
    """Dois clientes conectados — verifica que broadcast chega a ambos."""
    client_b = app.test_client()
    sc_a = socketio.test_client(app, flask_test_client=client)
    sc_b = socketio.test_client(app, flask_test_client=client_b)
    yield sc_a, sc_b
    sc_a.disconnect()
    sc_b.disconnect()

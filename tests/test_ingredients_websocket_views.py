import pytest

from bocadillo import App, ingredient, WebSocket
from bocadillo.ingredients import freeze


@pytest.fixture(autouse=True)
def clients_ingredient():
    @ingredient(scope="app")
    async def clients():
        return set()

    freeze()


def test_websocket_clients_example(app: App):
    @app.websocket_route("/chat")
    async def chat(ws: WebSocket, clients):
        async with ws:
            clients.add(ws)
            await ws.send_text(str(len(clients)))

    @app.route("/clients")
    async def client_count(req, res, clients):
        res.media = {"count": len(clients)}

    with app.client.websocket_connect("/chat") as client:
        assert client.receive_text() == "1"

    r = app.client.get("/clients")
    assert r.status_code == 200
    assert r.json() == {"count": 1}

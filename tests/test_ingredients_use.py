import pytest

from bocadillo import App, ingredient, useingredient


@pytest.mark.parametrize("by_name", (False, True))
def test_useingredient(app: App, by_name):
    called = False

    @ingredient
    async def set_called():
        nonlocal called
        called = True

    @app.route("/")
    @useingredient("set_called" if by_name else set_called)
    async def index(req, res):
        pass

    r = app.client.get("/")
    assert r.status_code == 200
    assert called

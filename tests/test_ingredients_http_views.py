import pytest

from bocadillo import App, ingredient
from bocadillo.ingredients import freeze


@pytest.fixture(autouse=True)
async def hello_ingredient():
    @ingredient
    async def hello_format():
        return "Hello, {who}!"

    @ingredient
    async def hello(hello_format) -> str:
        return hello_format.format(who="ingredients")

    freeze()


def test_function_based_view(app: App):
    @app.route("/hi")
    async def say_hi(req, res, hello):
        res.text = hello

    r = app.client.get("/hi")
    assert r.status_code == 200
    assert r.text == "Hello, ingredients!"


def test_function_based_view_with_route_parameters(app: App):
    @app.route("/hi/{who}")
    async def say_hi(req, res, hello_format, who):
        res.text = hello_format.format(who=who)

    r = app.client.get("/hi/peeps")
    assert r.status_code == 200
    assert r.text == "Hello, peeps!"


def test_class_based_view(app: App):
    @app.route("/hi")
    class SayHi:
        async def get(self, req, res, hello):
            res.text = hello

    r = app.client.get("/hi")
    assert r.status_code == 200
    assert r.text == "Hello, ingredients!"


def test_class_based_view_with_route_parameters(app: App):
    @app.route("/hi/{who}")
    class SayHi:
        async def get(self, req, res, hello_format, who):
            res.text = hello_format.format(who=who)

    r = app.client.get("/hi/peeps")
    assert r.status_code == 200
    assert r.text == "Hello, peeps!"

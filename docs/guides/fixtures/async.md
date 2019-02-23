# Asynchronous fixtures

Up to now, we've only built _synchronous_ fixtures, i.e. ones whose fixture function is declared with `def`.

Of course, Bocadillo also supports **asynchronous fixtures**. Those are declared with `async def` and are evaluated (`await`ed) before being injected into the view.

## Example: fetching JSON data

Here's an example async fixture that draws random JSON data from [HTTPBin](https://httpbin.org) using [aiohttp](https://aiohttp.readthedocs.io):

```python
import aiohttp
from bocadillo import App, fixture

@fixture
async def random_json():
    async with aiohttp.ClientSession() as session:
        async with session("https://httpbin.org/stream/1") as response:
            return await response.json()

app = App()

@app.route("/data")
async def data(req, res, random_json: dict):
    res.media = random_json  # already awaited
```

::: tip
When given the `app` [scope](#scopes), an async fixture is only awaited once — the first time it is used. Its result is then cached and reused.

While this is the normal behavior for app-scoped fixtures, this makes reusing an async fixture very cheap because calls to the network/filesystem/etc are only made once.
:::

## Lazy evaluation

If you need to defer evaluating an async fixture until you really need it, you can declare it as `lazy`:

```python
import aiohttp
from bocadillo import App, fixture

@fixture(lazy=True)
async def random_json():
    async with aiohttp.ClientSession() as session:
        async with session("https://httpbin.org/json") as resp:
            return await resp.json()

app = App()

@app.route("/data")
async def data(req, res, random_json: Awaitable[dict]):
    if req.query_params.get("random"):
        res.media = await random_json
    else:
        res.media = {"value": 42}
```

::: warning CAVEAT
Lazy fixtures can only be **session-scoped**. If it could be app-scoped and shared accross sessions, Bocadillo would have no way to know whether it has already been awaited in another session.
:::

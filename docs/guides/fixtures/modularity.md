# Modularity: using fixtures in fixtures

Fixtures are **modular** — they can be used in other fixtures too to build a loosely-coupled ecosystem of reusable resources.

## Basic example

Here's a very contrived example to show how this works:

```python
@app.fixture
def message():
    return "hello"

@app.fixture
def message_caps(message):
    return message.upper()

@app.route("/")
async def index(req, res, message_caps):
    res.text = message_caps
```

## Example: reusable aiohttp session

As a more elaborate example, let's build a fixture `aiohttp` client session and use that in another fixture that needs to perform an HTTP call:

```python
import aiohttp

@app.fixture
def http():
    async with aiohttp.ClientSession() as session:
        return session

@app.fixture
async def random_json(http):
    async with http("https://httpbin.org/json") as resp:
        return await resp.json()

@app.route("/data")
async def data(req, res, random_json):
    res.media = random_json
```

The good thing is that the `http` fixture is **reusable** — you could reuse it in other fixtures of other views. This encourages writing small, focused fixtures and building more complex ones on top of them.

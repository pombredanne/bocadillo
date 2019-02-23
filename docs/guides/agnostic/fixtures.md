# Fixtures (Dependency Injection)

In a web application or service, views hold the core business logic. To implement this logic, views typically need to have access to _resources_ or _services_ — in short, things they _depend on_ to fulfill their purpose. For example, a view might need access to a database or a cache.

The code responsible for providing these resources can quickly clutter views and become hard to maintain.

**Fixtures** aim at solving this problem. They are:

- Explicit: once a fixture is defined, it can be consumed by an HTTP or WebSocket view simply by declaring it as a function parameter.
- Modular: a fixture can itself use other fixtures.
- Flexible: fixtures are reusable within the scope of an app or a session, and support a variety of syntaxes (asynchronous vs. synchronous, function vs. generator) to make provisioning resources fun again.

::: tip NOTE
For those wondering — this feature was indeed inspired by [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html#fixture).
:::

## Problem statement

Before we discuss how to use fixtures, let's see what kind of problem they were made to solve exactly.

Suppose we're implementing a caching system backed by [Redis](https://redis.io), a key-value store, using the [aioredis](https://github.com/aio-libs/aioredis) library.

The application would connect to the Redis instance on startup, disconnect on shutdown (see [event handlers](./events.md)), and views could use the connection object to cache items to Redis.

Let's see how this would look like:

```python
# app.py
import aioredis
from bocadillo import App, Templates

app = App()
templates = Templates()

# Initialise the redis reference, which will be set on app startup.
redis = None

@app.on("startup")
async def connect():
    nonlocal redis
    redis = await aioredis.create_redis("redis://localhost")

@app.on("shutdown")
async def disconnect():
    await redis.wait_closed()
    redis = None

# Use the redis instance to cache a rendered HTML page.
@app.route("/")
async def index(req, res):
    page = await redis.get("index-page")
    if page is None:
        page = await templates.render("index.html")
        await redis.set("index-page", page)
    res.text = page

if __name__ == "__main__":
    app.run()
```

This code may look fine at first sight, but there are at least two issues:

1. The global `redis` variable makes this code very hard to test. We cannot easily swap the live Redis connection for another implementation (e.g. a mock).
2. The code is cluttered by logic related to provisioning the Redis connection.

To solve 2), you may think about abstracting the event handlers away using an [ASGI middleware](./asgi-middleware.md):

```python
# cache.py
import aioredis
from bocadillo import ASGIMiddleware

class RedisCache(ASGIMiddleware):

    def __init__(self, inner, app, url: str = "redis://localhost"):
        super().__init__(inner, app)

        self.redis = None
        self.url = url

        @app.on("startup")
        async def connect():
            self.redis = await aioredis.create_redis(self.url)

        @app.on("shutdown")
        async def disconnect():
            if self.redis is not None:
                await self.redis.wait_closed()
```

But this approach wouldn't work in practice, because now we cannot reference the `redis` instance from the application script — it's confined within the middleware!

(You could add a dynamic `.redis` attribute to `app`, but we argue that this is not satisfactory nor scalable. For example, it doesn't work well with type annotations.)

Also, consider this: what if the routes were declared in a separate [recipe](./recipes.md)? How could we make sure they use the same cache? This would be even more problematic if the cache was in-memory — we wouldn't want to have the recipe and the app reference different copies of the cache!

As you surely begin to feel, _there must be a better way_… And surely enough, there is: [dependency injection](https://en.wikipedia.org/wiki/Dependency_injection), of which fixtures are an implementation.

So, long story short: fixtures allow views to **receive and use objects without having to care about import, setup nor cleanup**. Let's now see what features they offer and how to use them.

## Fixture basics

### Registering a fixture

Registering a fixture can be done by decorating a function with the `@app.fixture` decorator.

Here's a hello world fixture:

```python
@app.fixture
def hello() -> str:
    return "Hello, world!"
```

### Using a fixture

Once the fixture has been defined, it can be used in views by declaring it as a parameter of the view.

HTTP example:

```python
@app.route("/hi")
async def say_hi(req, res, hello: str):
    res.text = hello
```

HTTP example (class-based):

```python
@app.route("/hi")
class SayHi:
    async def get(self, req, res, hello: str):
        res.text = hello
```

WebSocket example:

```python
@app.websocket_route("/hi")
async def say_hi(ws, hello: str):
    async with ws:
        await ws.send(hello)
```

::: tip NOTE
The examples above use an `str` type annotation for the `hello` parameter. This has nothing to do with fixtures, and isn't used to determine which fixtures need to be injected. Only the name of the parameter matters.
:::

## Scopes

By default, a fixture is recomputed on every call to the view. This is convenient when you want to provide pre-computed values, e.g. common database queries or objects that are derived from the user, and those values are relatively cheap to compute.

However, some fixtures are typically expansive to setup and teardown, and could gain from being reused accross sessions. This is the case of fixtures that access the network, such as an SMTP client or, as in the [problem statement](#problem-statement), a Redis connection.

For this reason, Bocadillo fixtures come with two possible **scopes**:

- `session`: a new copy of the fixture is computed on each session. This is the default behavior.
- `app`: the fixture is reused in all sessions.

### Example: keeping track of WebSocket clients

For example, let's build a fixture for a set of clients (initially empty) which a WebSocket view can use to keep track of connected clients:

```python
@app.fixture(scope="app")
def clients() -> set:
    return set()

@app.websocket_route("/echo")
async def echo(ws, clients: set):
    async with ws:
        clients.add(ws)
        try:
            async for message in ws:
                await ws.send(message)
        finally:
            clients.remove(ws)
```

Since `clients` is app-scoped, other routes can require it and they'll have access to the _same_ set of clients.

For example, here's an API endpoint that returns their count:

```python
@app.route("/clients-count")
async def clients_count(req, res, clients: set):
    res.media = {"count": len(clients)}
```

## Asynchronous fixtures

Up to now, we've only built _synchronous_ fixtures, i.e. ones whose fixture function is declared with `def`.

Of course, Bocadillo also supports **asynchronous fixtures**. Those are declared with `async def` and are evaluated (`await`ed) before being injected into the view.

### Example: fetching JSON data

Here's an example async fixture that draws random JSON data from [HTTPBin](https://httpbin.org) using [aiohttp](https://aiohttp.readthedocs.io):

```python
import aiohttp

@app.fixture
async def random_json():
    async with aiohttp.ClientSession() as session:
        async with session("https://httpbin.org/stream/1") as response:
            return await response.json()

@app.route("/data")
async def data(req, res, random_json: dict):
    res.media = random_json  # already awaited
```

::: tip
When given the `app` [scope](#scopes), an async fixture is only awaited once — the first time it is used. Its result is then cached and reused.

While this is the normal behavior for app-scoped fixtures, this makes reusing an async fixture very cheap because calls to the network/filesystem/etc are only made once.
:::

### Lazy evaluation

If you need to defer evaluating an async fixture until you really need it, you can declare it as `lazy`:

```python
import aiohttp

@app.fixture(lazy=True)
async def random_json():
    async with aiohttp.ClientSession() as session:
        async with session("https://httpbin.org/json") as resp:
            return await resp.json()

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

## Cleaning up fixtures

Some fixtures need to perform cleanup operations when they go out of scope. For example, an app-scoped database fixture may need to close the open connections when the app shuts down, or a session-scoped file fixture may need to close descriptors when the request has been processed.

To support this, Bocadillo fixtures support using a `yield` statement instead of `return`. The yielded value will be injected in the view, and all the code after the `yield` statement will be executed when cleaning up the fixture.

Such fixtures are called **yield fixtures**.

### Example: providing a writable file

As an example, here's a fixture that provides a log file:

```python
from datetime import datetime

@app.fixture
def log():
    logfile = open("/var/requests.log", "w+")
    yield logfile
    logfile.close()

@app.route("/")
async def index(req, res, log):
    log.write(f"{datetime.now()}: {req.client.host}")
    res.text = "Hello, yield fixtures"
```

::: tip
Teardown code will be executed even if an exception occurs within the view. You don't have to wrap the `yield` within a `try/finally` block.
:::

Yield fixtures also play nicely with `with` statements:

```python
@app.fixture
def log():
    with open("/var/requests.log", "w+") as logfile:
        yield logfile
```

## Using fixtures in a fixture function

Fixtures are **modular** — they can be used in other fixtures too to build a loosely-coupled ecosystem of reusable resources.

### Basic example

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

### Example: reusable aiohttp session

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

## Factory fixtures

Sometimes you want a fixture to be generic so that it can be used for a variety of inputs.

**Factory fixtures** allow to do that: instead of having the fixture function return a _value_, it returns a _function_.

::: tip NOTE
Factory fixture is just a _pattern_. There's no magic performed behing the scenes: it's just a fixture that provides a callable.
:::

### Example: parametrized database query

A good candidate for a factory fixture would be a parametrized database query. For example, let's build a factory fixture that retrieves an item from the database given its primary key.

The following example simulates that with a hardcoded, in-memory database of sticky notes:

```python
@app.fixture(scope="app")
def notes():
    return [
        {"id": 1, "text": "Groceries"},
        {"id": 2, "text": "Make potatoe smash"},
    ]

@app.fixture
def get_note(notes):
    async def _get_note(pk: int) -> list:
        try:
            # TODO: fetch from a database instead?
            return next(note for note in notes if note["id"] == pk)
        except StopIteration:
            raise HTTPError(404, detail=f"Note with ID {pk} does not exist.")

    return _get_note

@app.route("/notes/{pk:d}")
async def retrieve_note(req, res, pk: int, get_note):
    res.media = await get_note(pk)
```

### Example: providing temporary files

This example allows views to create and access temporary files.

The factory fixture pattern is combined with [fixture cleanup](#cleaning-up-fixtures) so that temporary files are removed once the fixture goes out of scope:

```python
import os

@app.fixture
def tmpfile():
    files = set()

    async def _create_tmpfile(path: str):
        with open(path, "w") as tmp:
            files.add(path)
            return tmp

    yield _create_tmpfile

    for path in files:
        os.remove(path)
```

### Shortcut syntax

If your factory fixture only defines and returns a function, you can pass `factory=True` to save a bit of boilerplate.

If the fixture needs to access other fixtures, they should be declared first in the factory fixture's signature and separated with a `*` from the other parameters. They won't be expected by the constructed fixture.

To make things clearer, the following example is exactly equivalent to the one above:

```python
@app.fixture(factory=True)
async def get_note(notes, *, pk: int) -> list:
    try:
        return next(note for note in notes if note["id"] == pk)
    except StopIteration:
        raise HTTPError(404, detail=f"Note with ID {pk} does not exist.")

@app.route("/notes/{pk:d}")
async def retrieve_note(req, res, pk: int, get_note):
    res.media = await get_note(pk)
```

## Auto-used fixtures

Sometimes, you may want a fixture to be provisioned without having to explicitly declare it as a parameter in your views.

In that case, you can pass `autouse=True` to the fixture, and it will be automatically activated (within its configured scope).

Such fixtures are called **auto-used fixtures**.

### Example: automatically entering a database transaction

Suppose you're using [Databases](https://github.com/encode/databases) as an async database library, and you want to make sure that database calls in views are performed within a transaction.

This is a situation in which an auto-used fixture would shine:

```python
from databases import Database

from myapp.tables import notes  # imaginary

@app.fixture(scope="app")
async def db() -> Database:
    db = Database("sqlite://:memory:")
    app.on("startup", db.connect)
    app.on("shutdown", db.disconnect)
    return db

@app.fixture(autouse=True)
async def transaction(db: Database):
    async with db.transaction():
        yield

@app.route("/")
async def index(req, res, db: Database):
    # This query is being executed within a transaction. ✨
    res.media = await db.fetch_all(notes.select())
```

## Wrapping up: a better Redis cache

Let's go back to the Redis cache example we exposed in the [problem statement](#problem-statement), and use what we've learnt to improve it by using fixtures.

```python
import aioredis
from bocadillo import App, Templates

app = App()
templates = Templates()

@app.fixture
async def redis():
    redis = await aioredis.create_redis("redis://localhost")
    yield redis
    await redis.wait_closed()

@app.route("/")
async def index(req, res, redis):
    page = await redis.get("index-page")
    if page is None:
        page = await templates.render("index.html")
        await redis.set("index-page", page)
    res.text = page

if __name__ == "__main__":
    app.run()
```

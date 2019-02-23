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

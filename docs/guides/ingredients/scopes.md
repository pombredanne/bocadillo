## Scopes

By default, an ingredient is recomputed on every call to the view. This is convenient when you want to provide pre-computed values, e.g. common database queries or objects that are derived from the user, and those values are relatively cheap to compute.

However, some ingredients are typically expansive to setup and teardown, and could gain from being reused accross sessions. This is the case of ingredients that access the network, such as an SMTP client or, as in the [problem statement](#problem-statement), a Redis connection.

For this reason, Bocadillo ingredients come with two possible **scopes**:

- `session`: a new copy of the ingredient is computed on each session. This is the default behavior.
- `app`: the ingredient is reused in all sessions.

### Example: keeping track of WebSocket clients

For example, let's build an ingredient for a set of clients (initially empty) which a WebSocket view can use to keep track of connected clients:

```python
from bocadillo import App, ingredient

@ingredient(scope="app")
def clients() -> set:
    return set()

app = App()

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

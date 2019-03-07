# Introduction to WebSockets

::: tip NOTE
Although this makes them perfect for intermediate to complex use cases, Bocadillo WebSockets are arguably low-level.

To this extent, we wrote a guide on how to use the higher-level [socket.io](https://socket.io) framework in Bocadillo applications: [Build a real-time application with socket.io](/how-to/socketio.md).
:::

**WebSockets** allow a web browser and a web server to communicate in a bi-directional way via a long-held, low-latency TCP socket connection. They are typically used to build **event-driven** and **real-time** web applications that involve things like notifications, instant messaging or other real-time features.

Typically, WebSocket server applications are I/O-bound and need to deal with many concurrent client connections. This makes asynchronous programming a natural paradigm for implementing WebSocket servers.

As such, Bocadillo provides an easy-to-use and friendly API for building WebSocket servers.

::: tip
As an introduction to WebSockets, we recommend Dion Misic's talk [A Beginner's Guide to WebSockets](https://www.youtube.com/watch?v=PjiXkJ6P9pQ) (Pycon 2018).
:::

## Prerequisites

Bocadillo comes with the [websockets] package installed, so you do not need to install extra dependencies. You're ready to go!

## A basic example

Let's learn by example and see how to create a WebSocket server that simply echoes a message:

```python
from bocadillo import App, WebSocket

app = App()

@app.websocket_route("/echo")
async def echo(ws: WebSocket):
    await ws.accept()
    message = await ws.receive()
    await ws.send(f"You said: {message}")
    await ws.close()

if __name__ == "__main__":
    app.run()
```

Let's break this code down:

1. We create an `App` instance as usual. (If this is not familiar to you, see [The application class].)
2. We register a new **WebSocket route** using the `@app.websocket_route()` decorator. It works in a way similar to `@app.route()` for regular HTTP routes: we give it an URL pattern that will be matched against when an incoming WebSocket connection request is received.
3. We define a **WebSocket view**, i.e. an asynchronous function that takes a `WebSocket` object as its first parameter. Route parameters are passed as extra arguments just like for HTTP routes (see also [Routes and URL design]).
4. Inside the view:
   - We **accept** the connection request in order to complete the handshake with the client. The WebSocket connection is then established.
   - Then, we **receive** a text message from the WebSocket. If no message is available yet, the view will suspend, allowing the server to process other requests until a message is received.
   - Next, we **send** a message to the client.
   - Lastly, we **close** the connection.

These four operations (accept, receive, send and close) are the basic building blocks of WebSocket views.

Continue to learn more about how to use WebSockets in Bocadillo.

[websockets]: https://websockets.readthedocs.io
[the application class]: ../app.md
[routes and url design]: ../http/routing.md

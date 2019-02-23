# Fixture basics

## Registering a fixture

Registering a fixture can be done by decorating a function with the `@bocadillo.fixture` decorator.

Here's a hello world fixture:

```python
from bocadillo import fixture

@fixture
def hello() -> str:
    return "Hello, fixtures!"
```

## Using a fixture

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

## How are fixtures discovered?

Bocadillo can discover fixtures from the following sources:

1. Functions decorated with `@fixture` present in the application script.

```python
# app.py
from bocadillo import fixture

@fixture
def message():
    return "Hello, fixtures!"

app = App()

@app.route("/hello")
async def hello(req, res, message):
    res.media = {"message": message}

if __name__ == "__main__":
    app.run()
```

2. Functions decorated with `@fixture` that get _imported_ in the application script.

```python
# notes.py
from bocadillo import fixture

class Note:
    def __init__(self, id: int, text: str):
        self.id = id
        self.text = text

@fixture
def example_note() -> Note:
    return Note(id=1, text="Cook mashed potatoes")
```

```python
# app.py
from notes import Note  # => `example_note` discovered
```

3. Functions decorated with `@fixture` that live in the `fixtureconf.py` module relative to the application script.

```python
# fixtureconf.py
import random as _random
from bocadillo import fixture

@fixture
def random() -> float:
    return _random.random()
```

4. Functions decorated with `@fixture` that live in a module marked for discovery in the application script using `bocadillo.discover_fixtures(*module_paths)`.

```python
# app.py
from bocadillo import discover_fixtures

discover_fixtures("notes")  # => `example_note` discovered
```

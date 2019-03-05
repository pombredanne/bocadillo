# Ingredient basics

## Registering an ingredient

Registering an ingredient can be done by decorating a function with the `@bocadillo.ingredient` decorator.

Here's a simple hello world ingredient:

```python
from bocadillo import ingredient

@ingredient
def hello() -> str:
    return "Hello, ingredients!"
```

## Using an ingredient

### As a view parameter

Once the ingredient has been defined, it can be used in views by declaring it as a parameter of the view function.

- HTTP example:

```python
@app.route("/hi")
async def say_hi(req, res, hello: str):
    res.text = hello
```

- HTTP example (class-based):

```python
@app.route("/hi")
class SayHi:
    async def get(self, req, res, hello: str):
        res.text = hello
```

- WebSocket example:

```python
@app.websocket_route("/hi")
async def say_hi(ws, hello: str):
    async with ws:
        await ws.send(hello)
```

::: tip NOTE
The examples above use an `str` type annotation for the `hello` parameter. This has nothing to do with ingredients, and isn't used to determine which ingredients need to be injected. Only the name of the parameter matters.
:::

### As a decorator

Alternatively, you can decorate a view with the `@useingredient` decorator. This is useful when you don't need to use the value returned by the ingredient.

```python
from bocadillo import ingredient, useingredient

@ingredient
def hello():
    print("Hello, ingredients!")

@app.route("/hi")
@useingredient("hello")
async def say_hi(req, res):
    res.text = "A hello message was printed to the console."
```

::: tip

- The `@useingredient` decorator accepts a variable number of ingredients.
- Ingredients can be passed by name or by reference.

:::

## How are ingredients discovered?

Bocadillo can discover ingredients from the following sources:

1. Functions decorated with `@ingredient` present in the application script.

```python
# app.py
from bocadillo import ingredient

@ingredient
def message():
    return "Hello, ingredients!"

app = App()

@app.route("/hello")
async def hello(req, res, message):
    res.media = {"message": message}

if __name__ == "__main__":
    app.run()
```

2. Functions decorated with `@ingredient` that get _imported_ in the application script.

```python
# notes.py
from bocadillo import ingredient

class Note:
    def __init__(self, id: int, text: str):
        self.id = id
        self.text = text

@ingredient
def example_note() -> Note:
    return Note(id=1, text="Cook mashed potatoes")
```

```python
# app.py
from notes import Note  # => `example_note` discovered
```

3. Functions decorated with `@ingredient` that live in an `ingredientconf.py` module relative to the application script.

```python
# ingredientconf.py
import random as _random
from bocadillo import ingredient

@ingredient
def random() -> float:
    return _random.random()
```

4. Functions decorated with `@ingredient` that live in a module marked for discovery in the application script using `bocadillo.discover_ingredients(*module_paths)`.

```python
# app.py
from bocadillo import discover_ingredients

discover_ingredients("notes")  # => `example_note` discovered
```

# Factory ingredients

Sometimes you want a ingredient to be generic so that it can be used for a variety of inputs.

**Factory ingredients** allow to do that: instead of having the ingredient function return a _value_, it returns a _function_.

::: tip NOTE
Factory ingredient is just a _pattern_. There's no magic performed behing the scenes: it's just a ingredient that provides a callable.
:::

## Example: parametrized database query

A good candidate for a factory ingredient would be a parametrized database query. For example, let's build a factory ingredient that retrieves an item from the database given its primary key.

The following example simulates that with a hardcoded, in-memory database of sticky notes:

```python
from bocadillo import App, ingredient

@ingredient(scope="app")
def notes():
    return [
        {"id": 1, "text": "Groceries"},
        {"id": 2, "text": "Make potatoe smash"},
    ]

@ingredient
def get_note(notes):
    async def _get_note(pk: int) -> list:
        try:
            # TODO: fetch from a database instead?
            return next(note for note in notes if note["id"] == pk)
        except StopIteration:
            raise HTTPError(404, detail=f"Note with ID {pk} does not exist.")

    return _get_note

app = App()

@app.route("/notes/{pk:d}")
async def retrieve_note(req, res, pk: int, get_note):
    res.media = await get_note(pk)
```

## Example: providing temporary files

This example allows views to create and access temporary files.

The factory ingredient pattern is combined with [ingredient cleanup](#cleaning-up-ingredients) so that temporary files are removed once the ingredient goes out of scope:

```python
import os
from bocadillo import ingredient

@ingredient
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

## Shortcut syntax

If your factory ingredient only defines and returns a function, you can pass `factory=True` to save a bit of boilerplate.

If the ingredient needs to access other ingredients, they should be declared first in the factory ingredient's signature and separated with a `*` from the other parameters. They won't be expected by the constructed ingredient.

To make things clearer, the following example is exactly equivalent to the one above:

```python
from bocadillo import App, ingredient

@ingredient(factory=True)
async def get_note(notes, *, pk: int) -> list:
    try:
        return next(note for note in notes if note["id"] == pk)
    except StopIteration:
        raise HTTPError(404, detail=f"Note with ID {pk} does not exist.")

app = App()

@app.route("/notes/{pk:d}")
async def retrieve_note(req, res, pk: int, get_note):
    res.media = await get_note(pk)
```

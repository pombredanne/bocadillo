# Factory fixtures

Sometimes you want a fixture to be generic so that it can be used for a variety of inputs.

**Factory fixtures** allow to do that: instead of having the fixture function return a _value_, it returns a _function_.

::: tip NOTE
Factory fixture is just a _pattern_. There's no magic performed behing the scenes: it's just a fixture that provides a callable.
:::

## Example: parametrized database query

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

## Example: providing temporary files

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

## Shortcut syntax

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

# Auto-used ingredients

Sometimes, you may want a ingredient to be provisioned without having to explicitly declare it as a parameter in your views.

In that case, you can pass `autouse=True` to the ingredient, and it will be automatically activated (within its configured scope).

Such ingredients are called **auto-used ingredients**.

## Example: automatically entering a database transaction

Suppose you're using [Databases](https://github.com/encode/databases) as an async database library, and you want to make sure that database calls in views are performed within a transaction.

This is a situation in which an auto-used ingredient would shine:

```python
from databases import Database
from bocadillo import App, ingredient

from myapp.tables import notes  # imaginary

@ingredient(scope="app")
async def db() -> Database:
    with Database("sqlite://:memory:") as db:
        yield db

@ingredient(autouse=True)
async def transaction(db: Database):
    async with db.transaction():
        yield

app = App()

@app.route("/")
async def index(req, res, db: Database):
    # This query is being executed within a transaction. ✨
    res.media = await db.fetch_all(notes.select())
```

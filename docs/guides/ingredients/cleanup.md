# Cleaning up ingredients

Some ingredients need to perform cleanup operations when they go out of scope. For example, an app-scoped database ingredient may need to close the open connections when the app shuts down, or a session-scoped file ingredient may need to close descriptors when the request has been processed.

To support this, Bocadillo ingredients support using a `yield` statement instead of `return`. The yielded value will be injected in the view, and all the code after the `yield` statement will be executed when cleaning up the ingredient.

Such ingredients are called **yield ingredients**.

## Example: providing a writable file

As an example, here's a ingredient that provides a log file:

```python
from datetime import datetime
from bocadillo import App, ingredient

@ingredient
def log():
    logfile = open("/var/requests.log", "w+")
    yield logfile
    logfile.close()

app = App()

@app.route("/")
async def index(req, res, log):
    log.write(f"{datetime.now()}: {req.client.host}")
    res.text = "Hello, yield ingredients"
```

::: tip
Teardown code will be executed even if an exception occurs within the view. You don't have to wrap the `yield` within a `try/finally` block.
:::

Yield ingredients also play nicely with `with` statements:

```python
@ingredient
def log():
    with open("/var/requests.log", "w+") as logfile:
        yield logfile
```

# Cleaning up fixtures

Some fixtures need to perform cleanup operations when they go out of scope. For example, an app-scoped database fixture may need to close the open connections when the app shuts down, or a session-scoped file fixture may need to close descriptors when the request has been processed.

To support this, Bocadillo fixtures support using a `yield` statement instead of `return`. The yielded value will be injected in the view, and all the code after the `yield` statement will be executed when cleaning up the fixture.

Such fixtures are called **yield fixtures**.

## Example: providing a writable file

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

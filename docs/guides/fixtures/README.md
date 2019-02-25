# Introduction to Fixtures

In a Bocadillo application, views typically need to access _resources_ or _services_ to fulfill a client's request. For example, they may need to query a database, or interact with a disk-based cache.

Yet, views shouldn't have to care about _how_ those resources are assembled, provided, nor cleaned up.

To address this issue, **fixtures** allow resources to be _injected_ into the view. They are inspired by [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html) and are an example of [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection).

Fixtures aim at being:

- **Explicit**: once a fixture is defined, it can be consumed by an HTTP or WebSocket view simply by declaring it as a function parameter.
- **Modular**: a fixture can itself use other fixtures.
- **Flexible**: fixtures are reusable within the scope of an app or a session, and support a variety of syntaxes (asynchronous vs. synchronous, function vs. generator) to make provisioning resources fun again.

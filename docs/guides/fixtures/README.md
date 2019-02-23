# Introduction to Fixtures

In a web application or service, views hold the core business logic. To implement this logic, views typically need to have access to _resources_ or _services_ — in short, things they _depend on_ to fulfill their purpose. For example, a view might need access to a database or a cache.

The code responsible for providing these resources can quickly clutter views and become hard to maintain.

**Fixtures** aim at solving this problem using [dependency injection](https://en.wikipedia.org/wiki/Dependency_injection). They are:

- Explicit: once a fixture is defined, it can be consumed by an HTTP or WebSocket view simply by declaring it as a function parameter.
- Modular: a fixture can itself use other fixtures.
- Flexible: fixtures are reusable within the scope of an app or a session, and support a variety of syntaxes (asynchronous vs. synchronous, function vs. generator) to make provisioning resources fun again.

::: tip NOTE
For those wondering — this feature was indeed inspired by [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html#fixture).
:::

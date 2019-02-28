# Introduction to Ingredients

In a Bocadillo application, views typically need to access _resources_ or _services_ to fulfill a client's request. For example, they may need to query a database, or interact with a disk-based cache.

Yet, views shouldn't have to care about _how_ those resources are assembled, provided, nor cleaned up.

To address this issue, **ingredients** allow resources to be _injected_ into the view. In this sense, views are really _consumers_ of ingredients.

This feature was heavily inspired by [pytest fixtures](https://docs.pytest.org/en/latest/ingredient.html).

::: tip NOTE
The implementation of ingredients in Bocadillo is provided by [aiodine](https://github.com/bocadilloproject/aiodine), an async dependency injection library.

We chose to release aiodine separately from Bocadillo to allow its reuse in other projects. But keep in mind that **Bocadillo ingredients are merely a thin layer on top of aiodine's providers**.

To make things clear, here is the terminology correspondance between Bocadillo and aiodine:

| aiodine          | Bocadillo       |
| ---------------- | --------------- |
| Provider         | Ingredient      |
| Consumer         | View            |
| `session` scope  | `app` scope     |
| `function` scope | `session` scope |

:::

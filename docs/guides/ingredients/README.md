# Ingredients <Badge text="experimental" type="warn"/> <Badge text="0.13+"/>

## Motivation

In a Bocadillo application, views typically need to access **resources** or **services** to fulfill a client's request. For example, they may need to query a database, or interact with a disk-based cache.

Yet, views shouldn't have to care about _how_ those resources are assembled, provided, or cleaned up.

To address this issue, **ingredients** provide an explicit, modular and flexible way to **inject resources into views**.

The look and feel for the ingredients API was heavily inspired by [pytest fixtures](https://docs.pytest.org/en/latest/ingredient.html). However, ingredients are not specifically meant for testing (although they do enhance testability). Instead, you can think of ingredients as a **runtime dependency injection mechanism**.

## Relationship with the aiodine library

The implementation of ingredients in Bocadillo is provided by [aiodine](https://github.com/bocadilloproject/aiodine), an officially supported async-first dependency injection library.

For reference, here is the terminology correspondance between Bocadillo and aiodine:

| aiodine             | Bocadillo               |
| ------------------- | ----------------------- |
| Provider            | Ingredient              |
| Consumer            | View                    |
| `session` scope     | `app` scope             |
| `function` scope    | `request` scope         |
| `@aiodine.provider` | `@bocadillo.ingredient` |

Bocadillo automatically marks HTTP and WebSocket views as consumers so that they can

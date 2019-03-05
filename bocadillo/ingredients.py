from aiodine import Store, scopes

# pylint: disable=invalid-name
_STORE = Store(
    scope_aliases={"request": scopes.FUNCTION, "app": scopes.SESSION},
    providers_module="ingredientconf",
)
ingredient = _STORE.provider
discover_ingredients = _STORE.discover
useingredient = _STORE.useprovider
consumer = _STORE.consumer
freeze = _STORE.freeze

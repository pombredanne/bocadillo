from aiodine import Store, scopes

# pylint: disable=invalid-name
_STORE = Store(
    scope_aliases={"session": scopes.FUNCTION, "app": scopes.SESSION},
    providers_module="ingredientconf",
)
ingredient = _STORE.provider
consumer = _STORE.consumer
freeze = _STORE.freeze
exit_freeze = _STORE.exit_freeze
discover_ingredients = _STORE.discover

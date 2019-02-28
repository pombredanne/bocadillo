from aiodine import Store, scopes

# pylint: disable=invalid-name
_STORE = Store(
    scope_aliases={"session": scopes.FUNCTION, "app": scopes.SESSION}
)
ingredient = _STORE.provider
consumer = _STORE.consumer

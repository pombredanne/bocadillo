from functools import wraps, update_wrapper, partial
from contextlib import suppress, contextmanager
from importlib import import_module
from typing import Any, Awaitable, Dict, List, Callable, Tuple, Optional
from inspect import signature, Parameter

CoroutineFunction = Callable[..., Awaitable]
SCOPE_SESSION = "session"


# TODO: AsyncFixture
class Fixture:
    """Represents a (synchronous) fixture.

    This is mostly a wrapper around a fixture function, along with
    some metadata.
    """

    def __init__(self, func: Callable, name: str, scope: str):
        self.func = func
        self.name = name
        self.scope = scope

        update_wrapper(self, self.func)

    @classmethod
    def create(cls, func: Callable, name: str, scope: str) -> "Fixture":
        """Factory method to build fixtures of the appropriate scope."""
        if scope != SCOPE_SESSION:
            raise ValueError("non-session fixtures aren't supported yet")
        return cls(func, name=name, scope=scope)

    def __repr__(self) -> str:
        return (
            f"<Fixture name={self.name}, scope={self.scope}, func={self.func}>"
        )

    def __call__(self) -> Any:
        # TODO: support fixtures with parameters
        # TODO: support async fixtures
        return self.func()


class Store:

    DEFAULT_FIXTURES_MODULE = "fixtureconf"

    def __init__(self):
        # TODO: add support for app fixtures
        self.session_fixtures: Dict[str, Fixture] = {}

    @property
    def empty(self):
        return not self.session_fixtures

    def _exists(self, name: str) -> bool:
        return name in self.session_fixtures

    def _get(self, name: str) -> Optional[Fixture]:
        return self.session_fixtures.get(name)

    def _get_collection(self, scope: str) -> dict:
        # TODO: add support for app fixtures
        return self.session_fixtures

    def discover_default(self):
        with suppress(ImportError):
            self.discover_fixtures(self.DEFAULT_FIXTURES_MODULE)

    def discover_fixtures(self, *module_paths: str):
        for module_path in module_paths:
            import_module(module_path)

    def fixture(
        self, func: Callable = None, scope: str = "session", name: str = None
    ) -> Fixture:
        if func is None:
            return partial(self.fixture, scope=scope, name=name)

        if name is None:
            name = func.__name__

        # NOTE: save the new fixture before checking for recursion,
        # so that its dependants can detect it as a dependency.
        fixt = Fixture.create(func, name=name, scope=scope)
        self._add(fixt)

        self._check_for_recursive_fixtures(name, func)

        return fixt

    def _add(self, fixt: Fixture):
        collection = self._get_collection(fixt.scope)
        collection[fixt.name] = fixt

    def _check_for_recursive_fixtures(self, name: str, func: Callable):
        for other_name, other in self._get_fixtures(func).items():
            if name in self._get_fixtures(other.func):
                raise TypeError(
                    "recursive fixture detected: "
                    f"{name} and {other_name} depend on each other."
                )

    def _get_fixtures(self, func: Callable) -> Dict[str, Fixture]:
        fixtures = {
            param: self._get(param) for param in signature(func).parameters
        }
        return dict(filter(lambda item: item[1] is not None, fixtures.items()))

    def _resolve_fixtures(self, func: Callable) -> Tuple[list, dict]:
        args_fixtures: List[Tuple[str, Fixture]] = []
        kwargs_fixtures: Dict[str, Fixture] = {}

        for name, parameter in signature(func).parameters.items():
            fixt: Optional[Fixture] = self.session_fixtures.get(name)
            # TODO: try app fixtures too
            if fixt is None:
                continue

            if parameter.kind == Parameter.POSITIONAL_ONLY:
                args_fixtures.append((name, fixt))
            else:
                kwargs_fixtures[name] = fixt

        return args_fixtures, kwargs_fixtures

    def resolve_function(self, func: Callable) -> Callable:
        args_fixtures, kwargs_fixtures = self._resolve_fixtures(func)

        if not args_fixtures and not kwargs_fixtures:
            return func

        @wraps(func)
        def with_fixtures(*args, **kwargs):
            # Evaluate the fixtures when the function is actually called.
            injected_args = [fixt() for _, fixt in args_fixtures]
            injected_kwargs = {
                name: fixt() for name, fixt in kwargs_fixtures.items()
            }
            return func(*args, *injected_args, **kwargs, **injected_kwargs)

        return with_fixtures

    def freeze(self):
        """Resolve fixtures used by each fixture."""
        for fixt in self.session_fixtures.values():
            fixt.func = self.resolve_function(fixt.func)

    @contextmanager
    def will_freeze(self):
        yield
        self.freeze()

    def __contains__(self, element: Any) -> bool:
        return self._exists(element)

    def __bool__(self) -> bool:
        return not self.empty


_STORE = Store()
fixture = _STORE.fixture  # pylint: disable=invalid-name
discover_fixtures = _STORE.discover_fixtures  # pylint: disable=invalid-name


class BaseResolver:
    """Resolver for functions."""

    def __init__(self, store: Store = None):
        if store is None:
            store = _STORE
        self.store = store

    def resolve_function(self, func: Callable) -> Callable:
        return self.store.resolve_function(func)

    # TODO: resolve_coroutine_function


class Resolver(BaseResolver):
    """Resolver for framework-level objects."""

    # TODO


# TODO: utility to bootstrap fixtures on an app

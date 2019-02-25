from functools import wraps, update_wrapper, partial
from contextlib import suppress, contextmanager
from importlib import import_module
from typing import Any, Awaitable, Dict, List, Callable, Tuple, Optional, Union
from inspect import signature, Parameter, iscoroutinefunction

from .compat import call_async, wrap_async

CoroutineFunction = Callable[..., Awaitable]
SCOPE_SESSION = "session"


class FixtureDeclarationError(Exception):
    """Base exception for situations when a fixture was ill-declared."""


class RecursiveFixtureError(FixtureDeclarationError):
    """Raised when two fixtures depend on each other."""

    def __init__(self, first: str, second: str):
        message = (
            "recursive fixture detected: "
            f"{first} and {second} depend on each other."
        )
        super().__init__(message)


# TODO: AsyncFixture
class Fixture:
    """Represents a (synchronous) fixture.

    This is mostly a wrapper around a fixture function, along with
    some metadata.
    """

    def __init__(self, func: Callable, name: str, scope: str, lazy: bool):
        if lazy and scope != SCOPE_SESSION:
            raise FixtureDeclarationError(
                "Lazy fixtures must be session-scoped"
            )

        if not iscoroutinefunction(func):
            func = wrap_async(func)

        self.func: CoroutineFunction = func
        self.name = name
        self.scope = scope
        self.lazy = lazy

        update_wrapper(self, self.func)

    @classmethod
    def create(cls, func, **kwargs) -> "Fixture":
        """Factory method to build fixtures of the appropriate scope."""
        return cls(func, **kwargs)

    def __repr__(self) -> str:
        return (
            f"<Fixture name={self.name}, scope={self.scope}, func={self.func}>"
        )

    def __call__(self) -> Awaitable:
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
        self,
        func: Callable = None,
        scope: str = "session",
        name: str = None,
        lazy: bool = False,
    ) -> Fixture:
        if func is None:
            return partial(self.fixture, scope=scope, name=name, lazy=lazy)

        if name is None:
            name = func.__name__

        # NOTE: save the new fixture before checking for recursion,
        # so that its dependants can detect it as a dependency.
        fixt = Fixture.create(func, name=name, scope=scope, lazy=lazy)
        self._add(fixt)

        self._check_for_recursive_fixtures(name, func)

        return fixt

    def _add(self, fixt: Fixture):
        collection = self._get_collection(fixt.scope)
        collection[fixt.name] = fixt

    def _check_for_recursive_fixtures(self, name: str, func: Callable):
        for other_name, other in self._get_fixtures(func).items():
            if name in self._get_fixtures(other.func):
                raise RecursiveFixtureError(name, other_name)

    def _get_fixtures(self, func: Callable) -> Dict[str, Fixture]:
        fixtures = {
            param: self._get(param) for param in signature(func).parameters
        }
        return dict(filter(lambda item: item[1] is not None, fixtures.items()))

    def _resolve_fixtures(self, func: Callable) -> Tuple[list, dict]:
        args_fixtures: List[Tuple[str, Fixture]] = []
        kwargs_fixtures: Dict[str, Fixture] = {}

        # NOTE: This flag goes down when we process a non-fixture parameter.
        # It allows to detect fixture parameters declared *after*
        # non-fixture parameters.
        processing_fixtures = True

        for name, parameter in signature(func).parameters.items():
            fixt: Optional[Fixture] = self.session_fixtures.get(name)
            # TODO: try app fixtures too

            if fixt is None:
                processing_fixtures = False
                continue

            if not processing_fixtures:
                raise FixtureDeclarationError(
                    "Fixture parameters must be declared *before* other "
                    "parameters, so that they can be deterministically passed "
                    "to the consuming function."
                )

            if parameter.kind == Parameter.KEYWORD_ONLY:
                kwargs_fixtures[name] = fixt
            else:
                args_fixtures.append((name, fixt))

        return args_fixtures, kwargs_fixtures

    def resolve_function(
        self, func: Union[Callable, CoroutineFunction]
    ) -> CoroutineFunction:
        if not iscoroutinefunction(func):
            func = wrap_async(func)

        args_fixtures, kwargs_fixtures = self._resolve_fixtures(func)

        if not args_fixtures and not kwargs_fixtures:
            return func

        @wraps(func)
        async def with_fixtures(*args, **kwargs):
            # Evaluate the fixtures when the function is actually called.
            injected_args = [
                fixt() if fixt.lazy else await fixt()
                for _, fixt in args_fixtures
            ]
            injected_kwargs = {
                name: (fixt() if fixt.lazy else await fixt())
                for name, fixt in kwargs_fixtures.items()
            }
            # NOTE: injected args must be given first by convention.
            # The order for kwargs should not matter.
            return await func(
                *injected_args, *args, **injected_kwargs, **kwargs
            )

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

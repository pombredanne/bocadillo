import inspect

import pytest

from bocadillo.fixtures import Store, Resolver


def test_resolve_for_func_returns_function(resolver: Resolver):
    @resolver.resolve_function
    def func():
        return "test"

    assert inspect.isfunction(func)


def test_if_no_fixture_declared_then_behaves_like_func(resolver: Resolver):
    @resolver.resolve_function
    def func():
        return "test"

    assert func() == "test"


def test_if_fixture_does_not_exist_then_missing_argument(
    store: Store, resolver: Resolver
):
    @store.fixture
    def gra():
        return "gra"

    @resolver.resolve_function
    def func(arg):  # <- "gra" exists, but not "arg"
        return 2 * arg

    with pytest.raises(TypeError):
        func()

    assert func(10) == 20


def test_if_fixture_exists_then_injected(store: Store, resolver: Resolver):
    @store.fixture
    def arg():
        return "foo"

    @resolver.resolve_function
    def func(arg):
        return 2 * arg

    assert func() == "foofoo"


def test_foo(a):
    pass

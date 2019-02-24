import inspect

import pytest

from bocadillo.fixtures import Store, Resolver


def test_resolve_for_func_returns_function(resolver: Resolver):
    func = resolver.resolve_function(lambda: "test")
    assert inspect.isfunction(func)


def test_if_no_fixture_declared_then_behaves_like_func(resolver: Resolver):
    func = resolver.resolve_function(lambda: "test")
    assert func() == "test"


def test_if_fixture_does_not_exist_then_missing_argument(
    store: Store, resolver: Resolver
):
    @store.fixture
    def gra():
        return "gra"

    # "gra" exists, but not "arg"
    func = resolver.resolve_function(lambda arg: 2 * arg)

    with pytest.raises(TypeError):
        func()

    assert func(10) == 20


def test_if_fixture_exists_then_injected(store: Store, resolver: Resolver):
    @store.fixture
    def arg():
        return "foo"

    func = resolver.resolve_function(lambda arg: 2 * arg)
    assert func() == "foofoo"


def test_fixture_uses_fixture(store: Store, resolver: Resolver):
    with store.will_freeze():

        @store.fixture
        def a():
            return "a"

        @store.fixture
        def b(a):
            return a * 2

    func = resolver.resolve_function(lambda b: b)
    assert func() == "aa"


def test_fixture_uses_fixture_declared_later(store: Store, resolver: Resolver):
    with store.will_freeze():

        @store.fixture
        def b(a):
            return a * 2

        @store.fixture
        def a():
            return "a"

    func = resolver.resolve_function(lambda b: b)
    assert func() == "aa"


def test_detect_recursive_fixture(store: Store):
    with store.will_freeze():

        @store.fixture
        def b(a):
            return a * 2

        with pytest.raises(TypeError) as ctx:

            @store.fixture
            def a(b):
                return a * 2

        assert "recursive" in str(ctx.value)

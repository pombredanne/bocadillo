import inspect

import pytest

from bocadillo.fixtures import Store


def test_resolve_for_func_returns_function(store: Store):
    func = store.resolve_function(lambda: "test")
    assert inspect.isfunction(func)


def test_if_no_fixture_declared_then_behaves_like_func(store: Store):
    func = store.resolve_function(lambda: "test")
    assert func() == "test"


def test_if_fixture_does_not_exist_then_missing_argument(store: Store):
    @store.fixture
    def gra():
        return "gra"

    # "gra" exists, but not "arg"
    func = store.resolve_function(lambda arg: 2 * arg)

    with pytest.raises(TypeError):
        func()

    assert func(10) == 20


def test_if_fixture_exists_then_injected(store: Store):
    @store.fixture
    def arg():
        return "foo"

    assert store.resolve_function(lambda arg: 2 * arg)() == "foofoo"

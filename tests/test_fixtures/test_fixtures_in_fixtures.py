import pytest

from bocadillo.fixtures import Store, Resolver, RecursiveFixtureError


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
    @store.fixture
    def b(a):
        return a * 2

    with pytest.raises(RecursiveFixtureError) as ctx:

        @store.fixture
        def a(b):
            return a * 2

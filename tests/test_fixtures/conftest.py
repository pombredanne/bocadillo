import pytest

from bocadillo.fixtures import Store, Resolver


@pytest.fixture(name="store")
def fixture_store() -> Store:
    return Store()


@pytest.fixture(name="resolver")
def fixture_resolver(store: Store) -> Resolver:
    return Resolver(store=store)

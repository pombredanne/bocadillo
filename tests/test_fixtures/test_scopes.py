import pytest

from bocadillo.fixtures import Store


def test_fixtures_are_session_scoped_by_default(store: Store):
    @store.fixture
    def items():
        pass

    assert items.scope == "session"


@pytest.mark.asyncio
async def test_session_fixture_is_recomputed_every_time(store: Store):
    @store.fixture(scope="session")
    def items():
        return []

    @store.resolve_function
    def add(items, value):
        items.append(value)
        return items

    assert await add(1) == [1]
    assert await add(2) == [2]  # instead of [1, 2]

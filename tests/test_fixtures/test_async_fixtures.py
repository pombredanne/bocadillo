import pytest
from inspect import iscoroutine

from bocadillo.fixtures import Store

pytestmark = pytest.mark.asyncio


async def test_use_async_fixture(store: Store):
    @store.fixture
    async def pitch():
        return "C#"

    @store.resolve_function
    def play_sync(pitch):
        return 2 * "C#"

    @store.resolve_function
    async def play_async(pitch):
        return 2 * "C#"

    assert await play_sync() == "C#C#"
    assert await play_async() == "C#C#"


async def test_lazy_async_fixture(store: Store):
    @store.fixture(lazy=True)
    async def pitch():
        return "C#"

    @store.resolve_function
    async def play(pitch):
        assert iscoroutine(pitch)
        return 2 * await pitch

    assert await play() == "C#C#"

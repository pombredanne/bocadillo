import sys

import pytest
from bocadillo.fixtures import Store


@pytest.fixture
def notes_module(store: Store):
    class NotesModule:
        @store.fixture
        def pitch():  # pylint: disable=no-method-argument
            return "C#"

    sys.modules["notes"] = NotesModule


@pytest.mark.usefixtures("notes_module")
def test_discover_fixtures(store: Store):
    store.discover_fixtures("notes")
    assert store
    assert "pitch" in store
    assert store.resolve_function(lambda pitch: 2 * pitch)() == "C#C#"


def test_if_module_does_not_exist_then_error(store: Store):
    with pytest.raises(ImportError):
        store.discover_fixtures("doesnotexist")

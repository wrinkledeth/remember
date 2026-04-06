from unittest.mock import patch, Mock, call

import pytest
import requests

from remember.anki_client import (
    AnkiNote,
    _invoke,
    ensure_deck,
    find_synced_notes,
    get_notes_info,
    add_note,
    update_note_fields,
    update_tags,
    ANKI_CONNECT_URL,
    ANKI_CONNECT_VERSION,
)


def _mock_response(result=None, error=None):
    mock = Mock()
    mock.json.return_value = {"result": result, "error": error}
    return mock


# --- _invoke ---


@patch("remember.anki_client.requests.post")
def test_invoke_success(mock_post):
    mock_post.return_value = _mock_response(result=[1, 2, 3])
    result = _invoke("findNotes", query="deck:Test")
    assert result == [1, 2, 3]
    mock_post.assert_called_once_with(
        ANKI_CONNECT_URL,
        json={"action": "findNotes", "version": ANKI_CONNECT_VERSION, "params": {"query": "deck:Test"}},
        timeout=5,
    )


@patch("remember.anki_client.requests.post")
def test_invoke_anki_error(mock_post):
    mock_post.return_value = _mock_response(error="collection is not available")
    with pytest.raises(RuntimeError, match="AnkiConnect error: collection is not available"):
        _invoke("findNotes", query="deck:Test")


@patch("remember.anki_client.requests.post")
def test_invoke_connection_refused(mock_post):
    mock_post.side_effect = requests.exceptions.ConnectionError()
    with pytest.raises(RuntimeError, match="Could not connect to AnkiConnect"):
        _invoke("findNotes", query="deck:Test")


# --- find_synced_notes ---


@patch("remember.anki_client.requests.post")
def test_find_synced_notes_query(mock_post):
    mock_post.return_value = _mock_response(result=[10, 20])
    result = find_synced_notes("Life Insights")
    assert result == [10, 20]
    payload = mock_post.call_args[1]["json"]
    assert payload["params"]["query"] == 'deck:"Life Insights" tag:insight-id::*'


# --- get_notes_info ---


@patch("remember.anki_client.requests.post")
def test_get_notes_info_parses_response(mock_post):
    mock_post.return_value = _mock_response(result=[
        {
            "noteId": 100,
            "tags": ["insight-id::001", "mindset", "relationships"],
            "fields": {
                "Front": {"value": "Front text"},
                "Back": {"value": "Back text"},
            },
        }
    ])
    notes = get_notes_info([100])
    assert len(notes) == 1
    assert notes[0] == AnkiNote(
        note_id=100,
        card_id="001",
        front="Front text",
        back="Back text",
        tags=["mindset", "relationships"],
    )


@patch("remember.anki_client.requests.post")
def test_get_notes_info_empty_list(mock_post):
    result = get_notes_info([])
    assert result == []
    mock_post.assert_not_called()


# --- add_note ---


@patch("remember.anki_client.requests.post")
def test_add_note_payload(mock_post):
    mock_post.return_value = _mock_response(result=42)
    result = add_note("My Deck", "Q", "A", "001", ["mindset"])
    assert result == 42
    payload = mock_post.call_args[1]["json"]
    note = payload["params"]["note"]
    assert note["deckName"] == "My Deck"
    assert note["modelName"] == "Basic"
    assert note["fields"] == {"Front": "Q", "Back": "A"}
    assert note["tags"] == ["insight-id::001", "mindset"]


# --- update_note_fields ---


@patch("remember.anki_client.requests.post")
def test_update_note_fields_payload(mock_post):
    mock_post.return_value = _mock_response(result=None)
    update_note_fields(100, "New front", "New back")
    payload = mock_post.call_args[1]["json"]
    assert payload["action"] == "updateNoteFields"
    assert payload["params"]["note"] == {
        "id": 100,
        "fields": {"Front": "New front", "Back": "New back"},
    }


# --- update_tags ---


@patch("remember.anki_client.requests.post")
def test_update_tags_adds_and_removes(mock_post):
    mock_post.return_value = _mock_response(result=None)
    update_tags(100, "001", old_tags=["mindset", "career"], new_tags=["mindset", "health"])
    assert mock_post.call_count == 2
    calls = mock_post.call_args_list
    actions = {c[1]["json"]["action"] for c in calls}
    assert actions == {"removeTags", "addTags"}

    remove_call = next(c for c in calls if c[1]["json"]["action"] == "removeTags")
    assert remove_call[1]["json"]["params"]["tags"] == "career"

    add_call = next(c for c in calls if c[1]["json"]["action"] == "addTags")
    assert add_call[1]["json"]["params"]["tags"] == "health"


@patch("remember.anki_client.requests.post")
def test_update_tags_no_change(mock_post):
    update_tags(100, "001", old_tags=["mindset"], new_tags=["mindset"])
    mock_post.assert_not_called()

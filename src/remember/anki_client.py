from dataclasses import dataclass
from typing import Any

import requests

ANKI_CONNECT_URL = "http://localhost:8765"
ANKI_CONNECT_VERSION = 6
ID_TAG_PREFIX = "insight-id::"


@dataclass
class AnkiNote:
    note_id: int
    card_id: str
    front: str
    back: str
    mod: int = 0
    model_name: str = ""


def _invoke(action: str, **params) -> Any:
    payload = {"action": action, "version": ANKI_CONNECT_VERSION, "params": params}
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to AnkiConnect. Is Anki running with AnkiConnect installed?"
        )
    result = response.json()
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect error: {result['error']}")
    return result["result"]


def ensure_deck(deck: str) -> None:
    _invoke("createDeck", deck=deck)


def find_synced_notes(deck: str) -> list[int]:
    query = f'deck:"{deck}" tag:{ID_TAG_PREFIX}*'
    return _invoke("findNotes", query=query)


def get_notes_info(note_ids: list[int]) -> list[AnkiNote]:
    if not note_ids:
        return []
    raw = _invoke("notesInfo", notes=note_ids)
    notes = []
    for item in raw:
        tags: list[str] = item["tags"]
        card_id = next(
            (
                t.removeprefix(ID_TAG_PREFIX)
                for t in tags
                if t.startswith(ID_TAG_PREFIX)
            ),
            "",
        )
        notes.append(
            AnkiNote(
                note_id=item["noteId"],
                card_id=card_id,
                front=item["fields"]["Front"]["value"],
                back=item["fields"]["Back"]["value"],
                mod=item.get("mod", 0),
                model_name=item.get("modelName", ""),
            )
        )
    return notes


def add_note(deck: str, front: str, back: str, card_id: str) -> int:
    return _invoke(
        "addNote",
        note={
            "deckName": deck,
            "modelName": "Basic",
            "fields": {"Front": front, "Back": back},
            "tags": [f"{ID_TAG_PREFIX}{card_id}"],
        },
    )


def update_note_fields(note_id: int, front: str, back: str) -> None:
    _invoke(
        "updateNoteFields",
        note={"id": note_id, "fields": {"Front": front, "Back": back}},
    )


def find_notes_in_deck(deck: str) -> list[int]:
    query = f'deck:"{deck}"'
    return _invoke("findNotes", query=query)


def add_tags(note_ids: list[int], tags: str) -> None:
    _invoke("addTags", notes=note_ids, tags=tags)


def delete_notes(note_ids: list[int]) -> None:
    if not note_ids:
        return
    _invoke("deleteNotes", notes=note_ids)

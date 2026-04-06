import textwrap
import warnings
from pathlib import Path

import pytest

from remember.parser import InsightCard, parse_insights

FIXTURE = Path(__file__).parent / "fixtures" / "test_insights.md"


# --- fixture file tests ---

def test_fixture_parses_valid_cards():
    cards = parse_insights(str(FIXTURE))
    # fixture has 7 valid IDs (001-007); malformed card is skipped
    assert len(cards) == 7


def test_fixture_card_ids():
    cards = parse_insights(str(FIXTURE))
    ids = [c.id for c in cards]
    assert ids == ["001", "002", "003", "004", "005", "006", "007"]


def test_fixture_fronts_stripped():
    cards = parse_insights(str(FIXTURE))
    for card in cards:
        assert card.front == card.front.strip()
        assert card.front != ""


def test_fixture_backs_stripped():
    cards = parse_insights(str(FIXTURE))
    for card in cards:
        assert card.back == card.back.strip()


# --- normal card with tags ---

def test_tags_parsed():
    cards = parse_insights(str(FIXTURE))
    card_001 = next(c for c in cards if c.id == "001")
    assert card_001.tags == ["relationships", "mindset"]


def test_single_tag():
    cards = parse_insights(str(FIXTURE))
    card_004 = next(c for c in cards if c.id == "004")
    assert card_004.tags == ["relationships"]


def test_front_text():
    cards = parse_insights(str(FIXTURE))
    card_001 = next(c for c in cards if c.id == "001")
    assert card_001.front == "When she's venting about her day, what am I actually being asked to do?"


# --- card without tags ---

def test_no_tags_returns_empty_list():
    cards = parse_insights(str(FIXTURE))
    card_006 = next(c for c in cards if c.id == "006")
    assert card_006.tags == []


def test_no_tags_back_parsed():
    cards = parse_insights(str(FIXTURE))
    card_006 = next(c for c in cards if c.id == "006")
    assert "no tags" in card_006.back.lower()


# --- multi-paragraph back ---

def test_multi_paragraph_back():
    cards = parse_insights(str(FIXTURE))
    card_002 = next(c for c in cards if c.id == "002")
    assert "\n\n" in card_002.back
    assert "10% truth" in card_002.back


# --- malformed metadata ---

def test_malformed_metadata_warns():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cards = parse_insights(str(FIXTURE))
    messages = [str(w.message) for w in caught]
    assert any("malformed" in m.lower() for m in messages)


def test_malformed_metadata_card_skipped():
    cards = parse_insights(str(FIXTURE))
    fronts = [c.front for c in cards]
    assert "A card with malformed metadata" not in fronts


# --- empty back ---

def test_empty_back_card_included():
    cards = parse_insights(str(FIXTURE))
    card_007 = next((c for c in cards if c.id == "007"), None)
    assert card_007 is not None


def test_empty_back_is_empty_string():
    cards = parse_insights(str(FIXTURE))
    card_007 = next(c for c in cards if c.id == "007")
    assert card_007.back == ""


# --- inline edge case tests ---

def _parse_inline(md: str) -> list[InsightCard]:
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md)
        path = f.name
    try:
        return parse_insights(path)
    finally:
        os.unlink(path)


def test_minimal_card():
    md = textwrap.dedent("""\
        # Life Insights

        ## Minimal front
        <!-- id: 001 -->
        Minimal back.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 1
    assert cards[0].id == "001"
    assert cards[0].front == "Minimal front"
    assert cards[0].back == "Minimal back."
    assert cards[0].tags == []


def test_tags_with_extra_spaces():
    md = textwrap.dedent("""\
        # Life Insights

        ## Front
        <!-- id: 001 | tags:  mindset ,  career  -->
        Back.
    """)
    cards = _parse_inline(md)
    assert cards[0].tags == ["mindset", "career"]


def test_multiple_cards_correct_count():
    md = textwrap.dedent("""\
        # Life Insights

        ## Card one
        <!-- id: 001 | tags: mindset -->
        Back one.

        ## Card two
        <!-- id: 002 | tags: career -->
        Back two.

        ## Card three
        <!-- id: 003 -->
        Back three.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 3


def test_missing_metadata_entirely_warns_and_skips():
    md = textwrap.dedent("""\
        # Life Insights

        ## A card with no metadata at all

    """)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cards = _parse_inline(md)
    assert len(cards) == 0
    assert len(caught) == 1


def test_dataclass_fields():
    card = InsightCard(id="001", front="Front", back="Back", tags=["mindset"])
    assert card.id == "001"
    assert card.front == "Front"
    assert card.back == "Back"
    assert card.tags == ["mindset"]


def test_dataclass_default_tags():
    card = InsightCard(id="001", front="Front", back="Back")
    assert card.tags == []

import textwrap
import warnings
from pathlib import Path

from remember.parser import InsightCard, parse_insights

FIXTURE = Path(__file__).parent / "fixtures" / "test_insights.md"


# --- fixture file tests ---


def test_fixture_parses_valid_cards():
    cards = parse_insights(str(FIXTURE))
    assert len(cards) == 8


def test_fixture_card_ids():
    cards = parse_insights(str(FIXTURE))
    ids = [c.id for c in cards]
    assert ids == ["001", "002", "003", "004", "005", "006", "008", "007"]


def test_fixture_fronts_stripped():
    cards = parse_insights(str(FIXTURE))
    for card in cards:
        assert card.front == card.front.strip()
        assert card.front != ""


def test_fixture_backs_stripped():
    cards = parse_insights(str(FIXTURE))
    for card in cards:
        if card.back:
            assert card.back == card.back.strip()


def test_front_text():
    cards = parse_insights(str(FIXTURE))
    card_001 = next(c for c in cards if c.id == "001")
    assert (
        card_001.front
        == "When she's venting about her day, what am I actually being asked to do?"
    )


# --- multi-line front ---


def test_multi_line_front():
    cards = parse_insights(str(FIXTURE))
    card_008 = next(c for c in cards if c.id == "008")
    assert "A multi-line front card" in card_008.front
    assert "with a second line of context" in card_008.front
    assert "and a third" in card_008.front
    assert card_008.front.count("\n") == 2


# --- multi-paragraph back ---


def test_multi_paragraph_back():
    cards = parse_insights(str(FIXTURE))
    card_002 = next(c for c in cards if c.id == "002")
    assert "\n\n" in card_002.back
    assert "10% truth" in card_002.back


# --- missing separator ---


def test_missing_separator_warns():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parse_insights(str(FIXTURE))
    messages = [str(w.message) for w in caught]
    assert any("missing ---" in m.lower() for m in messages)


def test_missing_separator_card_skipped():
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

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
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
        ---
        Minimal back.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 1
    assert cards[0].id == "001"
    assert cards[0].front == "Minimal front"
    assert cards[0].back == "Minimal back."


def test_multiple_cards_correct_count():
    md = textwrap.dedent("""\
        # Life Insights

        ## Card one
        <!-- id: 001 -->
        ---
        Back one.

        ## Card two
        <!-- id: 002 -->
        ---
        Back two.

        ## Card three
        <!-- id: 003 -->
        ---
        Back three.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 3


def test_missing_separator_warns_and_skips():
    md = textwrap.dedent("""\
        # Life Insights

        ## A card with no separator
        Just some text.
    """)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cards = _parse_inline(md)
    assert len(cards) == 0
    assert len(caught) == 1


def test_card_without_id():
    md = textwrap.dedent("""\
        # Life Insights

        ## A card with no ID
        ---
        Back text.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 1
    assert cards[0].id is None
    assert cards[0].front == "A card with no ID"
    assert cards[0].back == "Back text."


def test_multi_line_front_inline():
    md = textwrap.dedent("""\
        # Life Insights

        ## First line of front
        <!-- id: 001 -->
        second line
        third line
        ---
        Back text.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 1
    assert cards[0].front == "First line of front\nsecond line\nthird line"
    assert cards[0].back == "Back text."


def test_html_comments_ignored():
    md = textwrap.dedent("""\
        # Life Insights

        <!-- This is a section comment -->

        ## Card front
        <!-- id: 001 -->
        ---
        Back text.

        <!-- Another comment between cards -->

        ## Second card
        <!-- id: 002 -->
        ---
        Second back.
    """)
    cards = _parse_inline(md)
    assert len(cards) == 2
    assert cards[0].front == "Card front"
    assert cards[1].front == "Second card"


def test_dataclass_fields():
    card = InsightCard(id="001", front="Front", back="Back")
    assert card.id == "001"
    assert card.front == "Front"
    assert card.back == "Back"

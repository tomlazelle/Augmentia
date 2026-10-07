import pytest

from textkit import truncate


def test_short_text_is_unchanged():
    assert truncate("hello", 10) == "hello"


def test_long_text_is_cut_with_suffix():
    assert truncate("hello world", 8) == "hello w…"


def test_width_smaller_than_suffix_raises():
    with pytest.raises(ValueError):
        truncate("hello", 0)

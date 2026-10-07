import pytest

from textkit import truncate, word_count


@pytest.mark.parametrize(
    "text", ["one two  three", "one\ttwo\nthree", "  one \t two\nthree  "]
)
def test_word_count_separates_words_by_whitespace_runs(text):
    assert word_count(text) == 3


def test_word_count_empty_text():
    assert word_count("") == 0


@pytest.mark.parametrize("text", [" ", "   ", "\t", "\n", " \t\r\n "])
def test_word_count_whitespace_only(text):
    assert word_count(text) == 0


def test_short_text_is_unchanged():
    assert truncate("hello", 10) == "hello"


def test_long_text_is_cut_with_suffix():
    assert truncate("hello world", 8) == "hello w…"


def test_width_smaller_than_suffix_raises():
    with pytest.raises(ValueError):
        truncate("hello", 0)

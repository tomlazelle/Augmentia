import pytest

from textkit import slugify, truncate


def test_short_text_is_unchanged():
    assert truncate("hello", 10) == "hello"


def test_long_text_is_cut_with_suffix():
    assert truncate("hello world", 8) == "hello w…"


def test_width_smaller_than_suffix_raises():
    with pytest.raises(ValueError):
        truncate("hello", 0)


def test_slugify_two_word_title():
    assert slugify("Hello World") == "hello-world"


def test_slugify_treats_punctuation_as_separator():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_multiple_spaces():
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"


def test_slugify_preserves_digits():
    assert slugify("Post 42") == "post-42"


def test_slugify_empty_string_returns_empty():
    assert slugify("") == ""


def test_slugify_only_punctuation_returns_empty():
    assert slugify("!!!") == ""


def test_slugify_collapses_symbol_runs():
    assert slugify("C++ Tips") == "c-tips"

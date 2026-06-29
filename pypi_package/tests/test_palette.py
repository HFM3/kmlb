"""Tests for the color palette and icon shorthands."""

import pytest

from kmlb import colors, icons
from kmlb.base import _resolve_color, _resolve_icon


# --- colors ----------------------------------------------------------------

def test_color_name():
    assert colors.get("red") == "#ff0000"


def test_color_name_case_insensitive():
    assert colors.get("RED") == "#ff0000"


def test_color_constant():
    assert colors.RED == "#ff0000"
    assert colors.KMLB_TEAL == "#1b8a9b"


def test_color_unknown_raises():
    with pytest.raises(ValueError):
        colors.get("notacolor")


def test_colors_names_listed():
    assert "red" in colors.names() and "kmlb_teal" in colors.names()


@pytest.mark.parametrize("value,expected", [
    ("red", ("#ff0000", 100)),
    ("#abcdef", ("#abcdef", 100)),
    (("red", 50), ("#ff0000", 50)),
    (("#abcdef", 25), ("#abcdef", 25)),
])
def test_resolve_color(value, expected):
    assert _resolve_color(value) == expected


def test_resolve_color_unknown_raises():
    with pytest.raises(ValueError):
        _resolve_color("nope")


# --- icons -----------------------------------------------------------------

def test_icon_shape():
    assert icons.get("triangle").endswith("shapes/triangle.png")


def test_icon_pin():
    assert icons.get("red-pin").endswith("pushpin/red-pushpin.png")


def test_icon_paddle_uses_paddle_abbreviation():
    assert icons.get("blue-paddle").endswith("paddle/blu-circle.png")


def test_icon_underscore_alias():
    assert icons.get("red_paddle") == icons.get("red-paddle")


def test_icon_url_passthrough():
    url = "http://example.com/custom.png"
    assert icons.get(url) == url


def test_icon_constant():
    assert icons.RED_PADDLE.endswith("paddle/red-circle.png")
    assert icons.TRIANGLE.endswith("shapes/triangle.png")


def test_icon_unknown_raises():
    with pytest.raises(ValueError):
        icons.get("notanicon")


def test_resolve_icon():
    assert _resolve_icon("triangle").endswith("shapes/triangle.png")
    assert _resolve_icon("http://x/y.png") == "http://x/y.png"

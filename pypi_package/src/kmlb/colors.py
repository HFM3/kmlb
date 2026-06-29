# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Named color presets.

A small, map-friendly palette so colors can be given by name instead of a hex
string. Anywhere a style takes a color you can pass a name (``"red"``), this
module's constant (``kmlb.colors.RED``), a bare hex string (``"#ff0000"``), or a
``(color, opacity)`` pair (``("red", 50)``).
"""

from __future__ import annotations

# Curated palette: the basic web colors, a few common extras, and the kmlb brand
# hues. Names are lowercase keys; values are #rrggbb strings.
_PALETTE = {
    "black":      "#000000",
    "white":      "#ffffff",
    "red":        "#ff0000",
    "lime":       "#00ff00",
    "green":      "#008000",
    "blue":       "#0000ff",
    "yellow":     "#ffff00",
    "cyan":       "#00ffff",
    "magenta":    "#ff00ff",
    "silver":     "#c0c0c0",
    "gray":       "#808080",
    "maroon":     "#800000",
    "olive":      "#808000",
    "navy":       "#000080",
    "teal":       "#008080",
    "purple":     "#800080",
    "orange":     "#ffa500",
    "pink":       "#ffc0cb",
    "brown":      "#a52a2a",
    "gold":       "#ffd700",
    "kmlb_teal":  "#1b8a9b",
    "kmlb_amber": "#f2a81d",
    "kmlb_green": "#36c23f",
    "kmlb_red":   "#e8472a",
}


def get(name: str) -> str:
    """Return the ``#rrggbb`` hex for a palette name (case-insensitive)."""
    try:
        return _PALETTE[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown color {name!r}. Available colors: {', '.join(names())}"
        ) from None


def names() -> list:
    """Return the sorted list of available color names."""
    return sorted(_PALETTE)


# Upper-case constants (e.g. ``kmlb.colors.RED``, ``kmlb.colors.KMLB_TEAL``).
globals().update({key.upper(): value for key, value in _PALETTE.items()})

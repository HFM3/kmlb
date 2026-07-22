# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Shorthand references for Google Earth's built-in marker icons.

Instead of a full ``mapfiles`` URL, ``point_style(icon=...)`` accepts a shorthand
key (``"triangle"``, ``"red-pin"``, ``"red-paddle"``), this module's constant
(``kmlb.icons.TRIANGLE``), or any full ``http`` URL. Keys are case-insensitive and
treat ``-`` and ``_`` the same.

Three families of built-in markers are covered:

- **shapes**   - ``circle``, ``square``, ``triangle``, ``star``, ``donut``, ...
- **pushpins** - ``<color>-pin`` (red/blue/green/yellow/ltblue/pink/purple/white)
- **paddles**  - ``<color>-paddle`` (the colored paddle markers)
"""

from __future__ import annotations

_BASE = "http://maps.google.com/mapfiles/kml/"

# Shape markers (paths relative to _BASE). Keys use hyphens.
_SHAPES = {
    "circle":     "shapes/placemark_circle.png",
    "square":     "shapes/placemark_square.png",
    "triangle":   "shapes/triangle.png",
    "star":       "shapes/star.png",
    "donut":      "shapes/donut.png",
    "diamond":    "shapes/open-diamond.png",
    "shaded-dot": "shapes/shaded_dot.png",
    "flag":       "shapes/flag.png",
    "info":       "shapes/info.png",
    "info-i":     "shapes/info-i.png",
    "caution":    "shapes/caution.png",
    "target":     "shapes/target.png",
    "arrow":      "shapes/arrow.png",
    "camera":     "shapes/camera.png",
    "dining":     "shapes/dining.png",
    "ferry":      "shapes/ferry.png",
    "plane":      "shapes/airports.png",
    "hiker":      "shapes/hiker.png",
    "golf":       "shapes/golf.png",
    "marina":     "shapes/marina.png",
    "parking":    "shapes/parking_lot.png",
    "ranger":     "shapes/ranger_station.png",
    "poi":        "shapes/poi.png",
    "taxi":       "shapes/cabs.png",
    # places & services
    "bar":        "shapes/bars.png",
    "coffee":     "shapes/coffee.png",
    "fuel":       "shapes/gas_stations.png",
    "grocery":    "shapes/grocery.png",
    "shopping":   "shapes/shopping.png",
    "lodging":    "shapes/lodging.png",
    "hospital":   "shapes/hospitals.png",
    "police":     "shapes/police.png",
    "fire":       "shapes/firedept.png",
    "phone":      "shapes/phone.png",
    "toilets":    "shapes/toilets.png",
    "water":      "shapes/water.png",
    "webcam":     "shapes/webcam.png",
    # recreation & outdoors
    "fishing":    "shapes/fishing.png",
    "cycling":    "shapes/cycling.png",
    "trail":      "shapes/trail.png",
    "picnic":     "shapes/picnic.png",
    "campground": "shapes/campground.png",
    "campfire":   "shapes/campfire.png",
    # transport
    "rail":       "shapes/rail.png",
    "bus":        "shapes/bus.png",
    "sailing":    "shapes/sailing.png",
    "heliport":   "shapes/heliport.png",
    "truck":      "shapes/truck.png",
}

# Colored pushpins. Friendly name -> Google's color abbreviation.
_PIN_COLORS = {"red": "red", "blue": "blue", "green": "grn", "yellow": "ylw",
               "ltblue": "ltblu", "pink": "pink", "purple": "purple", "white": "wht"}
_PINS = {f"{name}-pin": f"pushpin/{abbr}-pushpin.png" for name, abbr in _PIN_COLORS.items()}

# Colored paddles (Google's "paddle" circle markers). Note the abbreviations.
_PADDLE_COLORS = {"red": "red", "blue": "blu", "green": "grn", "yellow": "ylw",
                  "ltblue": "ltblu", "pink": "pink", "purple": "purple", "white": "wht"}
_PADDLES = {f"{name}-paddle": f"paddle/{abbr}-circle.png" for name, abbr in _PADDLE_COLORS.items()}

# Full registry: shorthand key -> absolute URL.
_ICONS = {key: _BASE + path for key, path in {**_SHAPES, **_PINS, **_PADDLES}.items()}


def get(name: str) -> str:
    """Resolve an icon shorthand (or full URL) to an absolute marker URL.

    A value beginning with ``http`` is returned unchanged. Otherwise the
    shorthand is looked up case-insensitively, treating ``-`` and ``_`` alike.
    """
    if name.startswith("http"):
        return name
    key = name.strip().lower().replace("_", "-")
    try:
        return _ICONS[key]
    except KeyError:
        raise ValueError(
            f"Unknown icon {name!r}. Available icons: {', '.join(names())}"
        ) from None


def names() -> list:
    """Return the sorted list of available icon shorthands."""
    return sorted(_ICONS)


# Upper-case constants (e.g. ``kmlb.icons.TRIANGLE``, ``kmlb.icons.RED_PADDLE``).
globals().update({key.upper().replace("-", "_"): url for key, url in _ICONS.items()})

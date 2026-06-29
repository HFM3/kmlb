# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""kmlb - A straightforward Google Earth KML builder.

The feature, style, and document builders live in :mod:`kmlb.base` and are
re-exported here, so ``kmlb.point(...)``, ``kmlb.kml(...)`` and friends work
directly. Higher-level shapes live in the :mod:`kmlb.shapes` submodule
(``kmlb.shapes.wedge``). Geodesic measurements
(``kmlb.distance``, ``kmlb.bearing``, ``kmlb.destination``) live in
:mod:`kmlb.geodesy` and are re-exported here.
"""

from __future__ import annotations

from . import colors, icons, shapes
from .base import (
    folder,
    kml,
    line,
    line_style,
    look_at,
    networklink_kml,
    point,
    point_style,
    polygon,
    polygon_style,
    search_poi,
)
from .geodesy import bearing, destination, distance

__version__ = "0.1.0"

__all__ = [
    "look_at",
    "point",
    "search_poi",
    "line",
    "polygon",
    "point_style",
    "line_style",
    "polygon_style",
    "folder",
    "kml",
    "networklink_kml",
    "distance",
    "bearing",
    "destination",
    "colors",
    "icons",
    "shapes",
]

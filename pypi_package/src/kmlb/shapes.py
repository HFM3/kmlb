# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Higher-level shape builders composed from the base KML primitives."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Sequence

from . import base
from .geodesy import destination

__all__ = ["wedge"]


def wedge(center: Sequence[float], azimuth: float, width: float, radius: float,
          *, steps: int = 15, name: str = 'Wedge', **kwargs) -> ET.Element:
    """
    Creates a pie-wedge shaped KML polygon.

    OVERVIEW:
        Creates a pie-wedge shaped polygon that can be included in a KML document.

        A wedge maps naturally onto a cellular coverage sector: ``azimuth`` is the
        direction the antenna faces, ``width`` is the sector's beamwidth, and
        ``radius`` is its reach. That makes ``wedge`` a convenient way to visualize
        a cell tower's sector width, direction, and reach on the map.

    INPUTS:
        center (List of three Floats):
            A list of [x, y, z] coordinates that will be the origin of the pie wedge.
        azimuth (Float):
            The direction that the center of the wedge's arc will point. 0 = True North.
        width (Float):
            The width of the wedge in degrees.
        radius (Float):
            The length of the wedge's straight edges, in meters.
        steps (Integer) [Optional]:
            The number of vertices along the curved edge of the wedge. More steps will make a smoother arc.
            (Default = 15)
        name (String) [Optional]:
            The name to be given to the wedge object within the KML.
            (Default = 'Wedge')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        wedge (Element):
            An XML element representing a KML polygon.
    """

    # Attribute table
    headers_default = ['Azimuth', 'Width', 'Radius', 'Steps', 'Center Lat', 'Center Lng', 'Center Z']
    headers = kwargs.pop('headers', headers_default)

    attrs_default = [azimuth, width, radius, steps, center[1], center[0], center[2]]
    attrs = kwargs.pop('attrs', attrs_default)

    # Starting azimuth is a 1/2 width clockwise from the provided azimuth.
    start_az = (azimuth + width / 2) % 360
    step_degrees = width / (steps - 1)

    # Determine the azimuth of each step
    azimuths = [(start_az - i * step_degrees) % 360 for i in range(steps)]

    # Calculate the coordinates of the steps along the wedge's arc.
    coords = [destination(center, az, radius) for az in azimuths]

    # Add the wedge vertex as the initial and final coordinate to close the polygon.
    coords.insert(0, center)
    coords.append(center)

    # Create polygon
    wedge_poly = base.polygon([coords], name, headers=headers, attrs=attrs, **kwargs)

    return wedge_poly

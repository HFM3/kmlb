# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Higher-level shape builders composed from the base KML primitives."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import List, Literal, Optional, Sequence

from . import base
from .base import AltitudeMode, ColorInput, _floatify
from .geodesy import bearing, destination, distance

# The default flat-polygon (cell) outline color; grid labels match it unless the
# caller passes its own 'label_color'.
_CELL_OUTLINE = ("#ffff00", 100)

__all__ = ["wedge", "circle", "ellipse", "rectangle", "ngon", "annulus", "arc",
           "ribbon", "con_rings", "fishnet", "hex_grid", "hex_field",
           "fresnel_zone", "cylinder", "cone", "dome", "sphere",
           "cube", "pyramid", "soccer_ball", "PYRAMID_PALETTE"]

_LIGHT_SPEED = 299_792_458.0   # meters per second

# The anchor names accepted by the 3D solids. As a Literal this gives editors the
# one-of-three completion and lets type checkers flag typos before runtime; each
# solid still guards the value at runtime and raises on anything else.
Anchor = Literal["base", "center", "top"]

# Default fill colors for an unstyled pyramid, keyed by base edge count so a
# triangular, square, pentagonal, ... pyramid each reads a different color. Index
# with '(sides - 3) % len', so 3 -> [0], 4 -> [1], ... and higher counts cycle.
PYRAMID_PALETTE = [
    ('kmlb_red', 55),    # 3 sides (triangular)
    ('gold', 55),        # 4 sides (square)
    ('purple', 55),      # 5 sides (pentagonal)
    ('kmlb_teal', 55),   # 6 sides (hexagonal)
]


def _tilt_wedge_coord(center: Sequence[float], boresight: float, vertex_az: float,
                      radius: float, tilt: float) -> List[float]:
    """
    Lifts one wedge arc vertex out of the horizontal plane.

    The sector is rotated rigidly by 'tilt' degrees (positive up, negative down)
    about the horizontal axis that passes through 'center' perpendicular to the
    boresight (the wedge's central azimuth). This is Rodrigues' rotation of the
    vertex about that axis; horizontal placement reuses the geodesic 'destination'
    so the result stays on the WGS-84 ellipsoid. Returns a [lon, lat, z] coord.

    At 'tilt' = 0 this reduces exactly to a flat arc vertex at the center's
    altitude, so untilted wedges are unaffected.
    """

    t = math.radians(tilt)
    off = math.radians(vertex_az - boresight)   # angular offset from the boresight
    va = math.radians(vertex_az)
    ba = math.radians(boresight)
    cos_t = math.cos(t)

    # Local East/North offset of the untilted vertex, relative to the center.
    e0 = radius * math.sin(va)
    n0 = radius * math.cos(va)

    # Component along the (horizontal) rotation axis is preserved by the tilt.
    s = radius * math.sin(off)

    e1 = e0 * cos_t + math.cos(ba) * s * (1 - cos_t)
    n1 = n0 * cos_t - math.sin(ba) * s * (1 - cos_t)
    up = radius * math.cos(off) * math.sin(t)

    new_bearing = math.degrees(math.atan2(e1, n1)) % 360
    new_dist = math.hypot(e1, n1)

    lon, lat = destination(center, new_bearing, new_dist)[:2]
    return [lon, lat, center[2] + up]


def wedge(origin: Sequence[float], azimuth: float, width: float, radius: float,
          *, tilt: float = 0.0, steps: int = 15, name: str = 'Wedge',
          **kwargs) -> ET.Element:
    """
    Creates a pie-wedge shaped KML polygon.

    OVERVIEW:
        Creates a pie-wedge shaped polygon that can be included in a KML document.

        A wedge maps naturally onto a cellular coverage sector: ``azimuth`` is the
        direction the antenna faces, ``width`` is the sector's beamwidth, and
        ``radius`` is its reach. That makes ``wedge`` a convenient way to visualize
        a cell tower's sector width, direction, and reach on the map.

        ``tilt`` adds an antenna-style elevation tilt, rotating the whole sector up
        or down out of the horizontal plane about its origin.

    INPUTS:
        origin (List of three Floats):
            A list of [x, y, z] coordinates for the origin of the pie wedge (the point
            where its two straight edges meet), which the arc opens out from.
        azimuth (Float):
            The direction the wedge faces: the bearing to the middle of its arc.
            0 = True North.
        width (Float):
            The width of the wedge in degrees.
        radius (Float):
            The length of the wedge's straight edges, in meters.
        tilt (Float) [Optional]:
            An elevation tilt of the whole sector in degrees (Default = 0.0).
            A value of 0 keeps the wedge flat on the ground.
            A value of -90 points the sector straight down.
            A value of 90 points the sector straight up.
            A nonzero tilt lifts vertices off the ground, so it only renders under
            a non-clamped altitude mode: when 'z_mode' is not supplied it defaults
            to 'ABS' and the origin's z is treated as an absolute (MSL) altitude.
            Pass an explicit 'z_mode' to override.
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

    origin = _floatify(origin)
    azimuth, width, radius, tilt = float(azimuth), float(width), float(radius), float(tilt)
    steps = int(steps)
    if steps < 2:
        raise ValueError("wedge requires steps of at least 2.")

    # Attribute table
    headers_default = ['Azimuth', 'Width (deg)', 'Radius (m)', 'Tilt', 'Steps', 'Origin Lat', 'Origin Lng', 'Origin Z']
    headers = kwargs.pop('headers', headers_default)

    attrs_default = [azimuth, width, radius, tilt, steps, origin[1], origin[0], origin[2]]
    attrs = kwargs.pop('attrs', attrs_default)

    # Starting azimuth is a 1/2 width clockwise from the provided azimuth.
    start_az = (azimuth + width / 2) % 360
    step_degrees = width / (steps - 1)

    # Determine the azimuth of each step
    azimuths = [(start_az - i * step_degrees) % 360 for i in range(steps)]

    # Calculate the coordinates of the steps along the wedge's arc. A tilt lifts
    # the arc out of the horizontal plane and needs an altitude mode that honors
    # the resulting elevations, so absolute is used unless the caller overrides.
    if tilt == 0:
        coords = [destination(origin, az, radius) for az in azimuths]
    else:
        coords = [_tilt_wedge_coord(origin, azimuth, az, radius, tilt) for az in azimuths]
        kwargs.setdefault('z_mode', 'ABS')

    # Add the wedge vertex as the initial and final coordinate to close the polygon.
    coords.insert(0, origin)
    coords.append(origin)

    # Create polygon
    wedge_poly = base.polygon([coords], name, headers=headers, attrs=attrs, **kwargs)

    return wedge_poly


def circle(center: Sequence[float], radius: float, *, steps: int = 48,
           name: str = 'Circle', **kwargs) -> ET.Element:
    """
    Creates a circular KML polygon.

    OVERVIEW:
        Approximates a circle of a given radius (in meters) around a center point
        with a regular polygon of 'steps' vertices, projected across the WGS-84
        ellipsoid.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the circle's center.
        radius (Float):
            The circle's radius, in meters.
        steps (Integer) [Optional]:
            The number of vertices around the circle; more gives a smoother edge.
            (Default = 48)
        name (String) [Optional]:
            The name given to the circle within the KML. (Default = 'Circle')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        circle (Element):
            An XML element representing a KML polygon.
    """

    center = _floatify(center)
    radius, steps = float(radius), int(steps)
    if steps < 3:
        raise ValueError("circle requires steps of at least 3.")
    headers_default = ['Radius (m)', 'Steps', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [radius, steps, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    ring = [destination(center, i * 360 / steps, radius) for i in range(steps)]
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def ellipse(center: Sequence[float], semi_major: float, semi_minor: float, *,
            orient: float = 0.0, steps: int = 64, name: str = 'Ellipse',
            **kwargs) -> ET.Element:
    """
    Creates an elliptical KML polygon.

    OVERVIEW:
        Builds an ellipse from its two semi-axis lengths (in meters) and an
        orientation. At 'orient' = 0 the major axis runs north-south; increasing
        'orient' rotates the major axis clockwise (degrees from true north).

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the ellipse's center.
        semi_major (Float):
            Half the length of the long axis, in meters.
        semi_minor (Float):
            Half the length of the short axis, in meters.
        orient (Float) [Optional]:
            Clockwise rotation of the major axis, in degrees from true north.
            (Default = 0.0)
        steps (Integer) [Optional]:
            The number of vertices around the ellipse. (Default = 64)
        name (String) [Optional]:
            The name given to the ellipse within the KML. (Default = 'Ellipse')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        ellipse (Element):
            An XML element representing a KML polygon.
    """

    center = _floatify(center)
    semi_major, semi_minor, orient, steps = float(semi_major), float(semi_minor), float(orient), int(steps)
    if steps < 3:
        raise ValueError("ellipse requires steps of at least 3.")
    headers_default = ['Semi-Major (m)', 'Semi-Minor (m)', 'Orient', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [semi_major, semi_minor, orient, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    o = math.radians(orient)
    ring = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x, y = semi_major * math.cos(t), semi_minor * math.sin(t)   # x along the major axis
        east = x * math.sin(o) + y * math.cos(o)
        north = x * math.cos(o) - y * math.sin(o)
        ring.append(_enu(center, east, north))
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def rectangle(corner: Sequence[float], width: float, height: float, *,
              azimuth: float = 90.0, name: str = 'Rectangle', **kwargs) -> ET.Element:
    """
    Creates a rectangular KML polygon.

    OVERVIEW:
        Builds a rectangle anchored at 'corner'. 'azimuth' is the compass bearing
        (degrees from true north) of the rectangle's first edge, the 'width' edge
        that runs from the corner: the default 90 runs 'width' due east and 'height'
        due south, an upright north-up box, so 'corner' is the upper-left corner.
        'azimuth' = 0 would point the first edge due north; increasing 'azimuth'
        turns the whole rectangle clockwise about the corner, so it can line up with
        a feature that is not north-up (which corner of the box 'corner' represents
        turns with it). ('height' always runs 90 degrees clockwise of 'width'.)

    INPUTS:
        corner (List of Floats):
            A [lon, lat] or [lon, lat, z] anchor coordinate (the rectangle's upper-
            left corner at the default azimuth of 90).
        width (Float):
            The length of the first edge (the one bearing 'azimuth'), in meters.
        height (Float):
            The length of the perpendicular edge (90 degrees clockwise of 'width'),
            in meters.
        azimuth (Float) [Optional]:
            Compass bearing of the first ('width') edge, in degrees from true north
            (0 = north, 90 = east). (Default = 90.0, i.e. width runs due east.)
        name (String) [Optional]:
            The name given to the rectangle within the KML. (Default = 'Rectangle')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        rectangle (Element):
            An XML element representing a KML polygon.
    """

    corner = _floatify(corner)
    width, height, azimuth = float(width), float(height), float(azimuth)
    headers_default = ['Width (m)', 'Height (m)', 'Azimuth', 'Corner Lat', 'Corner Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [width, height, azimuth, corner[1], corner[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    # 'azimuth' is the bearing of the first edge; the rotation is measured from
    # the east-marching default, so subtract 90 (azimuth 90 = east = no rotation).
    a = math.radians(azimuth - 90.0)
    cos_a, sin_a = math.cos(a), math.sin(a)

    def place(east, north):
        # Rotate the local offset clockwise, then project geodesically from the corner.
        return _enu(corner, east * cos_a + north * sin_a, -east * sin_a + north * cos_a)

    # In the local frame, march along 'width', then 90 degrees clockwise for 'height'.
    ring = [place(0, 0), place(width, 0), place(width, -height), place(0, -height)]
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def ngon(center: Sequence[float], radius: float, sides: int, *, orient: float = 0.0,
         name: str = 'Ngon', **kwargs) -> ET.Element:
    """
    Creates a regular-polygon KML polygon.

    OVERVIEW:
        Builds a regular polygon of 'sides' equal edges, with each vertex 'radius'
        meters from the center. 'orient' turns the shape clockwise; at 'orient' = 0
        the first vertex points due north.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the polygon's center.
        radius (Float):
            The distance from the center to each vertex, in meters.
        sides (Integer):
            The number of sides (3 = triangle, 5 = pentagon, 6 = hexagon).
        orient (Float) [Optional]:
            Clockwise rotation of the first vertex, in degrees from true north.
            (Default = 0.0)
        name (String) [Optional]:
            The name given to the polygon within the KML. (Default = 'Ngon')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        ngon (Element):
            An XML element representing a KML polygon.
    """

    sides = int(sides)
    if sides < 3:
        raise ValueError("ngon requires at least 3 sides.")

    center = _floatify(center)
    radius, orient = float(radius), float(orient)
    headers_default = ['Sides', 'Radius (m)', 'Orient', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [sides, radius, orient, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    ring = [destination(center, orient + i * 360 / sides, radius) for i in range(sides)]
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def annulus(center: Sequence[float], inner_radius: float, outer_radius: float, *,
            steps: int = 48, name: str = 'Annulus', **kwargs) -> ET.Element:
    """
    Creates an annular (ring) KML polygon.

    OVERVIEW:
        Builds a filled ring: an outer circle of 'outer_radius' with a concentric
        inner circle of 'inner_radius' punched out as a hole. Both circles are
        approximated with 'steps' vertices. The radii are given inner first, then
        outer (smallest to largest).

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the ring's center.
        inner_radius (Float):
            The inner (hole) radius, in meters. Must be smaller than outer_radius.
        outer_radius (Float):
            The outer edge radius, in meters.
        steps (Integer) [Optional]:
            The number of vertices around each circle. (Default = 48)
        name (String) [Optional]:
            The name given to the ring within the KML. (Default = 'Annulus')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        annulus (Element):
            An XML element representing a KML polygon with one hole.
    """

    inner_radius, outer_radius, steps = float(inner_radius), float(outer_radius), int(steps)
    if steps < 3:
        raise ValueError("annulus requires steps of at least 3.")
    if inner_radius >= outer_radius:
        raise ValueError("annulus inner_radius must be smaller than outer_radius.")

    center = _floatify(center)
    headers_default = ['Inner (m)', 'Outer (m)', 'Steps', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [inner_radius, outer_radius, steps, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    outer = [destination(center, i * 360 / steps, outer_radius) for i in range(steps)]
    inner = [destination(center, i * 360 / steps, inner_radius) for i in range(steps)]
    outer.append(outer[0])
    inner.append(inner[0])

    return base.polygon([outer, inner], name, headers=headers, attrs=attrs, **kwargs)


def arc(center: Sequence[float], radius: float, start_az: float, end_az: float, *,
        steps: int = 32, name: str = 'Arc', **kwargs) -> ET.Element:
    """
    Creates an arc as a KML line.

    OVERVIEW:
        Draws a curved path at a fixed 'radius' from a center point, sweeping from
        'start_az' to 'end_az' (degrees from true north). Handy for range-of-reach
        arcs and fields of fire. The sweep runs in increasing-azimuth order; give
        an 'end_az' below 'start_az' (or add 360) to sweep the other way.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the arc's center.
        radius (Float):
            The arc's radius, in meters.
        start_az (Float):
            The starting azimuth, in degrees from true north.
        end_az (Float):
            The ending azimuth, in degrees from true north.
        steps (Integer) [Optional]:
            The number of segments along the arc. (Default = 32)
        name (String) [Optional]:
            The name given to the arc within the KML. (Default = 'Arc')
        **kwargs:
            Any keyword argument accepted by the kmlb.line function.

    OUTPUT:
        arc (Element):
            An XML element representing a KML line.
    """

    center = _floatify(center)
    radius, start_az, end_az, steps = float(radius), float(start_az), float(end_az), int(steps)
    headers_default = ['Radius (m)', 'Start Az', 'End Az', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [radius, start_az, end_az, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    coords = [destination(center, start_az + (end_az - start_az) * i / steps, radius)
              for i in range(steps + 1)]

    return base.line(coords, name, headers=headers, attrs=attrs, **kwargs)


def ribbon(path: Sequence[Sequence[float]], width, *,
           name: str = 'Ribbon', **kwargs) -> ET.Element:
    """
    Creates a ribbon (buffer) around a path, as a KML polygon.

    OVERVIEW:
        Buffers an open path into a polygon by offsetting each vertex along the
        bisector of its turn (a miter join), so the ribbon keeps an even width
        through bends. Useful for trails, rail lines, pipelines, and flight
        corridors.

        'width' can be a single value for an even-width ribbon, or a list with one
        width per path point for a ribbon that widens and narrows along its length
        (a hurricane track's wind field, a river that broadens, a variable buffer).

    INPUTS:
        path (List of Coordinates):
            An ordered list of [lon, lat] or [lon, lat, z] coordinates (2 or more).
        width (Float or List of Floats):
            The ribbon's total width, in meters. A single value gives an even
            width; a list (one value per path point) sets the width at each point
            and tapers linearly between them.
        name (String) [Optional]:
            The name given to the ribbon within the KML. (Default = 'Ribbon')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        ribbon (Element):
            An XML element representing a KML polygon.
    """

    path = [_floatify(p) for p in path]
    m = len(path)
    if m < 2:
        raise ValueError("ribbon requires a path of at least 2 points.")

    # Broadcast a scalar width to one value per point; a list must match the path.
    if isinstance(width, (int, float)):
        widths = [float(width)] * m
    else:
        widths = [float(w) for w in width]
        if len(widths) != m:
            raise ValueError("ribbon width list must have one value per path point.")

    headers_default = ['Min Width (m)', 'Max Width (m)', 'Points']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [min(widths), max(widths), m]
    attrs = kwargs.pop('attrs', attrs_default)

    left, right = [], []
    for i, p in enumerate(path):
        hw = widths[i] / 2                                # half-width at this vertex
        b_in = bearing(path[max(i - 1, 0)], path[max(i, 1)])
        b_out = bearing(path[min(i, m - 2)], path[min(i + 1, m - 1)])
        turn = ((b_out - b_in + 180) % 360) - 180        # signed deflection at the vertex
        bis = (b_in + turn / 2) % 360                     # path direction through the vertex
        c = math.cos(math.radians(turn / 2))
        step = hw / c if abs(c) > 1e-6 else hw            # miter length keeps the width even
        left.append(destination(p, (bis - 90) % 360, step))
        right.append(destination(p, (bis + 90) % 360, step))
    ring = left + right[::-1] + [left[0]]

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def con_rings(center: Sequence[float], radii: Optional[Sequence[float]] = None, *,
              start: Optional[float] = None, interval: Optional[float] = None,
              count: Optional[int] = None,
              steps: int = 48, name: str = 'Concentric Rings',
              collapsed: bool = True, hidden: bool = False,
              **kwargs) -> ET.Element:
    """
    Creates a set of concentric range rings as a KML folder of lines.

    OVERVIEW:
        Draws one unfilled circle outline (a closed line) at each radius and
        returns them in a folder, so each ring can be toggled on its own. Handy for
        range rings around a point (a light, a radar, a siren).

        The radii can be given two ways: pass an explicit list as 'radii', or
        generate an evenly spaced series with 'start', 'interval', and 'count'
        (radii become start, start + interval, start + 2*interval, ...). Provide
        one form or the other.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate all rings share.
        radii (List of Floats) [Optional]:
            An explicit radius, in meters, for each ring. If None (the default),
            the ring radii are built from 'start', 'interval', and 'count'.
        start (Float) [Optional]:
            The radius of the innermost ring, in meters (generator form).
        interval (Float) [Optional]:
            The spacing between successive rings, in meters (generator form).
        count (Integer) [Optional]:
            The number of rings to generate (generator form).
        steps (Integer) [Optional]:
            The number of vertices around each ring. (Default = 48)
        name (String) [Optional]:
            The folder name. (Default = 'Concentric Rings')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.line function; applied to
            every ring.

    OUTPUT:
        con_rings (Element):
            An XML element representing a KML folder of line rings.
    """

    center = _floatify(center)
    steps = int(steps)
    if steps < 3:
        raise ValueError("con_rings requires steps of at least 3.")
    if radii is None:
        if start is None or interval is None or count is None:
            raise ValueError(
                "con_rings needs either 'radii' or all of "
                "'start', 'interval', and 'count'.")
        start, interval, count = float(start), float(interval), int(count)
        radii = [start + i * interval for i in range(count)]
    else:
        radii = [float(r) for r in radii]

    headers = kwargs.pop('headers', None)
    attrs = kwargs.pop('attrs', None)

    rings = []
    for ring_no, r in enumerate(radii, 1):
        coords = [destination(center, i * 360 / steps, r) for i in range(steps)]
        coords.append(coords[0])
        ring_headers = (headers if headers is not None
                        else ['Ring', 'Radius (m)', 'Steps', 'Center Lat', 'Center Lng'])
        ring_attrs = (attrs if attrs is not None
                      else [ring_no, r, steps, center[1], center[0]])
        rings.append(base.line(coords, f'{r:.0f} m',
                               headers=ring_headers, attrs=ring_attrs, **kwargs))

    return base.folder(name, rings, collapsed=collapsed, hidden=hidden)


def _cell_id(ids, r: int, c: int, cols: int):
    """Resolve a grid cell's ID/name for row 'r', column 'c'.

    'ids' may be None (an auto id like 'r0c2' is returned), a nested rows-by-cols
    list ('ids[r][c]'), or a flat list in row-major order ('ids[r*cols + c]').
    """
    if ids is None:
        return f"r{r}c{c}"
    if ids and isinstance(ids[0], (list, tuple)):
        return ids[r][c]
    return ids[r * cols + c]


def _check_ids(ids, rows: int, cols: int) -> None:
    """Guard that a grid's 'ids' matches its shape, with a clear message.

    'ids' may be None, a nested 'rows' by 'cols' list, or a flat row-major list of
    'rows * cols' values.
    """
    if ids is None:
        return
    if ids and isinstance(ids[0], (list, tuple)):
        if len(ids) != rows or any(len(row) != cols for row in ids):
            raise ValueError(f"ids nested list must be {rows} rows by {cols} columns.")
    elif len(ids) != rows * cols:
        raise ValueError(f"ids must have rows*cols = {rows * cols} entries, got {len(ids)}.")


def _cell_polygon(ring, cell_id, r: int, c: int, kwargs):
    """Build one clickable grid cell as a KML polygon.

    The cell is named by its ID and, unless the caller supplied its own
    headers/attrs through kwargs, carries an ID/Row/Column attribute table so it
    is clickable with a description balloon. Remaining kwargs (style, z_mode, ...)
    apply to every cell.
    """
    cell_kwargs = dict(kwargs)
    headers = cell_kwargs.pop('headers', ['ID', 'Row', 'Column'])
    attrs = cell_kwargs.pop('attrs', [cell_id, r, c])
    return base.polygon([ring], str(cell_id), headers=headers, attrs=attrs, **cell_kwargs)


def _hex_spiral(rings: int):
    """Axial (q, r) of a filled hexagon's cells as a continuous spiral from the center.

    Index 0 is the center, then the cells spiral outward so consecutive cells are
    always neighbors: each ring is entered by one step out from the end of the
    previous ring, then walked around (cells 2-7 the first ring, 8-19 the second,
    ...). Numbering the cells in this order follows the spiral without jumps.
    """
    dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]   # the 6 hex neighbors
    coords = [(0, 0)]
    q, r = 0, 0
    for k in range(1, rings + 1):
        q, r = q, r + 1                          # step out into the next ring
        coords.append((q, r))
        for side, (de, dn) in enumerate(dirs):   # walk the ring; first side is short
            for _ in range(k - 1 if side == 0 else k):
                q, r = q + de, r + dn
                coords.append((q, r))
    return coords


def _hex_cell_polygon(ring, cell_id, ring_no: int, kwargs):
    """Build one clickable hex cell as a KML polygon with an ID/Ring attribute table."""
    cell_kwargs = dict(kwargs)
    headers = cell_kwargs.pop('headers', ['ID', 'Ring'])
    attrs = cell_kwargs.pop('attrs', [cell_id, ring_no])
    return base.polygon([ring], str(cell_id), headers=headers, attrs=attrs, **cell_kwargs)


def _cell_centroid(ring):
    """[lon, lat, z] centroid of a cell's outer ring (its closing vertex dropped)."""
    pts = ring[:-1]
    n = len(pts)
    return [sum(p[i] for p in pts) / n for i in range(3)]


def _labels_folder(labels, z_mode: AltitudeMode, grid_name: str,
                   dot_color: ColorInput) -> ET.Element:
    """A 'Labels' subfolder: a small-dot + text point at each (coords, text) pair.

    One shared point style, built with 'kmlb.point_style' and scoped to the grid by
    name, is defined in the folder and referenced by every label, so the labels sit
    in their own folder and toggle on their own in the places panel. The dot is drawn
    in 'dot_color' (the cells' outline color by default) so the labels read as part
    of the grid.
    """
    style_id = grid_name.strip().lower().replace(" ", "-") + "-labels"
    style = base.point_style(style_id, icon="circle", color=dot_color,
                             scale=1.0, label_color=("#ffffff", 100), label_size=0.9)
    points = [base.point(coords, text, style_to_use=style_id, z_mode=z_mode)
              for coords, text in labels]
    return base.folder("Labels", [style] + points, collapsed=True, hidden=False)


def fishnet(corner: Sequence[float], cell_dim, cols: int, rows: int, *,
            azimuth: float = 90.0, ids: Optional[Sequence] = None, labels: bool = False,
            label_color: Optional[ColorInput] = None,
            name: str = 'Fishnet', collapsed: bool = True, hidden: bool = False,
            **kwargs) -> ET.Element:
    """
    Creates a rectangular fishnet grid as a KML folder of polygon cells.

    OVERVIEW:
        Tiles a 'cols' by 'rows' grid of rectangular cells starting from an upper-
        left 'corner' and returns them in a folder. Cells march along the top edge
        (increasing column) and 90 degrees clockwise of it (increasing row).

        'cell_dim' sets the cell size: a single value makes square cells of that
        side length; a pair '[x, y]' makes rectangular cells 'x' meters along the
        column direction by 'y' meters along the row direction. 'azimuth' is the
        compass bearing of the top edge (the column direction): the default 90 runs
        columns due east and rows due south, a north-up grid. Increasing 'azimuth'
        turns the whole grid clockwise about the corner, so the cells can line up
        with a feature that is not north-up (a rotated parking lot, a runway apron,
        a survey block).

        Each cell is clickable: pass 'ids' to name the cells and every cell carries
        an ID/Row/Column attribute table.

    INPUTS:
        corner (List of Floats):
            A [lon, lat] or [lon, lat, z] anchor coordinate (the grid's upper-left
            corner at the default azimuth of 90).
        cell_dim (Float or List of two Floats):
            A single side length for square cells, or '[x, y]' for rectangular
            cells ('x' along the columns, 'y' along the rows), in meters.
        cols (Integer):
            The number of columns.
        rows (Integer):
            The number of rows.
        azimuth (Float) [Optional]:
            Compass bearing of the top (column) edge, in degrees from true north
            (0 = north, 90 = east). (Default = 90.0, i.e. columns run due east.)
        ids (List) [Optional]:
            Cell IDs, as a flat row-major list ('rows * cols' values) or a nested
            'rows' by 'cols' list. Each ID names its cell and appears in the cell's
            attribute table. When omitted, cells are named 'r{row}c{col}'.
        labels (Boolean) [Optional]:
            True puts the cells in a 'Cells' subfolder and adds a sibling 'Labels'
            subfolder with a text label at each cell's centroid (named by the cell's
            ID), so each toggles on its own. (Default = False)
        label_color (Tuple) [Optional]:
            Color (hex, opacity) for the label dots. When None, they match the cells'
            outline color. (Default = None)
        name (String) [Optional]:
            The folder name. (Default = 'Fishnet')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function; applied to
            every cell.

    OUTPUT:
        fishnet (Element):
            An XML element representing a KML folder of polygon cells.
    """

    cols, rows = int(cols), int(rows)
    if cols < 1 or rows < 1:
        raise ValueError("fishnet requires cols and rows of at least 1.")
    _check_ids(ids, rows, cols)

    corner = _floatify(corner)
    azimuth = float(azimuth)
    if isinstance(cell_dim, (int, float)):
        cw = ch = float(cell_dim)
    else:
        cw, ch = float(cell_dim[0]), float(cell_dim[1])

    # 'azimuth' is the bearing of the column (top-edge) direction; the rotation is
    # measured from the east-marching default, so subtract 90 (azimuth 90 = east).
    a = math.radians(azimuth - 90.0)
    cos_a, sin_a = math.cos(a), math.sin(a)

    def place(east, north):
        # Rotate the local offset clockwise, then project geodesically from the corner.
        return _enu(corner, east * cos_a + north * sin_a, -east * sin_a + north * cos_a)

    cells, label_data = [], []
    for r in range(rows):
        for c in range(cols):
            x0, x1 = c * cw, (c + 1) * cw            # east edges
            y0, y1 = -r * ch, -(r + 1) * ch          # north edges (rows go south)
            ring = [place(x0, y0), place(x1, y0), place(x1, y1), place(x0, y1)]
            ring.append(ring[0])
            cid = _cell_id(ids, r, c, cols)
            cells.append(_cell_polygon(ring, cid, r, c, kwargs))
            if labels:
                label_data.append((_cell_centroid(ring), cid))

    if labels:
        # put the cells and the labels in their own sibling subfolders so each
        # toggles on its own in the places panel.
        parts = [base.folder("Cells", cells, collapsed=True, hidden=False),
                 _labels_folder(label_data, kwargs.get("z_mode", "CTG"), name,
                                label_color or _CELL_OUTLINE)]
        return base.folder(name, parts, collapsed=collapsed, hidden=hidden)
    return base.folder(name, cells, collapsed=collapsed, hidden=hidden)


def hex_grid(corner: Sequence[float], cell: float, cols: int, rows: int, *,
             azimuth: float = 90.0, ids: Optional[Sequence] = None, labels: bool = False,
             label_color: Optional[ColorInput] = None,
             name: str = 'Hex Grid', collapsed: bool = True, hidden: bool = False,
             **kwargs) -> ET.Element:
    """
    Creates a hexagonal grid as a KML folder of polygon cells.

    OVERVIEW:
        Tiles a 'cols' by 'rows' lattice of flat-top hexagons starting from an
        upper-left 'corner' and returns them in a folder. Each hexagon has a radius
        of 'cell' meters (center to vertex) and the cells interlock edge to edge.

        'azimuth' is the compass bearing of the column direction: the default 90
        marches columns due east, a north-up lattice. Increasing 'azimuth' turns the
        whole grid clockwise about the corner. The rotation is rigid, so the
        hexagons stay tessellated (neighbors keep their shared edges) at any azimuth.

        Each cell is clickable: pass 'ids' to name the cells and every cell carries
        an ID/Row/Column attribute table.

    INPUTS:
        corner (List of Floats):
            A [lon, lat] or [lon, lat, z] anchor coordinate (the grid's upper-left
            corner at the default azimuth of 90).
        cell (Float):
            The hexagon radius (center to vertex), in meters.
        cols (Integer):
            The number of columns.
        rows (Integer):
            The number of rows.
        azimuth (Float) [Optional]:
            Compass bearing of the column direction, in degrees from true north
            (0 = north, 90 = east). (Default = 90.0, i.e. columns run due east.)
        ids (List) [Optional]:
            Cell IDs, as a flat row-major list ('rows * cols' values) or a nested
            'rows' by 'cols' list. Each ID names its cell and appears in the cell's
            attribute table. When omitted, cells are named 'r{row}c{col}'.
        labels (Boolean) [Optional]:
            True puts the cells in a 'Cells' subfolder and adds a sibling 'Labels'
            subfolder with a text label at each cell's centroid (named by the cell's
            ID), so each toggles on its own. (Default = False)
        label_color (Tuple) [Optional]:
            Color (hex, opacity) for the label dots. When None, they match the cells'
            outline color. (Default = None)
        name (String) [Optional]:
            The folder name. (Default = 'Hex Grid')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function; applied to
            every cell.

    OUTPUT:
        hex_grid (Element):
            An XML element representing a KML folder of polygon cells.
    """

    cols, rows = int(cols), int(rows)
    if cols < 1 or rows < 1:
        raise ValueError("hex_grid requires cols and rows of at least 1.")
    _check_ids(ids, rows, cols)

    corner = _floatify(corner)
    cell, azimuth = float(cell), float(azimuth)

    # 'azimuth' is the bearing of the column direction; the rotation is measured
    # from the east-marching default, so subtract 90 (azimuth 90 = east).
    a = math.radians(azimuth - 90.0)
    cos_a, sin_a = math.cos(a), math.sin(a)

    def place(east, north):
        # Rigid clockwise rotation about the corner, then project. Applying the same
        # rotation to every vertex (hub offset included) keeps the lattice
        # tessellated at any azimuth.
        return _enu(corner, east * cos_a + north * sin_a, -east * sin_a + north * cos_a)

    # Flat-top hexagons: columns step 1.5*radius apart, rows step sqrt(3)*radius,
    # and odd columns shift half a row so the cells interlock edge to edge. The six
    # vertices sit at 0, 60, ... 300 degrees around each hub (a vertex points east).
    dx, dy = cell * 1.5, cell * math.sqrt(3)
    verts = [(cell * math.cos(math.radians(k * 60)), cell * math.sin(math.radians(k * 60)))
             for k in range(6)]

    # Offset the hub lattice so the first hexagon's top-left bounding edges touch
    # the corner (its left vertex at the corner's longitude, its top at the
    # corner's latitude), matching fishnet's upper-left corner anchoring.
    off_e, off_n = cell, -dy / 2

    cells, label_data = [], []
    for r in range(rows):
        for c in range(cols):
            hub_e = off_e + c * dx
            hub_n = off_n - (r * dy + (dy / 2 if c % 2 else 0))
            ring = [place(hub_e + ve, hub_n + vn) for ve, vn in verts]
            ring.append(ring[0])
            cid = _cell_id(ids, r, c, cols)
            cells.append(_cell_polygon(ring, cid, r, c, kwargs))
            if labels:
                label_data.append((_cell_centroid(ring), cid))

    if labels:
        # put the cells and the labels in their own sibling subfolders so each
        # toggles on its own in the places panel.
        parts = [base.folder("Cells", cells, collapsed=True, hidden=False),
                 _labels_folder(label_data, kwargs.get("z_mode", "CTG"), name,
                                label_color or _CELL_OUTLINE)]
        return base.folder(name, parts, collapsed=collapsed, hidden=hidden)
    return base.folder(name, cells, collapsed=collapsed, hidden=hidden)


def hex_field(center: Sequence[float], cell: float, rings: int, *,
              azimuth: float = 90.0, ids: Optional[Sequence] = None, labels: bool = False,
              label_color: Optional[ColorInput] = None,
              name: str = 'Hex Field', collapsed: bool = True, hidden: bool = False,
              **kwargs) -> ET.Element:
    """
    Creates a hexagon-shaped cluster of hexagons as a KML folder of polygon cells.

    OVERVIEW:
        Tiles a filled hexagon of flat-top hexagons: a central cell surrounded by
        'rings' rings of hexagons, so the whole cluster is itself hexagonal. Each
        hexagon has a radius of 'cell' meters (center to vertex) and the cells
        interlock edge to edge. The total cell count is 1 + 3 * rings * (rings + 1)
        (7 at rings = 1, 19 at rings = 2, 37 at rings = 3, ...).

        Cells are numbered 1, 2, 3, ... in a spiral outward from the center: cell 1
        is the center, then the numbering spirals through each ring (cells 2-7 the
        first ring, 8-19 the second, and so on), so consecutive cells are always
        neighbors. 'azimuth' turns the whole cluster clockwise about the center; the
        default 90 leaves it in its base orientation (flat-top hexagons, a vertex
        pointing due east). The rotation is rigid, so the hexagons stay tessellated
        at any azimuth.

        Each cell is clickable and carries an ID/Ring attribute table.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the center hexagon.
        cell (Float):
            The hexagon radius (center to vertex), in meters.
        rings (Integer):
            The number of rings of hexagons around the center hexagon.
        azimuth (Float) [Optional]:
            Clockwise rotation of the whole cluster about the center, in degrees from
            true north; the default 90 is the base orientation. (Default = 90.0)
        ids (List) [Optional]:
            Cell labels as a flat list of '1 + 3*rings*(rings+1)' values in cell
            order (cell 1 the center, then ring by ring); 'ids[k]' names cell 'k+1'.
            When omitted, cells are named '1', '2', '3', ...
        labels (Boolean) [Optional]:
            True puts the cells in a 'Cells' subfolder and adds a sibling 'Labels'
            subfolder with a text label at each cell's centroid (named by the cell's
            ID), so each toggles on its own. (Default = False)
        label_color (Tuple) [Optional]:
            Color (hex, opacity) for the label dots. When None, they match the cells'
            outline color. (Default = None)
        name (String) [Optional]:
            The folder name. (Default = 'Hex Field')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function; applied to
            every cell.

    OUTPUT:
        hex_field (Element):
            An XML element representing a KML folder of polygon cells.
    """

    rings = int(rings)
    if rings < 1:
        raise ValueError("hex_field requires rings of at least 1.")

    center = _floatify(center)
    cell, azimuth = float(cell), float(azimuth)

    # Cells of a filled hexagon of 'rings' rings, ordered center-first then ring by
    # ring so they number 1..n outward.
    coords = _hex_spiral(rings)
    if ids is not None and len(ids) != len(coords):
        raise ValueError(
            f"hex_field ids must have {len(coords)} entries (one per cell), got {len(ids)}.")

    # 'azimuth' rotates the whole cluster; measured from the base orientation, so
    # subtract 90 (azimuth 90 = no rotation).
    a = math.radians(azimuth - 90.0)
    cos_a, sin_a = math.cos(a), math.sin(a)

    def place(east, north):
        # Rigid clockwise rotation about the center, then project. Applying the same
        # rotation to every vertex keeps the lattice tessellated at any azimuth.
        return _enu(center, east * cos_a + north * sin_a, -east * sin_a + north * cos_a)

    # Flat-top hexagons: the standard axial -> pixel layout places each hub, and the
    # six vertices sit at 0, 60, ... 300 degrees around it (a vertex points east).
    verts = [(cell * math.cos(math.radians(k * 60)), cell * math.sin(math.radians(k * 60)))
             for k in range(6)]

    cells, label_data = [], []
    for i, (q, r) in enumerate(coords):
        hub_e = 1.5 * cell * q
        hub_n = math.sqrt(3) * cell * (r + q / 2)
        ring_poly = [place(hub_e + ve, hub_n + vn) for ve, vn in verts]
        ring_poly.append(ring_poly[0])
        cell_id = ids[i] if ids is not None else i + 1
        ring_no = (abs(q) + abs(r) + abs(q + r)) // 2
        cells.append(_hex_cell_polygon(ring_poly, cell_id, ring_no, kwargs))
        if labels:
            label_data.append((_cell_centroid(ring_poly), cell_id))

    if labels:
        # put the cells and the labels in their own sibling subfolders so each
        # toggles on its own in the places panel.
        parts = [base.folder("Cells", cells, collapsed=True, hidden=False),
                 _labels_folder(label_data, kwargs.get("z_mode", "CTG"), name,
                                label_color or _CELL_OUTLINE)]
        return base.folder(name, parts, collapsed=collapsed, hidden=hidden)
    return base.folder(name, cells, collapsed=collapsed, hidden=hidden)


def _unit(v):
    """Normalize a 3-vector."""
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / m, v[1] / m, v[2] / m)


def _cross(a, b):
    """Cross product of two 3-vectors."""
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _fresnel_radius(zone: int, wavelength: float, d1: float, d2: float,
                    d_total: float) -> float:
    """
    The Fresnel-zone radius at a point on the path.

    'd1' and 'd2' are the distances from that point to each endpoint; their sum
    is the total path length 'd_total'. The radius is 0 at both endpoints and
    peaks at '0.5 * sqrt(zone * wavelength * d_total)' at mid-path.
    """
    return math.sqrt(zone * wavelength * d1 * d2 / d_total)


def _fresnel_ring_at(point_a: Sequence[float], point_b: Sequence[float],
                     wavelength: float, zone: int, ring_strips: int,
                     frac: float) -> List[List[float]]:
    """
    One Fresnel cross-section ring at fraction 'frac' (0..1) along the line of sight.

    The ring is a list of 'ring_strips' [lon, lat, z] vertices in the plane
    perpendicular to the LOS axis. Altitudes are absolute (point z + local up
    offset); 'frac' 0 or 1 collapses the ring to an endpoint (radius 0), and 0.5 is
    the widest cross-section at true mid-path.
    """
    d_total = distance(point_a, point_b)
    az_r = math.radians(bearing(point_a, point_b))
    dz = point_b[2] - point_a[2]

    # Orthonormal frame around the LOS axis: 'side' is horizontal and
    # perpendicular; 'up_perp' completes the frame (near-vertical).
    u = _unit((d_total * math.sin(az_r), d_total * math.cos(az_r), dz))
    side = (math.cos(az_r), -math.sin(az_r), 0.0)
    up_perp = _cross(u, side)

    d1 = frac * d_total
    r = _fresnel_radius(zone, wavelength, d1, d_total - d1, d_total)
    ax_e, ax_n, ax_u = d1 * math.sin(az_r), d1 * math.cos(az_r), frac * dz

    ring = []
    for k in range(ring_strips):
        phi = 2 * math.pi * k / ring_strips
        te = ax_e + r * (math.cos(phi) * up_perp[0] + math.sin(phi) * side[0])
        tn = ax_n + r * (math.cos(phi) * up_perp[1] + math.sin(phi) * side[1])
        tu = ax_u + r * (math.cos(phi) * up_perp[2] + math.sin(phi) * side[2])
        heading = math.degrees(math.atan2(te, tn)) % 360
        dist = math.hypot(te, tn)
        lon, lat = destination([point_a[0], point_a[1]], heading, dist)[:2]
        ring.append([lon, lat, point_a[2] + tu])
    return ring


def _fresnel_rings(point_a: Sequence[float], point_b: Sequence[float],
                   wavelength: float, zone: int, cross_rings: int,
                   ring_strips: int) -> List[List[List[float]]]:
    """
    Sample the Fresnel ellipsoid as a stack of cross-section rings.

    Returns 'cross_rings' evenly spaced rings along the line-of-sight (each built by
    '_fresnel_ring_at'); the two end rings collapse to the endpoints (radius 0).
    """
    return [_fresnel_ring_at(point_a, point_b, wavelength, zone, ring_strips,
                             j / (cross_rings - 1)) for j in range(cross_rings)]


def _tube_placemark(rings, name, zone_color, z_mode, headers, attrs, blurb):
    """Assemble the Fresnel tube as a single MultiGeometry Placemark."""
    fill_hex, fill_opacity = base._resolve_color(zone_color)

    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)
    ET.SubElement(placemark, 'visibility').text = '1'

    # Inline style: translucent fill with an opaque outline of the same hue.
    style = ET.SubElement(placemark, 'Style')
    poly_style = ET.SubElement(style, 'PolyStyle')
    ET.SubElement(poly_style, 'color').text = base._kml_color(fill_hex, fill_opacity)
    line_style = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_style, 'color').text = base._kml_color(fill_hex, 100)
    ET.SubElement(line_style, 'width').text = '1.0'

    ET.SubElement(placemark, 'snippet').text = blurb
    ET.SubElement(placemark, 'description').text = base._description_text(None, headers, attrs)

    multigeometry = ET.SubElement(placemark, 'MultiGeometry')
    segments = len(rings) - 1
    strips = len(rings[0])
    for j in range(segments):
        for k in range(strips):
            k2 = (k + 1) % strips
            quad = [rings[j][k], rings[j][k2], rings[j + 1][k2], rings[j + 1][k], rings[j][k]]
            poly = ET.SubElement(multigeometry, 'Polygon')
            base._set_altitude_mode(poly, z_mode)
            outer = ET.SubElement(poly, 'outerBoundaryIs')
            linear_ring = ET.SubElement(outer, 'LinearRing')
            coord_string = ''.join(base._coord_text(c) + ' ' for c in quad)
            ET.SubElement(linear_ring, 'coordinates').text = coord_string
    return placemark


def _path_placemark(point_a, point_b, name, path_color, z_mode, headers, attrs, blurb):
    """Assemble the straight line-of-sight link path as a LineString Placemark."""
    stroke_hex, stroke_opacity = base._resolve_color(path_color)

    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)
    ET.SubElement(placemark, 'visibility').text = '1'

    style = ET.SubElement(placemark, 'Style')
    line_style = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_style, 'color').text = base._kml_color(stroke_hex, stroke_opacity)
    ET.SubElement(line_style, 'width').text = '2.0'

    ET.SubElement(placemark, 'snippet').text = blurb
    ET.SubElement(placemark, 'description').text = base._description_text(None, headers, attrs)

    linestring = ET.SubElement(placemark, 'LineString')
    base._set_altitude_mode(linestring, z_mode)
    coord_string = base._coord_text(point_a) + ' ' + base._coord_text(point_b) + ' '
    ET.SubElement(linestring, 'coordinates').text = coord_string
    return placemark


def _ring_placemark(ring, name, color, z_mode, headers, attrs, blurb):
    """Assemble one cross-section as a closed LineString hoop Placemark."""
    stroke_hex, stroke_opacity = base._resolve_color(color)

    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)
    ET.SubElement(placemark, 'visibility').text = '1'

    style = ET.SubElement(placemark, 'Style')
    line_style = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_style, 'color').text = base._kml_color(stroke_hex, stroke_opacity)
    ET.SubElement(line_style, 'width').text = '5.0'

    ET.SubElement(placemark, 'snippet').text = blurb
    ET.SubElement(placemark, 'description').text = base._description_text(None, headers, attrs)

    linestring = ET.SubElement(placemark, 'LineString')
    base._set_altitude_mode(linestring, z_mode)
    loop = list(ring) + [ring[0]]  # repeat the first vertex to close the hoop
    ET.SubElement(linestring, 'coordinates').text = ''.join(base._coord_text(c) + ' ' for c in loop)
    return placemark


def fresnel_zone(point_a: Sequence[float], point_b: Sequence[float], freq_mhz: float,
                 *, name: str = 'RF Link', zone: int = 1, cross_rings: int = 25,
                 ring_strips: int = 16, zone_color=('yellow', 40), include_path: bool = True,
                 path_color='red', center_ring_color='cyan', z_mode: AltitudeMode = 'ABS',
                 collapsed: bool = True, hidden: bool = False,
                 cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D radio Fresnel-zone tube between two points.

    OVERVIEW:
        Builds the Fresnel zone of a point-to-point radio link as a 3D ellipsoid
        tube (a 'MultiGeometry' of polygon panels) around the line of sight, and,
        by default, the straight line-of-sight path itself. The two are returned
        together in a folder so each can be toggled on its own in Google Earth.

        The tube is inherently three-dimensional, so it uses absolute altitude:
        each endpoint's z should be an absolute (MSL) antenna altitude.

    INPUTS:
        point_a (List of three Floats):
            The first endpoint as [lon, lat, z]; z is an absolute (MSL) altitude.
        point_b (List of three Floats):
            The second endpoint as [lon, lat, z]; z is an absolute (MSL) altitude.
        freq_mhz (Float):
            The link frequency in megahertz.
        name (String) [Optional]:
            The link name (Default = 'RF Link'). It becomes the folder name and is
            prefixed onto each child so a search of Google Earth's places panel for
            the link name finds the folder, the tube, and the path together.
        zone (Integer) [Optional]:
            The Fresnel zone number to draw (Default = 1).
        cross_rings (Integer) [Optional]:
            The number of cross-section rings along the link. More gives a smoother
            tube lengthwise (Default = 25).
        ring_strips (Integer) [Optional]:
            The number of strips (facets) around each cross-section. More gives a
            rounder tube (Default = 16).
        zone_color (Color) [Optional]:
            The tube color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('yellow', 40)).
        include_path (Bool) [Optional]:
            True = also draw the line-of-sight path and return a folder holding
            both. False = return the tube on its own (Default = True).
        path_color (Color) [Optional]:
            The line-of-sight path color, in the same forms as 'zone_color'
            (Default = 'red').
        center_ring_color (Color) [Optional]:
            The color of a highlighted ring drawn at the widest (mid-path)
            cross-section, in the same forms as 'zone_color'. Set to None to omit
            it (Default = 'cyan').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The tube only renders under a non-clamped mode.
        collapsed (Bool) [Optional]:
            True = the returned folder is collapsed in the places panel (Default = True).
        hidden (Bool) [Optional]:
            True = the returned folder is hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view of
            the returned folder (or of the tube when it is returned on its own).

    OUTPUT:
        element (Element):
            A KML 'Folder' holding the tube plus the line-of-sight path and/or the
            center ring when either is drawn, or the tube 'Placemark' on its own
            when both 'include_path' is False and 'center_ring_color' is None.
    """

    point_a = _floatify(point_a)
    point_b = _floatify(point_b)
    freq_mhz = float(freq_mhz)
    zone, cross_rings, ring_strips = int(zone), int(cross_rings), int(ring_strips)
    if cross_rings < 2:
        raise ValueError("fresnel_zone requires cross_rings of at least 2.")
    if ring_strips < 3:
        raise ValueError("fresnel_zone requires ring_strips of at least 3.")
    d_total = distance(point_a, point_b)
    if d_total == 0:
        raise ValueError("point_a and point_b must be different locations.")

    az = bearing(point_a, point_b)
    dz = point_b[2] - point_a[2]
    wavelength = _LIGHT_SPEED / (freq_mhz * 1e6)
    r_max = 0.5 * math.sqrt(zone * wavelength * d_total)

    rings = _fresnel_rings(point_a, point_b, wavelength, zone, cross_rings, ring_strips)

    # Tube. The blurb is kept to two lines: Google Earth's places panel only
    # shows about two, so it leads with the band and the widest radius.
    zone_headers = ['Frequency (MHz)', 'Zone', 'Path Length (m)', 'Wavelength (m)', 'Max Radius (m)']
    zone_attrs = [freq_mhz, zone, round(d_total, 1), round(wavelength, 4), round(r_max, 2)]
    zone_blurb = f"Fresnel {zone} · {freq_mhz:g} MHz\nMax radius {r_max:.1f} m"
    tube = _tube_placemark(rings, f"{name} - Fresnel Zone", zone_color, z_mode,
                           zone_headers, zone_attrs, zone_blurb)

    # The folder is assembled in TOC order: path, tube, then the center-ring
    # highlight. Each piece is optional; the tube is the only guaranteed one.
    pieces = []

    if include_path:
        path_headers = ['End A (lon, lat, z)', 'End B (lon, lat, z)', 'Path Length (m)',
                        'Azimuth (deg)', 'Elevation Diff (m)']
        path_attrs = [f"{point_a[0]}, {point_a[1]}, {point_a[2]}",
                      f"{point_b[0]}, {point_b[1]}, {point_b[2]}",
                      round(d_total, 1), round(az, 1), round(dz, 1)]
        path_blurb = f"Link path · {d_total / 1000:.2f} km\nAz {az:.0f}°"
        pieces.append(_path_placemark(point_a, point_b, f"{name} - Link Path", path_color,
                                      z_mode, path_headers, path_attrs, path_blurb))

    pieces.append(tube)

    if center_ring_color is not None:
        # Highlight the widest cross-section, built at true mid-path (frac 0.5) so it
        # is centered and matches r_max regardless of the 'cross_rings' parity.
        mid_ring = _fresnel_ring_at(point_a, point_b, wavelength, zone, ring_strips, 0.5)
        mid_alt = point_a[2] + 0.5 * dz
        ring_headers = ['Radius (m)', 'Distance from End A (m)', 'Altitude (m)']
        ring_attrs = [round(r_max, 2), round(0.5 * d_total, 1), round(mid_alt, 1)]
        ring_blurb = f"Widest cross-section\nRadius {r_max:.1f} m"
        pieces.append(_ring_placemark(mid_ring, f"{name} - Center Ring", center_ring_color,
                                      z_mode, ring_headers, ring_attrs, ring_blurb))

    if len(pieces) == 1:
        if cam is not None:
            tube.append(cam)
        return tube

    return base.folder(name, pieces, collapsed=collapsed, hidden=hidden, cam=cam)


def _enu(center: Sequence[float], east: float, north: float, up: float = 0.0) -> List[float]:
    """Local East/North/Up offset (meters) -> [lon, lat, z] around 'center'."""
    dist = math.hypot(east, north)
    if dist == 0:
        lon, lat = center[0], center[1]
    else:
        heading = math.degrees(math.atan2(east, north)) % 360
        lon, lat = destination([center[0], center[1]], heading, dist)[:2]
    return [lon, lat, (center[2] if len(center) > 2 else 0) + up]


def _wall(bottom: List[List[float]], top: List[List[float]]) -> List[List[List[float]]]:
    """Quad panels bridging two equal-length rings (a band of a solid's surface)."""
    sides = len(bottom)
    return [[bottom[i], bottom[(i + 1) % sides], top[(i + 1) % sides], top[i], bottom[i]]
            for i in range(sides)]


def _axis_frame(azimuth: float, elevation: float):
    """Orthonormal (u, side, up_perp) ENU frame for an axis at azimuth/elevation.

    'u' is the axis direction (elevation 90 = straight up). 'side' and 'up_perp'
    span the plane perpendicular to the axis, in which the cross-section rings lie.
    """
    az, el = math.radians(azimuth), math.radians(elevation)
    u = (math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el))
    side = (math.cos(az), -math.sin(az), 0.0)     # horizontal, perpendicular to u
    up_perp = _cross(u, side)
    return u, side, up_perp


def _axis_ring(center, radius, dist, sides, frame, phase=0.0):
    """A ring of 'sides' points, radius 'radius', 'dist' along the axis from center.

    'phase' (radians) offsets the starting angle, so a polygonal ring can be
    rotated about the axis (used by 'pyramid' to aim a face or vertex).
    """
    u, side, up_perp = frame
    ring = []
    for i in range(sides):
        phi = 2 * math.pi * i / sides + phase
        cos_p, sin_p = math.cos(phi), math.sin(phi)
        ring.append(_enu(center,
                         dist * u[0] + radius * (cos_p * up_perp[0] + sin_p * side[0]),
                         dist * u[1] + radius * (cos_p * up_perp[1] + sin_p * side[1]),
                         dist * u[2] + radius * (cos_p * up_perp[2] + sin_p * side[2])))
    return ring


def _axis_point(center, dist, frame):
    """The point 'dist' along the axis from center."""
    u = frame[0]
    return _enu(center, dist * u[0], dist * u[1], dist * u[2])


def _check_anchor(anchor: str) -> None:
    """Guard that a solid's anchor is one of 'base', 'center', or 'top'."""
    if anchor not in ('base', 'center', 'top'):
        raise ValueError("anchor must be 'base', 'center', or 'top'.")


def _anchor_shift(anchor: str, base_u: float, top_u: float) -> float:
    """Axis offset so the named reference ('base'|'center'|'top') sits at the center.

    A shape spans the axis from 'base_u' to 'top_u'; subtracting the returned
    offset from every axis distance slides that reference point onto the center.
    """
    if anchor == 'center':
        return (base_u + top_u) / 2
    if anchor == 'top':
        return top_u
    return base_u


def _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                     style_to_use=None, cam=None, line_width=1.0):
    """Assemble a 3D solid as a single MultiGeometry Placemark of polygon panels.

    When 'style_to_use' names a shared style it is referenced with a <styleUrl>
    and overrides the inline single-'color' fill; otherwise a translucent fill
    with an opaque outline of the same hue is written inline. An optional 'cam'
    ('LookAt' or 'Camera') is appended as the placemark's default view.
    """
    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)
    ET.SubElement(placemark, 'visibility').text = '0' if hidden else '1'

    if style_to_use is not None:
        ET.SubElement(placemark, 'styleUrl').text = '#' + str(style_to_use)
    else:
        # Translucent fill with an opaque outline of the same hue.
        fill_hex, fill_opacity = base._resolve_color(color)
        style = ET.SubElement(placemark, 'Style')
        ET.SubElement(ET.SubElement(style, 'PolyStyle'), 'color').text = base._kml_color(fill_hex, fill_opacity)
        line_style = ET.SubElement(style, 'LineStyle')
        ET.SubElement(line_style, 'color').text = base._kml_color(fill_hex, 100)
        ET.SubElement(line_style, 'width').text = str(float(line_width))

    if blurb is not None:
        ET.SubElement(placemark, 'snippet').text = blurb
    ET.SubElement(placemark, 'description').text = base._description_text(None, headers, attrs)

    multigeometry = ET.SubElement(placemark, 'MultiGeometry')
    for ring in panels:
        poly = ET.SubElement(multigeometry, 'Polygon')
        base._set_altitude_mode(poly, z_mode)
        linear_ring = ET.SubElement(ET.SubElement(poly, 'outerBoundaryIs'), 'LinearRing')
        linear_ring_text = ''.join(base._coord_text(c) + ' ' for c in ring)
        ET.SubElement(linear_ring, 'coordinates').text = linear_ring_text

    if cam is not None:
        placemark.append(cam)
    return placemark


def cylinder(coords: Sequence[float], radius: float, height: float, *,
             top_radius: Optional[float] = None,
             azimuth: float = 0.0, tilt: float = 90.0, anchor: Anchor = 'base',
             sides: int = 32, color=('#66ff33', 40), cap: bool = True,
             headers: Optional[list] = None, attrs: Optional[list] = None,
             style_to_use: Optional[str] = None, name: str = 'Cylinder',
             z_mode: AltitudeMode = 'ABS', hidden: bool = False,
             cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D cylinder as a KML solid.

    OVERVIEW:
        Builds a cylinder that runs from a base circle to a top circle, as a
        'MultiGeometry' of polygon panels. Useful for volumes such as a column of
        airspace, a tank, or a tower footprint extruded along an axis. By default it
        stands vertical; 'azimuth'/'tilt' point the axis elsewhere. Give a
        'top_radius' different from 'radius' to taper it into a frustum (a truncated
        cone), for a tank, cooling tower, bucket, or lampshade.

        The cylinder is three-dimensional, so it uses absolute altitude: the
        coordinate's z is an absolute (MSL) altitude for the base.

    INPUTS:
        coords (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The base circle radius in meters.
        height (Float):
            The length in meters along the axis (the far cap sits 'height' from the
            base, in the axis direction).
        top_radius (Float) [Optional]:
            The top circle radius in meters. When None it equals 'radius' (a true
            cylinder); a different value tapers the sides into a frustum, and 0
            closes it to a point like a cone (Default = None).
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'tilt' is not straight up or down.
        tilt (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which end sits at 'coords': 'base' = the near face (body extends along
            the axis), 'center' = mid-height, 'top' = the far face (body hangs back
            along the axis) (Default = 'base').
        sides (Integer) [Optional]:
            The number of facets around the circumference. More gives a rounder
            cylinder (Default = 32).
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#66ff33', 40)).
        cap (Bool) [Optional]:
            True = close the open ends (both the top and bottom) with disc caps
            (Default = True).
        headers (List) [Optional]:
            Titles for the cylinder's attribute table. Defaults to a radius/height/
            altitude/sides summary when omitted.
        attrs (List) [Optional]:
            Values for the cylinder's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the cylinder (Default = 'Cylinder').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the cylinder starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        cylinder (Element):
            A KML 'Placemark' containing the cylinder 'MultiGeometry'.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, height, azimuth, tilt = float(radius), float(height), float(azimuth), float(tilt)
    r_top = radius if top_radius is None else float(top_radius)
    if r_top < 0:
        raise ValueError("cylinder top_radius must not be negative.")
    sides = int(sides)
    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, 0.0, height)
    bottom = _axis_ring(coords, radius, 0.0 - off, sides, frame)
    top = _axis_ring(coords, r_top, height - off, sides, frame)

    panels = _wall(bottom, top)
    if cap:
        panels.append(bottom + [bottom[0]])
        panels.append(top + [top[0]])

    base_alt = coords[2] if len(coords) > 2 else 0
    tapered = r_top != radius
    if headers is None:
        headers = ['Radius (m)', 'Height (m)', 'Base Altitude (m)', 'Sides']
        if tapered:
            headers.insert(1, 'Top Radius (m)')
    if attrs is None:
        attrs = [radius, height, round(base_alt, 1), sides]
        if tapered:
            attrs.insert(1, r_top)
    blurb = (f"Frustum · r={radius:g} to {r_top:g} m" if tapered
             else f"Cylinder · r={radius:g} m") + f"\nHeight {height:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam)


def cone(coords: Sequence[float], radius: float, height: float, *,
         azimuth: float = 0.0, tilt: float = 90.0, anchor: Anchor = 'base',
         sides: int = 32, color=('#3399ff', 40), cap: bool = True,
         headers: Optional[list] = None, attrs: Optional[list] = None,
         style_to_use: Optional[str] = None, name: str = 'Cone',
         z_mode: AltitudeMode = 'ABS', hidden: bool = False,
         cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D cone as a KML solid.

    OVERVIEW:
        Builds a cone between a circular base and a single apex, as a
        'MultiGeometry' of triangular panels. Useful for beams, sensor cones, or
        funnel volumes. By default it stands vertical with the base at 'coords';
        'azimuth'/'tilt' point the axis elsewhere and 'anchor' slides the cone
        along that axis.

        The base sits at the anchor's near end and the apex is 'height' out along
        the axis, so 'base'/'center'/'top' move the cone the same way they move a
        cylinder or dome. A forward-opening beam (apex at 'coords', widening away)
        is made by aiming the axis with 'azimuth'/'tilt' and anchoring 'top', not by
        a special anchor mode.

        The cone is three-dimensional, so it uses absolute altitude: the
        coordinate's z is an absolute (MSL) altitude.

    INPUTS:
        coords (List of three Floats):
            The anchor point as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The base radius in meters.
        height (Float):
            The length in meters between the base and the apex along the axis.
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'tilt' is not straight up or down.
        tilt (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which point sits at 'coords': 'base' = the base disc (apex out along the
            axis), 'center' = mid-way along the axis, 'top' = the apex (base hangs
            back along the axis) (Default = 'base').
        sides (Integer) [Optional]:
            The number of facets around the base. More gives a rounder cone
            (Default = 32).
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#3399ff', 40)).
        cap (Bool) [Optional]:
            True = close the base with a disc cap (Default = True).
        headers (List) [Optional]:
            Titles for the cone's attribute table. Defaults to a radius/height/
            altitude/sides summary when omitted.
        attrs (List) [Optional]:
            Values for the cone's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the cone (Default = 'Cone').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the cone starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        cone (Element):
            A KML 'Placemark' containing the cone 'MultiGeometry'.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, height, azimuth, tilt = float(radius), float(height), float(azimuth), float(tilt)
    sides = int(sides)
    frame = _axis_frame(azimuth, tilt)
    # Base disc at 0 and apex at 'height', shifted so the anchor sits at 'coords'.
    # This matches cylinder/dome/sphere, so base/center/top move the cone the same
    # direction under any tilt.
    off = _anchor_shift(anchor, 0.0, height)
    base_ring = _axis_ring(coords, radius, 0.0 - off, sides, frame)
    apex = _axis_point(coords, height - off, frame)

    panels = [[base_ring[i], base_ring[(i + 1) % sides], apex, base_ring[i]] for i in range(sides)]
    if cap:
        panels.append(base_ring + [base_ring[0]])

    base_alt = coords[2] if len(coords) > 2 else 0
    if headers is None:
        headers = ['Base Radius (m)', 'Height (m)', 'Base Altitude (m)', 'Sides']
    if attrs is None:
        attrs = [radius, height, round(base_alt, 1), sides]
    blurb = f"Cone · r={radius:g} m\nHeight {height:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam)


def dome(coords: Sequence[float], radius: float, *, azimuth: float = 0.0,
         tilt: float = 90.0, anchor: Anchor = 'base', sides: int = 32, rings: int = 8,
         color=('#ff9933', 40), cap: bool = True,
         headers: Optional[list] = None, attrs: Optional[list] = None,
         style_to_use: Optional[str] = None, name: str = 'Dome',
         z_mode: AltitudeMode = 'ABS', hidden: bool = False,
         cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D dome (hemisphere) as a KML solid.

    OVERVIEW:
        Builds a hemispherical dome that rises from a base circle to a pole point,
        as a 'MultiGeometry' of polygon panels. Useful for radar/sensor domes,
        stadium roofs, or hemispheric coverage volumes. By default the pole points
        straight up; 'azimuth'/'tilt' aim it elsewhere.

        The dome is three-dimensional, so it uses absolute altitude: the
        coordinate's z is an absolute (MSL) altitude for the base.

    INPUTS:
        coords (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The dome radius in meters (also its height along the axis).
        azimuth (Float) [Optional]:
            The compass bearing the pole leans toward, in degrees (Default = 0.0).
            Only has an effect when 'tilt' is not straight up or down.
        tilt (Float) [Optional]:
            The angle of the pole above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which point sits at 'coords': 'base' = the base rim center (pole out
            along the axis), 'center' = mid-way, 'top' = the pole (the dome hangs
            back along the axis) (Default = 'base').
        sides (Integer) [Optional]:
            The number of facets around the circumference. More gives a rounder
            dome (Default = 32).
        rings (Integer) [Optional]:
            The number of horizontal bands stacked from the base to the top. More
            gives a smoother curve (Default = 8).
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#ff9933', 40)).
        cap (Bool) [Optional]:
            True = close the base with a disc cap (Default = True).
        headers (List) [Optional]:
            Titles for the dome's attribute table. Defaults to a radius/altitude/
            sides/rings summary when omitted.
        attrs (List) [Optional]:
            Values for the dome's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the dome (Default = 'Dome').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the dome starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        dome (Element):
            A KML 'Placemark' containing the dome 'MultiGeometry'.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, azimuth, tilt = float(radius), float(azimuth), float(tilt)
    sides, rings = int(sides), int(rings)
    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, 0.0, radius)   # rim at 0, pole at radius along the axis
    levels = []
    for r in range(rings + 1):
        phi = math.radians(90 * r / rings)
        levels.append(_axis_ring(coords, radius * math.cos(phi), radius * math.sin(phi) - off, sides, frame))

    panels = []
    for r in range(rings):
        panels.extend(_wall(levels[r], levels[r + 1]))
    if cap:
        panels.append(levels[0] + [levels[0][0]])

    base_alt = coords[2] if len(coords) > 2 else 0
    if headers is None:
        headers = ['Radius (m)', 'Base Altitude (m)', 'Sides', 'Rings']
    if attrs is None:
        attrs = [radius, round(base_alt, 1), sides, rings]
    blurb = f"Dome · r={radius:g} m\nHemisphere"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam)


def sphere(coords: Sequence[float], radius: float, *, azimuth: float = 0.0,
           tilt: float = 90.0, anchor: Anchor = 'center', sides: int = 24, rings: int = 12,
           color=('#9933ff', 40), headers: Optional[list] = None, attrs: Optional[list] = None,
           style_to_use: Optional[str] = None, name: str = 'Sphere', z_mode: AltitudeMode = 'ABS',
           hidden: bool = False, cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D sphere as a KML solid.

    OVERVIEW:
        Builds a sphere around a center point, as a 'MultiGeometry' of polygon
        panels stacked pole to pole. Useful for effect radii, exclusion volumes,
        or any point-centered 3D extent.

        Unlike the other solids, 'coords' is the sphere's geometric center, so the
        sphere extends 'radius' in every direction. It is three-dimensional and
        uses absolute altitude, so give the center a z of at least 'radius' for it
        to sit above the ground. 'azimuth'/'tilt' aim the pole axis, which only
        shifts where the mesh poles/seams sit (a sphere is symmetric).

    INPUTS:
        coords (List of three Floats):
            The sphere center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The sphere radius in meters.
        azimuth (Float) [Optional]:
            The compass bearing the pole axis leans toward, in degrees
            (Default = 0.0). Only shifts the mesh seams, not the silhouette.
        tilt (Float) [Optional]:
            The angle of the pole axis above horizontal in degrees: 90 = poles up
            and down (Default), 0 = poles horizontal.
        anchor (String) [Optional]:
            Which point sits at 'coords': 'center' = the geometric center
            (Default); 'base' = the near pole, so the sphere rests out along the
            axis (e.g. sitting on a mast tip); 'top' = the far pole, so it hangs
            back along the axis.
        sides (Integer) [Optional]:
            The number of facets around the equator (longitude divisions). More
            gives a rounder sphere (Default = 24).
        rings (Integer) [Optional]:
            The number of horizontal bands from pole to pole (latitude divisions).
            More gives a rounder sphere (Default = 12).
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#9933ff', 40)).
        headers (List) [Optional]:
            Titles for the sphere's attribute table. Defaults to a radius/altitude/
            sides/rings summary when omitted.
        attrs (List) [Optional]:
            Values for the sphere's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the sphere (Default = 'Sphere').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the sphere starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        sphere (Element):
            A KML 'Placemark' containing the sphere 'MultiGeometry'.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, azimuth, tilt = float(radius), float(azimuth), float(tilt)
    sides, rings = int(sides), int(rings)
    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, -radius, radius)   # poles at -radius and +radius along the axis
    levels = []
    for la in range(rings + 1):
        phi = math.radians(-90 + 180 * la / rings)
        levels.append(_axis_ring(coords, radius * math.cos(phi), radius * math.sin(phi) - off, sides, frame))

    panels = []
    for la in range(rings):
        panels.extend(_wall(levels[la], levels[la + 1]))

    center_alt = coords[2] if len(coords) > 2 else 0
    if headers is None:
        headers = ['Radius (m)', 'Center Altitude (m)', 'Sides', 'Rings']
    if attrs is None:
        attrs = [radius, round(center_alt, 1), sides, rings]
    blurb = f"Sphere · r={radius:g} m\nCenter {center_alt:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam)


def _frame_point(center, frame, a: float, b: float, dist: float) -> List[float]:
    """A point at cross-plane offsets 'a' (along side) and 'b' (along up_perp),
    'dist' along the axis from 'center'."""
    u, side, up_perp = frame
    return _enu(center,
                dist * u[0] + a * side[0] + b * up_perp[0],
                dist * u[1] + a * side[1] + b * up_perp[1],
                dist * u[2] + a * side[2] + b * up_perp[2])


def cube(coords: Sequence[float], size, *, azimuth: float = 0.0, tilt: float = 90.0,
         anchor: Anchor = 'base', color=('#ff5050', 40), cap: bool = True,
         headers: Optional[list] = None, attrs: Optional[list] = None,
         style_to_use: Optional[str] = None, name: str = 'Cube',
         z_mode: AltitudeMode = 'ABS', hidden: bool = False,
         cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D cube (or box) as a KML solid.

    OVERVIEW:
        Builds a cube, or a rectangular box, as a 'MultiGeometry' of polygon
        panels. Useful for buildings, containers, or blocked-out volumes. By
        default it stands upright on its base; 'azimuth'/'tilt' point the axis
        elsewhere and 'anchor' slides the box along that axis.

        The box is three-dimensional, so it uses absolute altitude: the
        coordinate's z is an absolute (MSL) altitude for the base.

    INPUTS:
        coords (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        size (Float or List of three Floats):
            A single edge length for a cube, or '[x, y, z]' for a box: 'x' across
            (east at azimuth 0), 'y' deep (north at azimuth 0), 'z' along the axis,
            in meters.
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'tilt' is not straight up or down.
        tilt (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which face sits at 'coords': 'base' = the near face, 'center' =
            mid-height, 'top' = the far face (Default = 'base').
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#ff5050', 40)).
        cap (Bool) [Optional]:
            True = close the two end faces (Default = True).
        headers (List) [Optional]:
            Titles for the box's attribute table. Defaults to a size/altitude
            summary when omitted.
        attrs (List) [Optional]:
            Values for the box's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the box (Default = 'Cube').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the box starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        cube (Element):
            A KML 'Placemark' containing the box 'MultiGeometry'.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    azimuth, tilt = float(azimuth), float(tilt)
    if isinstance(size, (int, float, str)):
        sx = sy = sz = float(size)
    else:
        sx, sy, sz = (float(s) for s in size)

    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, 0.0, sz)
    hx, hy = sx / 2, sy / 2
    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]   # one square cross-section
    bottom = [_frame_point(coords, frame, a, b, 0.0 - off) for a, b in corners]
    top = [_frame_point(coords, frame, a, b, sz - off) for a, b in corners]

    panels = _wall(bottom, top)
    if cap:
        panels.append(bottom + [bottom[0]])
        panels.append(top + [top[0]])

    base_alt = coords[2] if len(coords) > 2 else 0
    if headers is None:
        headers = ['Size X (m)', 'Size Y (m)', 'Size Z (m)', 'Base Altitude (m)']
    if attrs is None:
        attrs = [sx, sy, sz, round(base_alt, 1)]
    blurb = f"Cube · {sx:g}×{sy:g}×{sz:g} m\nBase {base_alt:g} m"
    # A cube has far fewer edges than the faceted solids, so give its outline extra
    # weight to keep the wireframe legible.
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam, line_width=3.0)


def pyramid(coords: Sequence[float], radius: float, height: float, sides: int = 4, *,
            orient: float = 0.0, azimuth: float = 0.0, tilt: float = 90.0,
            anchor: Anchor = 'base', color=None, cap: bool = True,
            headers: Optional[list] = None, attrs: Optional[list] = None,
            style_to_use: Optional[str] = None, name: str = 'Pyramid',
            z_mode: AltitudeMode = 'ABS', hidden: bool = False,
            cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D pyramid with an n-sided base as a KML solid.

    OVERVIEW:
        Builds a pyramid as a 'MultiGeometry' of triangular panels: a regular
        polygon base of 'sides' edges rising to a single apex. 'sides'=4 gives a
        square pyramid, 'sides'=3 a tetrahedron-like spike, and more sides approach
        a cone. By default it stands upright on its base; 'azimuth'/'tilt' point the
        axis elsewhere, and 'anchor' slides the pyramid along that axis. 'orient'
        spins the base about the axis so a corner or a flat side faces a chosen
        direction.

        The pyramid is three-dimensional, so it uses absolute altitude: the
        coordinate's z is an absolute (MSL) altitude for the base.

    INPUTS:
        coords (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The distance from the base center to each base corner, in meters.
        height (Float):
            The length in meters between the base and the apex along the axis.
        sides (Integer) [Optional]:
            The number of base sides (3 or more) (Default = 4, a square pyramid).
        orient (Float) [Optional]:
            Rotation of the base about the axis, in degrees, to aim a corner or a
            face (Default = 0.0).
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'tilt' is not straight up or down.
        tilt (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which point sits at 'coords': 'base' = the base, 'center' = mid-way,
            'top' = the apex (Default = 'base').
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity.
            When omitted (Default = None), the color is chosen by base edge count
            from 'PYRAMID_PALETTE', so a triangular, square, pentagonal, ... pyramid
            each reads a different color.
        cap (Bool) [Optional]:
            True = close the base with a polygon cap (Default = True).
        headers (List) [Optional]:
            Titles for the pyramid's attribute table. Defaults to a radius/height/
            altitude/sides summary when omitted.
        attrs (List) [Optional]:
            Values for the pyramid's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use in place of 'color'
            (Default = None).
        name (String) [Optional]:
            The name to be given to the pyramid (Default = 'Pyramid').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the pyramid starts hidden (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view.

    OUTPUT:
        pyramid (Element):
            A KML 'Placemark' containing the pyramid 'MultiGeometry'.
    """

    sides = int(sides)
    if sides < 3:
        raise ValueError("pyramid requires at least 3 base sides.")
    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, height, orient = float(radius), float(height), float(orient)
    azimuth, tilt = float(azimuth), float(tilt)
    # Unstyled pyramids color by base edge count (triangle, square, ... each differ).
    if color is None:
        color = PYRAMID_PALETTE[(sides - 3) % len(PYRAMID_PALETTE)]
    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, 0.0, height)
    base_ring = _axis_ring(coords, radius, 0.0 - off, sides, frame, phase=math.radians(orient))
    apex = _axis_point(coords, height - off, frame)

    panels = [[base_ring[i], base_ring[(i + 1) % sides], apex, base_ring[i]] for i in range(sides)]
    if cap:
        panels.append(base_ring + [base_ring[0]])

    base_alt = coords[2] if len(coords) > 2 else 0
    if headers is None:
        headers = ['Base Radius (m)', 'Height (m)', 'Base Altitude (m)', 'Sides']
    if attrs is None:
        attrs = [radius, height, round(base_alt, 1), sides]
    blurb = f"Pyramid · r={radius:g} m\nHeight {height:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb,
                            style_to_use=style_to_use, cam=cam)


# --- soccer ball (truncated icosahedron) ------------------------------------

_TRUNC_ICOS = None   # cached (pentagons, hexagons) as lists of unit-vector faces


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _order_face(points):
    """Order a face's unit-vector vertices into a convex ring by angle.

    The vertices of one truncated-icosahedron face are sorted around their
    centroid within the face plane, giving a clean, non-self-intersecting ring.
    """
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    cz = sum(p[2] for p in points) / len(points)
    normal = _unit((cx, cy, cz))                      # centroid direction ~ outward normal
    # A 2D basis (e1, e2) spanning the face plane.
    e1 = _unit(_cross(normal, (0.0, 0.0, 1.0)) if abs(normal[2]) < 0.9
               else _cross(normal, (0.0, 1.0, 0.0)))
    e2 = _cross(normal, e1)
    ordered = sorted(points, key=lambda p: math.atan2(
        _dot((p[0] - cx, p[1] - cy, p[2] - cz), e2),
        _dot((p[0] - cx, p[1] - cy, p[2] - cz), e1)))
    return ordered


def _truncated_icosahedron():
    """Return (pentagons, hexagons): the 12 + 20 faces of a truncated icosahedron.

    Each face is a list of unit vectors. Built by truncating a unit icosahedron:
    every edge yields two vertices a third of the way in from each end; pentagons
    ring each original vertex and hexagons fill each original triangular face.
    """
    global _TRUNC_ICOS
    if _TRUNC_ICOS is not None:
        return _TRUNC_ICOS

    phi = (1 + 5 ** 0.5) / 2
    verts = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            verts.append((0.0, float(s1), float(s2) * phi))
            verts.append((float(s1), float(s2) * phi, 0.0))
            verts.append((float(s2) * phi, 0.0, float(s1)))

    n = len(verts)
    # Icosahedron edges: vertex pairs at the minimum separation.
    def d2(i, j):
        a, b = verts[i], verts[j]
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    min_d2 = min(d2(i, j) for i in range(n) for j in range(i + 1, n))
    adj = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if abs(d2(i, j) - min_d2) < 1e-6:
                adj[i].append(j)
                adj[j].append(i)

    # Triangular faces: mutually adjacent triples.
    faces = []
    for i in range(n):
        for j in adj[i]:
            for k in adj[j]:
                if k in adj[i] and i < j < k:
                    faces.append((i, j, k))

    # Truncation point on edge (a -> b), a third of the way from a toward b.
    def trunc(a, b):
        va, vb = verts[a], verts[b]
        return _unit((va[0] * 2 / 3 + vb[0] / 3,
                      va[1] * 2 / 3 + vb[1] / 3,
                      va[2] * 2 / 3 + vb[2] / 3))

    pentagons = []
    for a in range(n):
        pentagons.append(_order_face([trunc(a, nb) for nb in adj[a]]))

    hexagons = []
    for a, b, c in faces:
        pts = [trunc(a, b), trunc(b, a), trunc(b, c),
               trunc(c, b), trunc(c, a), trunc(a, c)]
        hexagons.append(_order_face(pts))

    _TRUNC_ICOS = (pentagons, hexagons)
    return _TRUNC_ICOS


def _two_colors(colors):
    """Resolve a soccer ball's 'colors' into a (pentagon, hexagon) pair.

    Accepts a single color used for both face types (a palette name / '#hex'
    string, or a '(color, opacity)' pair), or a '(pentagon_color, hexagon_color)'
    pair. The '(color, opacity)' case is told apart from a two-color pair by its
    numeric second item.
    """
    if isinstance(colors, str):
        return colors, colors
    if (len(colors) == 2 and isinstance(colors[0], str)
            and isinstance(colors[1], (int, float))):
        return colors, colors                      # a single (color, opacity) pair
    if len(colors) == 2:
        return colors[0], colors[1]                # (pentagon_color, hexagon_color)
    raise ValueError(
        "soccer_ball colors must be a single color or a (pentagon, hexagon) pair.")


def soccer_ball(coords: Sequence[float], radius: float, *, azimuth: float = 0.0,
                tilt: float = 90.0, anchor: Anchor = 'center',
                colors=(('#111111', 100), ('#ffffff', 100)),
                headers: Optional[list] = None, attrs: Optional[list] = None,
                style_to_use: Optional[str] = None, name: str = 'Soccer Ball',
                z_mode: AltitudeMode = 'ABS', hidden: bool = False, collapsed: bool = True,
                cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a 3D soccer ball (truncated icosahedron) as a KML folder of solids.

    OVERVIEW:
        Builds a soccer ball: a truncated icosahedron of 12 pentagon and 20 hexagon
        faces, two-tone by default (dark pentagons, light hexagons). The pentagons
        and hexagons are returned as two 'MultiGeometry' placemarks in a folder so
        each color can be toggled on its own.

        Like 'sphere', 'coords' is the geometric center and the ball extends
        'radius' in every direction; it uses absolute altitude, so give the center
        a z of at least 'radius' to sit above the ground.

    INPUTS:
        coords (List of three Floats):
            The ball center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The ball radius in meters.
        azimuth (Float) [Optional]:
            The compass bearing the pole axis leans toward, in degrees
            (Default = 0.0). Only shifts where the faces sit, not the silhouette.
        tilt (Float) [Optional]:
            The angle of the pole axis above horizontal in degrees (Default = 90.0).
        anchor (String) [Optional]:
            Which point sits at 'coords': 'center' (Default), 'base' = the near
            pole (the ball rests out along the axis), 'top' = the far pole.
        colors (Color or Pair of Colors) [Optional]:
            Either a single color for both face types, or a
            (pentagon_color, hexagon_color) pair. Each color is a palette name,
            '#rrggbb' hex string, or (color, opacity) pair
            (Default = (('#111111', 100), ('#ffffff', 100))).
        headers (List) [Optional]:
            Titles for each placemark's attribute table. Defaults to a radius/
            altitude summary when omitted.
        attrs (List) [Optional]:
            Values for each placemark's attribute table, paired with 'headers'.
        style_to_use (String) [Optional]:
            The name of a shared polygon style to use on both placemarks in place
            of 'colors' (Default = None).
        name (String) [Optional]:
            The folder name (Default = 'Soccer Ball').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the ball starts hidden (Default = False).
        collapsed (Bool) [Optional]:
            True = the returned folder is collapsed in the places panel (Default = True).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the folder's default view.

    OUTPUT:
        soccer_ball (Element):
            A KML 'Folder' holding the pentagon and hexagon placemarks.
    """

    _check_anchor(anchor)
    coords = _floatify(coords)
    radius, azimuth, tilt = float(radius), float(azimuth), float(tilt)
    frame = _axis_frame(azimuth, tilt)
    off = _anchor_shift(anchor, -radius, radius)   # poles at -radius and +radius along the axis
    pentagons, hexagons = _truncated_icosahedron()

    def build(faces, color, label):
        panels = []
        for face in faces:
            ring = [_frame_point(coords, frame, d[0] * radius, d[1] * radius,
                                 d[2] * radius - off) for d in face]
            ring.append(ring[0])
            panels.append(ring)
        base_alt = coords[2] if len(coords) > 2 else 0
        h = headers if headers is not None else ['Radius (m)', 'Center Altitude (m)', 'Faces']
        a = attrs if attrs is not None else [radius, round(base_alt, 1), len(faces)]
        blurb = f"Soccer ball · r={radius:g} m\n{label}"
        return _solid_placemark(panels, f"{name} - {label}", color, z_mode, hidden,
                                h, a, blurb, style_to_use=style_to_use)

    pent_color, hex_color = _two_colors(colors)
    pieces = [build(pentagons, pent_color, 'Pentagons'),
              build(hexagons, hex_color, 'Hexagons')]
    return base.folder(name, pieces, collapsed=collapsed, hidden=hidden, cam=cam)

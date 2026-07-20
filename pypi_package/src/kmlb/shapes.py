# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Higher-level shape builders composed from the base KML primitives."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import List, Optional, Sequence

from . import base
from .geodesy import bearing, destination, distance

__all__ = ["wedge", "circle", "ellipse", "rectangle", "ngon", "annulus", "arc",
           "corridor", "concentric_rings", "grid",
           "fresnel_zone", "cylinder", "cone", "dome", "sphere"]

_LIGHT_SPEED = 299_792_458.0   # meters per second


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


def wedge(center: Sequence[float], azimuth: float, width: float, radius: float,
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
        or down out of the horizontal plane about its center.

    INPUTS:
        center (List of three Floats):
            A list of [x, y, z] coordinates that will be the origin of the pie wedge.
        azimuth (Float):
            The direction that the center of the wedge's arc will point. 0 = True North.
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
            to 'ABS' and the center's z is treated as an absolute (MSL) altitude.
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

    # Attribute table
    headers_default = ['Azimuth', 'Width', 'Radius', 'Tilt', 'Steps', 'Center Lat', 'Center Lng', 'Center Z']
    headers = kwargs.pop('headers', headers_default)

    attrs_default = [azimuth, width, radius, tilt, steps, center[1], center[0], center[2]]
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
        coords = [destination(center, az, radius) for az in azimuths]
    else:
        coords = [_tilt_wedge_coord(center, azimuth, az, radius, tilt) for az in azimuths]
        kwargs.setdefault('z_mode', 'ABS')

    # Add the wedge vertex as the initial and final coordinate to close the polygon.
    coords.insert(0, center)
    coords.append(center)

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


def rectangle(center: Sequence[float], width: float, height: float, *,
              orient: float = 0.0, name: str = 'Rectangle', **kwargs) -> ET.Element:
    """
    Creates a rectangular KML polygon.

    OVERVIEW:
        Builds a rectangle centered on a point. At 'orient' = 0 'width' runs
        east-west and 'height' runs north-south; increasing 'orient' turns the
        rectangle clockwise (degrees from true north).

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the rectangle's center.
        width (Float):
            The east-west size (at 'orient' = 0), in meters.
        height (Float):
            The north-south size (at 'orient' = 0), in meters.
        orient (Float) [Optional]:
            Clockwise rotation, in degrees from true north. (Default = 0.0)
        name (String) [Optional]:
            The name given to the rectangle within the KML. (Default = 'Rectangle')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        rectangle (Element):
            An XML element representing a KML polygon.
    """

    headers_default = ['Width (m)', 'Height (m)', 'Rotation', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [width, height, orient, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    o = math.radians(orient)
    ring = []
    for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        x, y = sx * width / 2, sy * height / 2
        east = x * math.cos(o) - y * math.sin(o)
        north = x * math.sin(o) + y * math.cos(o)
        ring.append(_enu(center, east, north))
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def ngon(center: Sequence[float], radius: float, sides: int, *, orient: float = 0.0,
         name: str = 'Polygon', **kwargs) -> ET.Element:
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
            The name given to the polygon within the KML. (Default = 'Polygon')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        ngon (Element):
            An XML element representing a KML polygon.
    """

    if sides < 3:
        raise ValueError("ngon requires at least 3 sides.")

    headers_default = ['Sides', 'Radius (m)', 'Rotation', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [sides, radius, orient, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    ring = [destination(center, orient + i * 360 / sides, radius) for i in range(sides)]
    ring.append(ring[0])

    return base.polygon([ring], name, headers=headers, attrs=attrs, **kwargs)


def annulus(center: Sequence[float], outer_radius: float, inner_radius: float, *,
            steps: int = 48, name: str = 'Annulus', **kwargs) -> ET.Element:
    """
    Creates an annular (ring) KML polygon.

    OVERVIEW:
        Builds a filled ring: an outer circle of 'outer_radius' with a concentric
        inner circle of 'inner_radius' punched out as a hole. Both circles are
        approximated with 'steps' vertices.

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the ring's center.
        outer_radius (Float):
            The outer edge radius, in meters.
        inner_radius (Float):
            The inner (hole) radius, in meters. Must be smaller than outer_radius.
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

    if inner_radius >= outer_radius:
        raise ValueError("annulus inner_radius must be smaller than outer_radius.")

    headers_default = ['Outer (m)', 'Inner (m)', 'Steps', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [outer_radius, inner_radius, steps, center[1], center[0]]
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

    headers_default = ['Radius (m)', 'Start Az', 'End Az', 'Center Lat', 'Center Lng']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [radius, start_az, end_az, center[1], center[0]]
    attrs = kwargs.pop('attrs', attrs_default)

    coords = [destination(center, start_az + (end_az - start_az) * i / steps, radius)
              for i in range(steps + 1)]

    return base.line(coords, name, headers=headers, attrs=attrs, **kwargs)


def corridor(path: Sequence[Sequence[float]], width: float, *,
             name: str = 'Corridor', **kwargs) -> ET.Element:
    """
    Creates an even-width corridor around a path, as a KML polygon.

    OVERVIEW:
        Buffers an open path into a polygon of constant 'width' by offsetting each
        vertex along the bisector of its turn (a miter join), so the corridor keeps
        an even width through bends. Useful for trails, rail lines, pipelines, and
        flight corridors.

    INPUTS:
        path (List of Coordinates):
            An ordered list of [lon, lat] or [lon, lat, z] coordinates (2 or more).
        width (Float):
            The corridor's total width, in meters.
        name (String) [Optional]:
            The name given to the corridor within the KML. (Default = 'Corridor')
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function.

    OUTPUT:
        corridor (Element):
            An XML element representing a KML polygon.
    """

    m = len(path)
    if m < 2:
        raise ValueError("corridor requires a path of at least 2 points.")

    headers_default = ['Width (m)', 'Points']
    headers = kwargs.pop('headers', headers_default)
    attrs_default = [width, m]
    attrs = kwargs.pop('attrs', attrs_default)

    hw, left, right = width / 2, [], []
    for i, p in enumerate(path):
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


def concentric_rings(center: Sequence[float], radii: Optional[Sequence[float]] = None, *,
                     start: Optional[float] = None, interval: Optional[float] = None,
                     count: Optional[int] = None,
                     steps: int = 48, name: str = 'Range Rings',
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
            An explicit radius, in meters, for each ring. If omitted, the ring
            radii are built from 'start', 'interval', and 'count'.
        start (Float) [Optional]:
            The radius of the innermost ring, in meters (generator form).
        interval (Float) [Optional]:
            The spacing between successive rings, in meters (generator form).
        count (Integer) [Optional]:
            The number of rings to generate (generator form).
        steps (Integer) [Optional]:
            The number of vertices around each ring. (Default = 48)
        name (String) [Optional]:
            The folder name. (Default = 'Range Rings')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.line function; applied to
            every ring.

    OUTPUT:
        concentric_rings (Element):
            An XML element representing a KML folder of line rings.
    """

    if radii is None:
        if start is None or interval is None or count is None:
            raise ValueError(
                "concentric_rings needs either 'radii' or all of "
                "'start', 'interval', and 'count'.")
        radii = [start + i * interval for i in range(count)]

    rings = []
    for r in radii:
        coords = [destination(center, i * 360 / steps, r) for i in range(steps)]
        coords.append(coords[0])
        rings.append(base.line(coords, f'{r:.0f} m', **kwargs))

    return base.folder(name, rings, collapsed=collapsed, hidden=hidden)


def grid(center: Sequence[float], cell: float, cols: int, rows: int, *,
         kind: str = 'square', orient: float = 0.0, name: str = 'Grid',
         collapsed: bool = True, hidden: bool = False, **kwargs) -> ET.Element:
    """
    Creates a grid of cells (a fishnet) as a KML folder of polygons.

    OVERVIEW:
        Tiles a 'cols' by 'rows' grid of cells centered on a point and returns them
        in a folder. With kind='square' each cell is a square of side 'cell' meters
        (edge to edge). With kind='hex' each cell is a flat-top hexagon of radius
        'cell' meters (center to vertex), interlocked edge to edge.

        'orient' turns the whole grid clockwise about its center, so the cells can
        be lined up with a feature that is not oriented north-up (a rotated parking
        lot, a runway apron, a survey block).

    INPUTS:
        center (List of Floats):
            A [lon, lat] or [lon, lat, z] coordinate for the grid's center.
        cell (Float):
            Square side length, or hexagon radius, in meters (see 'kind').
        cols (Integer):
            The number of columns.
        rows (Integer):
            The number of rows.
        kind (String) [Optional]:
            'square' for square cells or 'hex' for hexagonal cells.
            (Default = 'square')
        orient (Float) [Optional]:
            Clockwise rotation of the whole grid about its center, in degrees from
            true north. (Default = 0.0)
        name (String) [Optional]:
            The folder name. (Default = 'Grid')
        collapsed (Boolean) [Optional]:
            Whether the folder starts collapsed in the places panel. (Default = True)
        hidden (Boolean) [Optional]:
            Whether the folder starts hidden. (Default = False)
        **kwargs:
            Any keyword argument accepted by the kmlb.polygon function; applied to
            every cell.

    OUTPUT:
        grid (Element):
            An XML element representing a KML folder of polygon cells.
    """

    kind = kind.lower()
    if kind not in ('square', 'hex'):
        raise ValueError("grid kind must be 'square' or 'hex'.")
    if cols < 1 or rows < 1:
        raise ValueError("grid requires cols and rows of at least 1.")

    o = math.radians(orient)
    cos_o, sin_o = math.cos(o), math.sin(o)

    def place(east, north):
        # Rotate the local offset clockwise by 'orient' before projecting to lon/lat.
        return _enu(center, east * cos_o - north * sin_o, east * sin_o + north * cos_o)

    cells = []
    if kind == 'square':
        half_w, half_h = cols * cell / 2, rows * cell / 2
        for r in range(rows):
            for c in range(cols):
                x0, y0 = -half_w + c * cell, -half_h + r * cell
                ring = [place(x0, y0), place(x0 + cell, y0),
                        place(x0 + cell, y0 + cell), place(x0, y0 + cell)]
                ring.append(ring[0])
                cells.append(base.polygon([ring], f'cell {r},{c}', **kwargs))
    else:
        # Flat-top hexagons: columns step 1.5*radius apart, rows step sqrt(3)*radius,
        # and odd columns shift half a row so the cells interlock edge to edge.
        dx, dy = cell * 1.5, cell * math.sqrt(3)
        for r in range(rows):
            for c in range(cols):
                east = (c - cols / 2) * dx
                north = (r - rows / 2) * dy + (dy / 2 if c % 2 else 0)
                hub = place(east, north)
                ring = [destination(hub, 30 + orient + i * 60, cell) for i in range(6)]
                ring.append(ring[0])
                cells.append(base.polygon([ring], f'hex {r},{c}', **kwargs))

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


def _fresnel_rings(point_a: Sequence[float], point_b: Sequence[float],
                   wavelength: float, zone: int, cross_rings: int,
                   ring_strips: int) -> List[List[List[float]]]:
    """
    Sample the Fresnel ellipsoid as a stack of cross-section rings.

    Returns 'cross_rings' rings along the line-of-sight; each ring is a list of
    'ring_strips' [lon, lat, z] vertices lying in the plane perpendicular to the
    LOS axis. The end rings collapse to the two endpoints (radius 0). Altitudes
    are absolute (point z + local up offset).
    """
    d_total = distance(point_a, point_b)
    az = bearing(point_a, point_b)
    dz = point_b[2] - point_a[2]

    az_r = math.radians(az)
    # Orthonormal frame around the LOS axis: 'side' is horizontal and
    # perpendicular; 'up_perp' completes the frame (near-vertical).
    u = _unit((d_total * math.sin(az_r), d_total * math.cos(az_r), dz))
    side = (math.cos(az_r), -math.sin(az_r), 0.0)
    up_perp = _cross(u, side)

    rings = []
    for j in range(cross_rings):
        frac = j / (cross_rings - 1)
        d1 = frac * d_total
        d2 = d_total - d1
        r = _fresnel_radius(zone, wavelength, d1, d2, d_total)

        # Axis point as an ENU offset from point_a's ground position.
        ax_e = d1 * math.sin(az_r)
        ax_n = d1 * math.cos(az_r)
        ax_u = frac * dz

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
        rings.append(ring)
    return rings


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
                 path_color='red', center_ring_color='cyan', z_mode: str = 'ABS',
                 collapsed: bool = True, hidden: bool = False) -> ET.Element:
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
            tube lengthwise; an odd value puts a ring exactly at mid-path
            (Default = 25).
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

    OUTPUT:
        element (Element):
            A KML 'Folder' holding the tube plus the line-of-sight path and/or the
            center ring when either is drawn, or the tube 'Placemark' on its own
            when both 'include_path' is False and 'center_ring_color' is None.
    """

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
        # The widest cross-section sits at (or nearest) mid-path.
        mid = len(rings) // 2
        mid_frac = mid / (cross_rings - 1)
        mid_alt = point_a[2] + mid_frac * dz
        ring_headers = ['Radius (m)', 'Distance from End A (m)', 'Altitude (m)']
        ring_attrs = [round(r_max, 2), round(mid_frac * d_total, 1), round(mid_alt, 1)]
        ring_blurb = f"Widest cross-section\nRadius {r_max:.1f} m"
        pieces.append(_ring_placemark(rings[mid], f"{name} - Center Ring", center_ring_color,
                                      z_mode, ring_headers, ring_attrs, ring_blurb))

    if len(pieces) == 1:
        return tube

    return base.folder(name, pieces, collapsed=collapsed, hidden=hidden)


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


def _axis_ring(center, radius, dist, sides, frame):
    """A ring of 'sides' points, radius 'radius', 'dist' along the axis from center."""
    u, side, up_perp = frame
    ring = []
    for i in range(sides):
        phi = 2 * math.pi * i / sides
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


def _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb):
    """Assemble a 3D solid as a single MultiGeometry Placemark of polygon panels."""
    fill_hex, fill_opacity = base._resolve_color(color)

    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)
    ET.SubElement(placemark, 'visibility').text = '0' if hidden else '1'

    # Translucent fill with an opaque outline of the same hue.
    style = ET.SubElement(placemark, 'Style')
    ET.SubElement(ET.SubElement(style, 'PolyStyle'), 'color').text = base._kml_color(fill_hex, fill_opacity)
    line_style = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_style, 'color').text = base._kml_color(fill_hex, 100)
    ET.SubElement(line_style, 'width').text = '1.0'

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
    return placemark


def cylinder(center: Sequence[float], radius: float, height: float, *,
             azimuth: float = 0.0, elevation: float = 90.0, anchor: str = 'base',
             sides: int = 32, color=('#66ff33', 40), cap: bool = True,
             name: str = 'Cylinder', z_mode: str = 'ABS', hidden: bool = False) -> ET.Element:
    """
    Creates a 3D cylinder as a KML solid.

    OVERVIEW:
        Builds a cylinder that runs from a base circle to a matching top circle,
        as a 'MultiGeometry' of polygon panels. Useful for volumes such as a column
        of airspace, a tank, or a tower footprint extruded along an axis. By
        default it stands vertical; 'azimuth'/'elevation' point the axis elsewhere.

        The cylinder is three-dimensional, so it uses absolute altitude: the
        center's z is an absolute (MSL) altitude for the base.

    INPUTS:
        center (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The cylinder radius in meters.
        height (Float):
            The length in meters along the axis (the far cap sits 'height' from the
            base, in the axis direction).
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'elevation' is not straight up or down.
        elevation (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which end sits at 'center': 'base' = the near face (body extends along
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
        name (String) [Optional]:
            The name to be given to the cylinder (Default = 'Cylinder').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the cylinder starts hidden (Default = False).

    OUTPUT:
        cylinder (Element):
            A KML 'Placemark' containing the cylinder 'MultiGeometry'.
    """

    frame = _axis_frame(azimuth, elevation)
    off = _anchor_shift(anchor, 0.0, height)
    bottom = _axis_ring(center, radius, 0.0 - off, sides, frame)
    top = _axis_ring(center, radius, height - off, sides, frame)

    panels = _wall(bottom, top)
    if cap:
        panels.append(bottom + [bottom[0]])
        panels.append(top + [top[0]])

    base_alt = center[2] if len(center) > 2 else 0
    headers = ['Radius (m)', 'Height (m)', 'Base Altitude (m)', 'Sides']
    attrs = [radius, height, round(base_alt, 1), sides]
    blurb = f"Cylinder · r={radius:g} m\nHeight {height:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb)


def cone(center: Sequence[float], radius: float, height: float, *,
         azimuth: float = 0.0, elevation: float = 90.0, anchor: str = 'base',
         sides: int = 32, color=('#3399ff', 40), cap: bool = True, name: str = 'Cone',
         z_mode: str = 'ABS', hidden: bool = False) -> ET.Element:
    """
    Creates a 3D cone as a KML solid.

    OVERVIEW:
        Builds a cone between a circular base and a single apex, as a
        'MultiGeometry' of triangular panels. Useful for beams, sensor cones, or
        funnel volumes. By default it stands vertical with the base at 'center';
        'azimuth'/'elevation' point the axis elsewhere and 'anchor' picks which end
        sits at the center.

        The cone is three-dimensional, so it uses absolute altitude: the center's
        z is an absolute (MSL) altitude.

    INPUTS:
        center (List of three Floats):
            The anchor point as [lon, lat, z]; z is an absolute (MSL) altitude.
            This is the base center, or the apex when 'anchor' is 'top'.
        radius (Float):
            The base radius in meters.
        height (Float):
            The length in meters between the base and the apex along the axis.
        azimuth (Float) [Optional]:
            The compass bearing the axis leans toward, in degrees (Default = 0.0).
            Only has an effect when 'elevation' is not straight up or down.
        elevation (Float) [Optional]:
            The angle of the axis above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which point sits at 'center': 'base' = the base disc, apex out along the
            axis (a spike/funnel); 'center' = mid-way along the axis; 'top' = the
            apex, widening to the base out along the axis (a directional beam)
            (Default = 'base').
        sides (Integer) [Optional]:
            The number of facets around the base. More gives a rounder cone
            (Default = 32).
        color (Color) [Optional]:
            The fill color as a palette name, a '#rrggbb' hex string, or a
            (color, opacity) pair. The outline uses the same hue at full opacity
            (Default = ('#3399ff', 40)).
        cap (Bool) [Optional]:
            True = close the base with a disc cap (Default = True).
        name (String) [Optional]:
            The name to be given to the cone (Default = 'Cone').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the cone starts hidden (Default = False).

    OUTPUT:
        cone (Element):
            A KML 'Placemark' containing the cone 'MultiGeometry'.
    """

    frame = _axis_frame(azimuth, elevation)
    if anchor == 'top':
        base_u, apex_u = height, 0.0          # apex at center, base opens along axis (beam)
    elif anchor == 'center':
        base_u, apex_u = -height / 2, height / 2
    else:  # 'base'
        base_u, apex_u = 0.0, height          # base at center, apex out along axis
    base_ring = _axis_ring(center, radius, base_u, sides, frame)
    apex = _axis_point(center, apex_u, frame)

    panels = [[base_ring[i], base_ring[(i + 1) % sides], apex, base_ring[i]] for i in range(sides)]
    if cap:
        panels.append(base_ring + [base_ring[0]])

    base_alt = center[2] if len(center) > 2 else 0
    headers = ['Base Radius (m)', 'Height (m)', 'Base Altitude (m)', 'Sides']
    attrs = [radius, height, round(base_alt, 1), sides]
    blurb = f"Cone · r={radius:g} m\nHeight {height:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb)


def dome(center: Sequence[float], radius: float, *, azimuth: float = 0.0,
         elevation: float = 90.0, anchor: str = 'base', sides: int = 32, rings: int = 8,
         color=('#ff9933', 40), cap: bool = True, name: str = 'Dome',
         z_mode: str = 'ABS', hidden: bool = False) -> ET.Element:
    """
    Creates a 3D dome (hemisphere) as a KML solid.

    OVERVIEW:
        Builds a hemispherical dome that rises from a base circle to a pole point,
        as a 'MultiGeometry' of polygon panels. Useful for radar/sensor domes,
        stadium roofs, or hemispheric coverage volumes. By default the pole points
        straight up; 'azimuth'/'elevation' aim it elsewhere.

        The dome is three-dimensional, so it uses absolute altitude: the center's
        z is an absolute (MSL) altitude for the base.

    INPUTS:
        center (List of three Floats):
            The base center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The dome radius in meters (also its height along the axis).
        azimuth (Float) [Optional]:
            The compass bearing the pole leans toward, in degrees (Default = 0.0).
            Only has an effect when 'elevation' is not straight up or down.
        elevation (Float) [Optional]:
            The angle of the pole above horizontal in degrees: 90 = straight up
            (Default), 0 = horizontal, -90 = straight down.
        anchor (String) [Optional]:
            Which point sits at 'center': 'base' = the base rim center (pole out
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
        name (String) [Optional]:
            The name to be given to the dome (Default = 'Dome').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the dome starts hidden (Default = False).

    OUTPUT:
        dome (Element):
            A KML 'Placemark' containing the dome 'MultiGeometry'.
    """

    frame = _axis_frame(azimuth, elevation)
    off = _anchor_shift(anchor, 0.0, radius)   # rim at 0, pole at radius along the axis
    levels = []
    for r in range(rings + 1):
        phi = math.radians(90 * r / rings)
        levels.append(_axis_ring(center, radius * math.cos(phi), radius * math.sin(phi) - off, sides, frame))

    panels = []
    for r in range(rings):
        panels.extend(_wall(levels[r], levels[r + 1]))
    if cap:
        panels.append(levels[0] + [levels[0][0]])

    base_alt = center[2] if len(center) > 2 else 0
    headers = ['Radius (m)', 'Base Altitude (m)', 'Sides', 'Rings']
    attrs = [radius, round(base_alt, 1), sides, rings]
    blurb = f"Dome · r={radius:g} m\nHemisphere"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb)


def sphere(center: Sequence[float], radius: float, *, azimuth: float = 0.0,
           elevation: float = 90.0, anchor: str = 'center', sides: int = 24, rings: int = 12,
           color=('#9933ff', 40), name: str = 'Sphere', z_mode: str = 'ABS',
           hidden: bool = False) -> ET.Element:
    """
    Creates a 3D sphere as a KML solid.

    OVERVIEW:
        Builds a sphere around a center point, as a 'MultiGeometry' of polygon
        panels stacked pole to pole. Useful for effect radii, exclusion volumes,
        or any point-centered 3D extent.

        Unlike the other solids, 'center' is the sphere's geometric center, so the
        sphere extends 'radius' in every direction. It is three-dimensional and
        uses absolute altitude, so give the center a z of at least 'radius' for it
        to sit above the ground. 'azimuth'/'elevation' aim the pole axis, which
        only shifts where the mesh poles/seams sit (a sphere is symmetric).

    INPUTS:
        center (List of three Floats):
            The sphere center as [lon, lat, z]; z is an absolute (MSL) altitude.
        radius (Float):
            The sphere radius in meters.
        azimuth (Float) [Optional]:
            The compass bearing the pole axis leans toward, in degrees
            (Default = 0.0). Only shifts the mesh seams, not the silhouette.
        elevation (Float) [Optional]:
            The angle of the pole axis above horizontal in degrees: 90 = poles up
            and down (Default), 0 = poles horizontal.
        anchor (String) [Optional]:
            Which point sits at 'center': 'center' = the geometric center
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
        name (String) [Optional]:
            The name to be given to the sphere (Default = 'Sphere').
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF')
            (Default = 'ABS'). The solid only renders under a non-clamped mode.
        hidden (Bool) [Optional]:
            True = the sphere starts hidden (Default = False).

    OUTPUT:
        sphere (Element):
            A KML 'Placemark' containing the sphere 'MultiGeometry'.
    """

    frame = _axis_frame(azimuth, elevation)
    off = _anchor_shift(anchor, -radius, radius)   # poles at -radius and +radius along the axis
    levels = []
    for la in range(rings + 1):
        phi = math.radians(-90 + 180 * la / rings)
        levels.append(_axis_ring(center, radius * math.cos(phi), radius * math.sin(phi) - off, sides, frame))

    panels = []
    for la in range(rings):
        panels.extend(_wall(levels[la], levels[la + 1]))

    center_alt = center[2] if len(center) > 2 else 0
    headers = ['Radius (m)', 'Center Altitude (m)', 'Sides', 'Rings']
    attrs = [radius, round(center_alt, 1), sides, rings]
    blurb = f"Sphere · r={radius:g} m\nCenter {center_alt:g} m"
    return _solid_placemark(panels, name, color, z_mode, hidden, headers, attrs, blurb)

# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Geodesic measurements on the WGS-84 ellipsoid: distance, bearing, destination.

These are thin, user-facing wrappers around the Vincenty solutions in
:mod:`kmlb._geo`. ``distance`` and ``bearing`` solve the *inverse* problem
(what separates two known points); ``destination`` solves the *direct* problem
(where you end up traveling a bearing and distance from a known point).
"""

from __future__ import annotations

from typing import List, Sequence

from ._geo import _vicenty_direct, _vicenty_inverse

__all__ = ["distance", "bearing", "destination"]


def distance(p1: Sequence[float], p2: Sequence[float], precision: int = 3) -> float:
    """
    Measures the distance between two coordinates.

    OVERVIEW:
        Returns the geodesic distance, in meters, between ``p1`` and ``p2``
        measured across the surface of the WGS-84 ellipsoid (Vincenty's inverse
        solution). For the direction between the points, see :func:`bearing`.

    INPUTS:
        p1 (List of Floats):
            A [longitude, latitude] (or [longitude, latitude, elevation]) coordinate.
            An elevation (z) value, if present, is ignored.
        p2 (List of Floats):
            A second [longitude, latitude] (or [longitude, latitude, elevation]) coordinate.
            An elevation (z) value, if present, is ignored.
        precision (Integer) [Optional]:
            Number of decimal places to retain in the result. (Default = 3)

    OUTPUT:
        distance (Float):
            The distance between the two coordinates, in meters.

    Example
    -------
    Measure the distance between two points::

        boston = [-71.057083, 42.361145]
        nyc = [-74.006015, 40.712776]
        kmlb.distance(boston, nyc)  # -> 306682.412 meters
    """
    dist_m, _, _ = _vicenty_inverse(p1, p2, precision)
    return dist_m


def bearing(p1: Sequence[float], p2: Sequence[float], precision: int = 3) -> float:
    """
    Measures the initial bearing from one coordinate to another.

    OVERVIEW:
        Returns the forward azimuth, in degrees clockwise from true north
        (0 = north, 90 = east), of the geodesic from ``p1`` to ``p2`` on the
        WGS-84 ellipsoid (Vincenty's inverse solution). Because geodesics curve,
        this is the bearing *at the start* of the path; it will differ from the
        bearing measured on arrival. For the separation between the points, see
        :func:`distance`.

    INPUTS:
        p1 (List of Floats):
            The origin [longitude, latitude] (or [longitude, latitude, elevation]) coordinate.
            An elevation (z) value, if present, is ignored.
        p2 (List of Floats):
            The target [longitude, latitude] (or [longitude, latitude, elevation]) coordinate.
            An elevation (z) value, if present, is ignored.
        precision (Integer) [Optional]:
            Number of decimal places to retain in the result. (Default = 3)

    OUTPUT:
        bearing (Float):
            The initial bearing from ``p1`` to ``p2``, in degrees (0 - 360)
            clockwise from true north.

    Example
    -------
    Find the heading from one point to another::

        boston = [-71.057083, 42.361145]
        nyc = [-74.006015, 40.712776]
        kmlb.bearing(boston, nyc)  # -> ~234.0 degrees (roughly southwest)
    """
    _, init_bearing, _ = _vicenty_inverse(p1, p2, precision)
    return init_bearing


def destination(origin: Sequence[float], bearing: float, distance: float,
                precision: int = 3) -> List[float]:
    """
    Finds the coordinate reached from an origin along a bearing and distance.

    OVERVIEW:
        Returns the coordinate reached by travelling ``distance`` meters from
        ``origin`` along ``bearing`` (degrees clockwise from true north) across
        the surface of the WGS-84 ellipsoid (Vincenty's direct solution). This is
        the inverse operation of :func:`distance` / :func:`bearing`.

    INPUTS:
        origin (List of Floats):
            A [longitude, latitude] (or [longitude, latitude, elevation]) coordinate.
            An elevation (z) value, if present, is carried through unchanged.
        bearing (Float):
            The direction to travel, in degrees clockwise from true north (0 = north).
        distance (Float):
            The distance to travel, in meters.
        precision (Integer) [Optional]:
            Number of decimal places to retain for the internal bearing
            calculation. (Default = 3)

    OUTPUT:
        coord (List of Floats):
            The destination [longitude, latitude] (or [longitude, latitude, elevation]).

    Example
    -------
    Find the point 100 km due east of a coordinate::

        start = [-71.057083, 42.361145]
        kmlb.destination(start, 90, 100_000)  # -> [-69.843..., 42.355...]
    """
    coord, _ = _vicenty_direct(origin, bearing, distance, precision)
    return coord

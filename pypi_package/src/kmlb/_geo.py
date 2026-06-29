# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Geodetic helpers: Vincenty distance/bearing on the WGS-84 ellipsoid."""

from __future__ import annotations

from math import sin, cos, sqrt, atan, atan2, tan, radians, degrees
from typing import Sequence

__all__ = []

# Ellipsoid Parameters (WGS-84):

# Length of the semi-major axis of the ellipsoid (radius at the equator, meters).
_R_EQ = 6378137.0

# Flattening of the ellipsoid.
_F = 1 / 298.257223563

# Length of the semi-minor axis of the ellipsoid (polar radius, meters).
_R_PM = (1 - _F) * _R_EQ


def _vicenty_inverse(p1: Sequence[float], p2: Sequence[float], precision: int = 3,
                    max_iter: int = 250, tol: float = 10 ** (-12)) -> tuple[float, float, float]:
    """
    Iteratively calculates the distance along the surface of an ellipsoid between two points.

    INPUTS:
        p1 (List of two Floats):
            Point 1. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        p2 (List of two Floats):
            Point 2. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        precision (Integer) [Optional]:
            Number of decimal places to retain in the resulting distance and bearings. (Default = 3)
        max_iter (Integer) [Optional]:
            Maximum number of iterations to run the formula for if tolerance is not satisfied. (Default = 250)
        tol (Float) [Optional]:
            Convergence tolerance.
            If the tolerance is larger than the difference between the longitude values calculated in the current step
            and the longitude value calculated in the previous step, the formula will stop iterating as the desired
            tolerance has been achieved. (Default = 10^(-12) or 0.000 000 000 001 of a degree)

    OUTPUTS:
        dist_m (Float):
            The distance (in meters) between the provided coordinates.
        init_bearing (Float):
            The forward azimuth between p1 and p2 in degrees from geographic north.
        final_bearing (Float):
            The final azimuth between p1 and p2 in degrees from geographic north.
    """

    # Convert coordinate values to float
    p1 = [float(c) for c in p1]
    p2 = [float(c) for c in p2]

    # Pull lat and lng from coordinates
    lng1, lat1 = p1[:2]
    lng2, lat2 = p2[:2]

    # Reduced latitudes (latitude on the auxiliary sphere)
    u_1 = atan((1-_F) * tan(radians(lat1)))
    u_2 = atan((1-_F) * tan(radians(lat2)))

    # Difference in longitude of two points
    lng_diff = radians(lng2 - lng1)

    # Set initial value of lambda to lng_diff
    lam = lng_diff

    # Pre-calculated values to make formulas shorter
    sin_u1 = sin(u_1)
    cos_u1 = cos(u_1)
    sin_u2 = sin(u_2)
    cos_u2 = cos(u_2)

    # Variables that will be set from inside of loop
    sigma = None
    sin_sigma = None
    cos_sigma = None
    cos_sq_alpha = None
    cos2_sigma_m = None

    for i in range(max_iter):
        cos_lambda = cos(lam)
        sin_lambda = sin(lam)

        sin_sigma = sqrt((cos_u2 * sin(lam)) ** 2 + (cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos_lambda) ** 2)
        cos_sigma = sin_u1 * sin_u2 + cos_u1 * cos_u2 * cos_lambda
        sigma = atan2(sin_sigma, cos_sigma)
        try:
            sin_alpha = (cos_u1 * cos_u2 * sin_lambda) / sin_sigma
        except ZeroDivisionError:
            sin_alpha = 0

        cos_sq_alpha = 1 - sin_alpha ** 2

        try:
            cos2_sigma_m = cos_sigma - ((2 * sin_u1 * sin_u2) / cos_sq_alpha)

        except ZeroDivisionError:
            cos2_sigma_m = 0

        c = (_F / 16) * cos_sq_alpha * (4 + _F * (4 - 3 * cos_sq_alpha))
        lambda_prev = lam
        lam = lng_diff + (1 - c) * _F * sin_alpha * (sigma + c * sin_sigma * (cos2_sigma_m + c * cos_sigma * (-1 + 2 * cos2_sigma_m ** 2)))

        # Successful convergence
        diff = abs(lambda_prev - lam)
        if diff <= tol:
            break

    u_sq = cos_sq_alpha * ((_R_EQ**2 - _R_PM**2) / _R_PM**2)
    a = 1 + (u_sq / 16384) * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    b = (u_sq / 1024) * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sig = b * sin_sigma * (cos2_sigma_m + 0.25 * b * (cos_sigma * (-1 + 2 * cos2_sigma_m ** 2) - (1 / 6) * b * cos2_sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos2_sigma_m ** 2)))

    dist_m = _R_PM * a * (sigma - delta_sig)
    dist_m = round(dist_m, precision)

    init_bearing = atan2(cos_u2 * sin(lam), cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos(lam))
    init_bearing = round(degrees(init_bearing), precision)
    if init_bearing < 0:
        init_bearing += 360
    final_bearing = atan2(cos_u1 * sin(lam), (sin_u1 * -1) * cos_u2 + cos_u1 * sin_u2 * cos(lam))
    final_bearing = round(degrees(final_bearing), precision)
    if final_bearing < 0:
        final_bearing += 360

    return dist_m, init_bearing, final_bearing


def _vicenty_direct(p1: Sequence[float], init_bearing: float, distance_m: float, precision: int = 3,
                   max_iter: int = 250, tol: float = 10 ** (-12)) -> tuple[list, float]:
    """
    Iteratively calculates the final coordinates (p2) of a line when given a starting point (p1), azimuth, and distance.

    INPUTS:
        p1 (List of two Floats):
            Point 1. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates may be provided. The Z coordinate will pass through unprocessed.)
        init_bearing (Float):
            The forward azimuth from p1 (in degrees from geographic north).
        distance_m (Float):
            The distance (in meters) of p2 from p1.
        precision (Integer) [Optional]:
            Number of decimal places to retain for the final bearing. (Default = 3)
        max_iter (Integer) [Optional]:
            Maximum number of iterations to run the formula for if tolerance is not satisfied. (Default = 250)
        tol (Float) [Optional]:
            Convergence tolerance.
            If the tolerance is larger than the difference between the longitude values calculated in the current step
            and the longitude value calculated in the previous step, the formula will stop iterating as the desired
            tolerance has been achieved. (Default = 10^(-12) or 0.000 000 000 001 of a degree)

    OUTPUTS:
        p2 (List of Floats):
            Point 2. A list of x, y coordinates as [x, y].
        final_bearing (Float):
            The final azimuth between p1 and p2 in degrees from geographic north.
    """

    # Pull lat and lng from coordinates as floats
    p1 = [float(c) for c in p1]
    p1_x, p1_y = p1[:2]

    init_bearing = radians(init_bearing)

    # Convert lat and lng to radians
    p1_x_rads = radians(p1_x)
    p1_y_rads = radians(p1_y)

    # Pre-calculated values to make formulas shorter
    tan_u1 = (1 - _F) * tan(p1_y_rads)
    cos_u1 = 1 / sqrt(1 + tan_u1**2)
    sin_u1 = tan_u1 * cos_u1
    sigma_1 = atan2(tan_u1, cos(init_bearing))
    sin_alpha = cos_u1 * sin(init_bearing)
    cos_sq_alpha = 1 - sin_alpha**2
    u_sq = cos_sq_alpha * (_R_EQ**2 - _R_PM**2) / _R_PM**2
    a = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    b = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    sigma = distance_m / (_R_PM * a)

    cos_2sigma_m = None

    for i in range(max_iter):
        cos_2sigma_m = cos(2 * sigma_1 + sigma)
        delta_sigma = b * sin(sigma) * (cos_2sigma_m + b / 4 * (cos(sigma) * (-1 + 2 * cos_2sigma_m**2) - b / 6 * cos_2sigma_m * (-3 + 4 * sin(sigma)**2) * (-3 + 4 * cos_2sigma_m**2)))

        sigma_prime = distance_m / (_R_PM * a) + delta_sigma

        diff = abs(sigma - sigma_prime)

        sigma = sigma_prime

        if diff <= tol:
            break

    j = sin_u1 * cos(sigma) + cos_u1 * sin(sigma) * cos(init_bearing)
    m = (1 - _F) * sqrt(sin_alpha ** 2 + (sin_u1 * sin(sigma) - cos_u1 * cos(sigma) * cos(init_bearing)) ** 2)
    p2_y_rads = atan2(j, m)

    lam = atan2((sin(sigma) * sin(init_bearing)), (cos_u1 * cos(sigma) - sin_u1 * sin(sigma) * cos(init_bearing)))
    c = _F / 16 * cos_sq_alpha * (4 + _F * (4 - 3 * cos_sq_alpha))
    p = lam - (1 - c) * _F * sin_alpha * (sigma + c * sin(sigma) * (cos_2sigma_m + c * cos(sigma) * (-1 + 2 * cos_2sigma_m**2)))
    p2_x_rads = p1_x_rads + p
    final_bearing = atan2(sin_alpha, (-1 * (sin_u1 * sin(sigma) - cos_u1 * cos(sigma) * cos(init_bearing))))

    p2 = [degrees(p2_x_rads), degrees(p2_y_rads)]
    p2.extend(p1[2:])
    final_bearing = round(degrees(final_bearing), precision)

    if final_bearing < 0:
        final_bearing += 360

    return p2, final_bearing


def _determinant(p1: Sequence[float], p2: Sequence[float], p3: Sequence[float]) -> float:
    """
    Calculates the _determinant of a three-point line.

    OVERVIEW:
        Used for determining if p2 --> p3 is clockwise, counterclockwise, or collinear relative to
        p1 --> p2.

        - negative = counterclockwise
        - 0 = collinear
        - positive = clockwise

        Formula:
        (y2 - y1) * (x3 - x2) - (y3 - y2) * (x2 - x1)

    INPUTS:
        p1 (List of two Floats):
            Point 1. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        p2 (List of two Floats):
            Point 2. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        p3 (List of two Floats):
            Point 3. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)

    OUTPUT:
        det (Float):
            The _determinant of the three-point line.
    """
    det = (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p3[1] - p2[1]) * (p2[0] - p1[0])

    return det

"""Unit tests for the geodetic helpers in ``kmlb.gis_basics``."""

import pytest

from kmlb import _geo as gb


# --- ellipsoid constants ---------------------------------------------------

def test_wgs84_constants():
    assert gb._R_EQ == 6378137.0
    # polar radius is slightly smaller than the equatorial radius
    assert gb._R_PM < gb._R_EQ
    assert round(gb._R_PM, 3) == 6356752.314


# --- _vicenty_inverse -------------------------------------------------------

def test_inverse_zero_distance():
    dist, _, _ = gb._vicenty_inverse([-71.0, 42.0], [-71.0, 42.0])
    assert dist == 0.0


def test_inverse_known_pair():
    # ~1 degree of latitude is roughly 111 km.
    dist, init_bearing, _ = gb._vicenty_inverse([0.0, 0.0], [0.0, 1.0])
    assert dist == pytest.approx(110574.389, abs=1.0)
    assert init_bearing == pytest.approx(0.0, abs=1e-3)


# --- round trip: inverse then direct ---------------------------------------

def test_inverse_direct_round_trip():
    p1 = [-71.0, 42.0]
    p2 = [-71.5, 42.5]
    # Request full precision so the returned bearing/distance are not coarsely
    # rounded; the inverse and direct solutions should then round-trip tightly.
    dist, init_bearing, _ = gb._vicenty_inverse(p1, p2, precision=12)
    p2_calc, _ = gb._vicenty_direct(p1, init_bearing, dist)
    assert p2_calc[0] == pytest.approx(p2[0], abs=1e-6)
    assert p2_calc[1] == pytest.approx(p2[1], abs=1e-6)


def test_direct_passes_z_through():
    p2, _ = gb._vicenty_direct([-71.0, 42.0, 123.0], 90, 1000)
    assert p2[2] == 123.0


# --- _determinant -----------------------------------------------------------

def test_determinant_counterclockwise_is_negative():
    assert gb._determinant([0, 0], [1, 0], [1, 1]) < 0


def test_determinant_clockwise_is_positive():
    assert gb._determinant([0, 0], [1, 0], [1, -1]) > 0


def test_determinant_collinear_is_zero():
    assert gb._determinant([0, 0], [1, 0], [2, 0]) == 0

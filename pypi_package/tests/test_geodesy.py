"""Unit tests for the public geodesy API (kmlb.distance/bearing/destination)."""

import pytest

import kmlb
from kmlb import _geo as gb
from kmlb import geodesy


# --- public API surface -----------------------------------------------------

def test_functions_are_exported():
    for name in ("distance", "bearing", "destination"):
        assert name in kmlb.__all__
        assert callable(getattr(kmlb, name))


# --- distance ---------------------------------------------------------------

def test_distance_zero():
    assert kmlb.distance([-71.0, 42.0], [-71.0, 42.0]) == 0.0


def test_distance_known_pair():
    # ~1 degree of latitude is roughly 111 km.
    assert kmlb.distance([0.0, 0.0], [0.0, 1.0]) == pytest.approx(110574.389, abs=1.0)


def test_distance_matches_inverse():
    p1, p2 = [-71.0, 42.0], [-71.5, 42.5]
    assert kmlb.distance(p1, p2) == gb._vicenty_inverse(p1, p2)[0]


def test_distance_ignores_altitude():
    flat = kmlb.distance([0.0, 0.0], [0.0, 1.0])
    with_z = kmlb.distance([0.0, 0.0, 500.0], [0.0, 1.0, 900.0])
    assert flat == with_z


# --- bearing ----------------------------------------------------------------

def test_bearing_due_north():
    assert kmlb.bearing([0.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0, abs=1e-3)


def test_bearing_due_east():
    assert kmlb.bearing([0.0, 0.0], [1.0, 0.0]) == pytest.approx(90.0, abs=1e-3)


def test_bearing_is_nonnegative():
    # A westward bearing should be normalized into the 0-360 range, not negative.
    b = kmlb.bearing([0.0, 0.0], [-1.0, 0.0])
    assert 0.0 <= b <= 360.0
    assert b == pytest.approx(270.0, abs=1e-3)


def test_bearing_matches_inverse():
    p1, p2 = [-71.0, 42.0], [-71.5, 42.5]
    assert kmlb.bearing(p1, p2) == gb._vicenty_inverse(p1, p2)[1]


# --- destination ------------------------------------------------------------

def test_destination_matches_direct():
    origin = [-71.0, 42.0]
    assert kmlb.destination(origin, 90, 1000) == gb._vicenty_direct(origin, 90, 1000)[0]


def test_destination_passes_z_through():
    coord = kmlb.destination([-71.0, 42.0, 123.0], 90, 1000)
    assert coord[2] == 123.0


def test_distance_destination_round_trip():
    # Travelling distance/bearing from p1 should land on p2.
    p1, p2 = [-71.0, 42.0], [-71.5, 42.5]
    dist = kmlb.distance(p1, p2, precision=12)
    brng = kmlb.bearing(p1, p2, precision=12)
    landed = kmlb.destination(p1, brng, dist)
    assert landed[0] == pytest.approx(p2[0], abs=1e-6)
    assert landed[1] == pytest.approx(p2[1], abs=1e-6)


def test_module_importable():
    # The submodule is reachable as kmlb.geodesy as well as via re-exports.
    assert geodesy.distance is kmlb.distance

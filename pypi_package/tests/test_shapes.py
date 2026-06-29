"""Unit tests for ``kmlb.shapes``."""

import pytest

import kmlb
from kmlb import shapes


# --- destination feeding shape builders ------------------------------------

def test_destination_2d_result_feeds_line_without_error():
    # destination() returns a 2D coord when the origin has no z; that result must
    # be usable directly as a line vertex (z defaults to 0). This is the radial
    # "spoke" pattern: project a point, then draw a line to it.
    start = [-71.053568, 42.359053]
    end = kmlb.destination(start, 33, 100)
    assert len(end) == 2  # no z carried through
    spoke = kmlb.line([start, end], "Spoke")
    coord_text = spoke.find("LineString").find("coordinates").text
    # both vertices rendered with a trailing ,0 altitude
    assert all(v.endswith(",0") for v in coord_text.split())


def test_wedge_returns_placemark_polygon():
    w = shapes.wedge([-71.0, 42.0, 0], azimuth=90, width=30, radius=1000)
    assert w.tag == "Placemark"
    assert w.find("Polygon") is not None
    assert w.find("name").text == "Wedge"


def test_wedge_vertex_count_tracks_steps():
    steps = 10
    w = shapes.wedge([-71.0, 42.0, 0], 90, 30, 1000, steps=steps)
    coord_text = w.find("Polygon").find("outerBoundaryIs").find("LinearRing").find("coordinates").text
    vertices = coord_text.split()
    # `steps` arc vertices plus the center repeated as first and last vertex.
    assert len(vertices) == steps + 2


def test_wedge_custom_name_and_kwargs():
    w = shapes.wedge([-71.0, 42.0, 0], 90, 30, 1000, name="Sector", hidden=True)
    assert w.find("name").text == "Sector"
    assert w.find("visibility").text == "0"

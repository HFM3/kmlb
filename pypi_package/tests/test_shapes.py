"""Unit tests for ``kmlb.shapes``."""

import math

import pytest

import kmlb
from kmlb import base, shapes


def _outer_vertices(wedge):
    """Return the wedge's outer-ring vertices as [lon, lat, z] float lists."""
    coord_text = (
        wedge.find("Polygon").find("outerBoundaryIs").find("LinearRing").find("coordinates").text
    )
    return [[float(v) for v in vertex.split(",")] for vertex in coord_text.split()]


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


# --- wedge tilt -------------------------------------------------------------

def test_wedge_untilted_stays_flat_and_clamped():
    # Default (tilt=0) keeps today's behavior: ground-clamped, every vertex at
    # the center's altitude.
    w = shapes.wedge([-71.0, 42.0, 5], 90, 30, 1000)
    assert w.find("Polygon").find("altitudeMode").text == "clampToGround"
    assert all(v[2] == 5 for v in _outer_vertices(w))


def test_wedge_tilt_auto_absolute_altitude_mode():
    w = shapes.wedge([-71.0, 42.0, 30], 90, 30, 1000, tilt=-6)
    assert w.find("Polygon").find("altitudeMode").text == "absolute"


def test_wedge_tilt_respects_explicit_z_mode():
    w = shapes.wedge([-71.0, 42.0, 30], 90, 30, 1000, tilt=-6, z_mode="RTG")
    assert w.find("Polygon").find("altitudeMode").text == "relativeToGround"


def test_wedge_tilt_apex_unmoved_and_arc_lifted():
    center_z = 30.0
    radius = 1000.0
    tilt = 20.0
    w = shapes.wedge([-71.0, 42.0, center_z], 90, 30, radius, tilt=tilt)
    verts = _outer_vertices(w)

    # First and last vertices are the apex (center) and never move.
    assert verts[0][2] == pytest.approx(center_z)
    assert verts[-1][2] == pytest.approx(center_z)

    # The middle arc vertex sits on the boresight and lifts by radius*sin(tilt).
    boresight_vertex = verts[1 + (len(verts) - 2) // 2]
    assert boresight_vertex[2] == pytest.approx(center_z + radius * math.sin(math.radians(tilt)), abs=1e-6)


def test_wedge_negative_tilt_lowers_arc():
    center_z = 100.0
    w = shapes.wedge([-71.0, 42.0, center_z], 90, 30, 1000, tilt=-90)
    arc = _outer_vertices(w)[1:-1]  # drop the two apex vertices
    assert all(v[2] < center_z for v in arc)


def test_wedge_tilt_straight_up_collapses_boresight_to_apex():
    # At tilt=90 the boresight vertex points straight up, so its horizontal
    # position collapses onto the apex/center.
    center = [-71.0, 42.0, 0.0]
    w = shapes.wedge(center, 90, 30, 1000, tilt=90)
    verts = _outer_vertices(w)
    boresight_vertex = verts[1 + (len(verts) - 2) // 2]
    assert boresight_vertex[0] == pytest.approx(center[0], abs=1e-4)
    assert boresight_vertex[1] == pytest.approx(center[1], abs=1e-4)


def test_wedge_tilt_preserves_vertex_count():
    steps = 12
    w = shapes.wedge([-71.0, 42.0, 30], 90, 30, 1000, tilt=15, steps=steps)
    assert len(_outer_vertices(w)) == steps + 2


def test_tilt_wedge_coord_reduces_to_flat_at_zero_tilt():
    center = [-71.0, 42.0, 7.0]
    flat = kmlb.destination(center, 33.0, 500.0)
    tilted = shapes._tilt_wedge_coord(center, 90.0, 33.0, 500.0, 0.0)
    assert tilted[0] == pytest.approx(flat[0])
    assert tilted[1] == pytest.approx(flat[1])
    assert tilted[2] == pytest.approx(center[2])


# --- fresnel_zone -----------------------------------------------------------

FZ_A = [-71.09, 42.36, 90.0]
FZ_B = [-71.02, 42.33, 70.0]


def test_fresnel_radius_zero_at_ends_and_peaks_midpath():
    d, lam = 1000.0, 0.3331
    assert shapes._fresnel_radius(1, lam, 0.0, d, d) == pytest.approx(0.0)
    assert shapes._fresnel_radius(1, lam, d, 0.0, d) == pytest.approx(0.0)
    assert shapes._fresnel_radius(1, lam, d / 2, d / 2, d) == pytest.approx(0.5 * math.sqrt(lam * d))


def test_fresnel_radius_scales_with_sqrt_zone():
    r1 = shapes._fresnel_radius(1, 0.3, 400, 600, 1000)
    r4 = shapes._fresnel_radius(4, 0.3, 400, 600, 1000)
    assert r4 == pytest.approx(2 * r1)


def test_fresnel_zone_returns_folder_with_path_tube_and_ring():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900)
    assert f.tag == "Folder"
    placemarks = f.findall("Placemark")
    assert len(placemarks) == 3
    tube = [p for p in placemarks if p.find("MultiGeometry") is not None][0]
    path = [p for p in placemarks if p.find("name").text.endswith("Link Path")][0]
    assert len(tube.find("MultiGeometry").findall("Polygon")) == 24 * 16  # (cross_rings-1) * ring_strips
    assert path.find("LineString").find("altitudeMode").text == "absolute"


def test_fresnel_zone_name_prefixes_children_and_folder():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900, name="North Link")
    assert f.find("name").text == "North Link"
    names = {p.find("name").text for p in f.findall("Placemark")}
    assert names == {"North Link - Link Path", "North Link - Fresnel Zone", "North Link - Center Ring"}


def test_fresnel_zone_center_ring_is_cyan_closed_hoop():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900, ring_strips=16)
    ring = [p for p in f.findall("Placemark") if p.find("name").text.endswith("Center Ring")][0]
    coords = ring.find("LineString/coordinates").text.split()
    assert len(coords) == 16 + 1  # ring_strips vertices plus the repeated closing vertex
    assert coords[0] == coords[-1]
    assert ring.find("Style/LineStyle/color").text == base._kml_color(*base._resolve_color("cyan"))
    assert ring.find("Style/LineStyle/width").text == "5.0"


def test_fresnel_zone_center_ring_can_be_disabled():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900, center_ring_color=None)
    names = {p.find("name").text for p in f.findall("Placemark")}
    assert names == {"RF Link - Link Path", "RF Link - Fresnel Zone"}


def test_fresnel_zone_bare_tube_when_path_and_ring_off():
    tube = shapes.fresnel_zone(FZ_A, FZ_B, 900, include_path=False, center_ring_color=None)
    assert tube.tag == "Placemark"
    assert tube.find("MultiGeometry") is not None
    assert tube.find("name").text == "RF Link - Fresnel Zone"


def test_fresnel_zone_panels_all_absolute():
    tube = shapes.fresnel_zone(FZ_A, FZ_B, 900, include_path=False, center_ring_color=None,
                               cross_rings=8, ring_strips=6)
    polys = tube.find("MultiGeometry").findall("Polygon")
    assert len(polys) == 7 * 6  # (cross_rings-1) * ring_strips
    assert all(p.find("altitudeMode").text == "absolute" for p in polys)


def test_fresnel_rings_midpoint_symmetric_about_los():
    lam = shapes._LIGHT_SPEED / (900 * 1e6)
    rings = shapes._fresnel_rings(FZ_A, FZ_B, lam, 1, 25, 16)
    d_total = kmlb.distance(FZ_A, FZ_B)
    r_max = 0.5 * math.sqrt(lam * d_total)
    los_alt = (FZ_A[2] + FZ_B[2]) / 2
    alts = [v[2] for v in rings[len(rings) // 2]]  # exact midpoint ring (odd ring count)
    assert max(alts) == pytest.approx(los_alt + r_max, abs=0.5)
    assert min(alts) == pytest.approx(los_alt - r_max, abs=0.5)


def test_fresnel_rings_ends_collapse_to_endpoints():
    lam = shapes._LIGHT_SPEED / (900 * 1e6)
    rings = shapes._fresnel_rings(FZ_A, FZ_B, lam, 1, 12, 8)  # 12 cross rings, 8 strips
    for v in rings[0]:
        assert v == pytest.approx(FZ_A, abs=1e-6)
    for v in rings[-1]:
        assert v == pytest.approx(FZ_B, abs=1e-6)


def test_fresnel_zone_rejects_coincident_points():
    with pytest.raises(ValueError):
        shapes.fresnel_zone(FZ_A, list(FZ_A), 900)


def test_fresnel_zone_colors_apply():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900, zone_color=("cyan", 40), path_color="#ff0000")
    tube = [p for p in f.findall("Placemark") if p.find("MultiGeometry") is not None][0]
    path = [p for p in f.findall("Placemark") if p.find("LineString") is not None][0]
    assert tube.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color(("cyan", 40)))
    assert path.find("Style/LineStyle/color").text == base._kml_color(*base._resolve_color("#ff0000"))


def test_fresnel_zone_folder_collapsed_by_default():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900)
    assert f.find("open").text == "0"  # collapsed
    assert shapes.fresnel_zone(FZ_A, FZ_B, 900, collapsed=False).find("open").text == "1"


def test_fresnel_zone_blurb_is_two_lines():
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900)
    for p in f.findall("Placemark"):
        assert p.find("snippet").text.count("\n") == 1  # exactly two lines


def test_fresnel_radius_physical_sanity():
    # 900 MHz over 1 km -> first-zone max radius ~9.1 m.
    lam = shapes._LIGHT_SPEED / (900 * 1e6)
    assert 0.5 * math.sqrt(lam * 1000.0) == pytest.approx(9.1, abs=0.3)


# --- cylinder ---------------------------------------------------------------

CYL_CENTER = [-71.06, 42.36, 100.0]


def _mg_polys(pm):
    return pm.find("MultiGeometry").findall("Polygon")


def test_cylinder_is_multigeometry_placemark():
    c = shapes.cylinder(CYL_CENTER, 300, 400)
    assert c.tag == "Placemark"
    assert c.find("name").text == "Cylinder"
    assert c.find("MultiGeometry") is not None


def test_cylinder_panel_count_with_and_without_cap():
    sides = 16
    assert len(_mg_polys(shapes.cylinder(CYL_CENTER, 300, 400, sides=sides))) == sides + 2
    assert len(_mg_polys(shapes.cylinder(CYL_CENTER, 300, 400, sides=sides, cap=False))) == sides


def test_cylinder_panels_absolute_altitude():
    c = shapes.cylinder(CYL_CENTER, 300, 400, z_mode="ABS")
    assert all(p.find("altitudeMode").text == "absolute" for p in _mg_polys(c))


def test_cylinder_spans_base_to_base_plus_height():
    base_z, height = 100.0, 400.0
    c = shapes.cylinder([-71.06, 42.36, base_z], 300, height, sides=12, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c)
          for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(base_z)
    assert max(zs) == pytest.approx(base_z + height)


def test_cylinder_radius_matches():
    radius = 300.0
    c = shapes.cylinder(CYL_CENTER, radius, 400, sides=24, cap=False)
    # first wall panel's first vertex is a bottom-ring point; check its ground
    # distance from the center equals the radius.
    v = _mg_polys(c)[0].find(".//coordinates").text.split()[0]
    lon, lat, _ = (float(x) for x in v.split(","))
    assert kmlb.distance(CYL_CENTER, [lon, lat]) == pytest.approx(radius, abs=1.0)


def test_cylinder_top_radius_makes_a_frustum():
    # bottom ring keeps 'radius', top ring uses 'top_radius'
    c = shapes.cylinder(CYL_CENTER, 300, 400, sides=24, top_radius=100)
    verts = [[float(x) for x in t.split(",")]
             for p in _mg_polys(c) for t in p.find(".//coordinates").text.split()]
    zmin, zmax = min(v[2] for v in verts), max(v[2] for v in verts)
    r_bot = max(kmlb.distance(CYL_CENTER, v[:2]) for v in verts if abs(v[2] - zmin) < 0.5)
    r_top = max(kmlb.distance(CYL_CENTER, v[:2]) for v in verts if abs(v[2] - zmax) < 0.5)
    assert r_bot == pytest.approx(300, abs=1.0)
    assert r_top == pytest.approx(100, abs=1.0)


def test_cylinder_rejects_negative_top_radius():
    with pytest.raises(ValueError):
        shapes.cylinder(CYL_CENTER, 300, 400, top_radius=-1)


def test_cylinder_color_default_and_override():
    c = shapes.cylinder(CYL_CENTER, 300, 400)
    fill = c.find("Style/PolyStyle/color").text
    assert fill == base._kml_color(*base._resolve_color(("#66ff33", 40)))
    outline = c.find("Style/LineStyle/color").text
    assert outline == base._kml_color("#66ff33", 100)
    c2 = shapes.cylinder(CYL_CENTER, 300, 400, color="cyan")
    assert c2.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color("cyan"))


def test_cylinder_hidden():
    assert shapes.cylinder(CYL_CENTER, 300, 400, hidden=True).find("visibility").text == "0"
    assert shapes.cylinder(CYL_CENTER, 300, 400).find("visibility").text == "1"


# --- cone -------------------------------------------------------------------

def test_cone_is_multigeometry_placemark():
    c = shapes.cone(CYL_CENTER, 300, 500)
    assert c.tag == "Placemark" and c.find("name").text == "Cone"
    assert c.find("MultiGeometry") is not None


def test_cone_panel_count_with_and_without_cap():
    sides = 20
    assert len(_mg_polys(shapes.cone(CYL_CENTER, 300, 500, sides=sides))) == sides + 1
    assert len(_mg_polys(shapes.cone(CYL_CENTER, 300, 500, sides=sides, cap=False))) == sides


def test_cone_apex_at_base_plus_height():
    base_z, height = 100.0, 500.0
    c = shapes.cone([-71.06, 42.36, base_z], 300, height, sides=12, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c)
          for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(base_z)          # base ring
    assert max(zs) == pytest.approx(base_z + height)  # apex


def test_cone_apex_is_over_center():
    c = shapes.cone(CYL_CENTER, 300, 500, sides=12, cap=False)
    # each wall triangle's 3rd vertex is the shared apex, above the center
    apex = _mg_polys(c)[0].find(".//coordinates").text.split()[2]
    lon, lat, _ = (float(x) for x in apex.split(","))
    assert kmlb.distance(CYL_CENTER, [lon, lat]) == pytest.approx(0.0, abs=1.0)


def test_cone_color_default():
    c = shapes.cone(CYL_CENTER, 300, 500)
    assert c.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color(("#3399ff", 40)))
    assert all(p.find("altitudeMode").text == "absolute" for p in _mg_polys(c))


# --- dome -------------------------------------------------------------------

def test_dome_is_multigeometry_placemark():
    d = shapes.dome(CYL_CENTER, 400)
    assert d.tag == "Placemark" and d.find("name").text == "Dome"
    assert d.find("MultiGeometry") is not None


def test_dome_panel_count_with_and_without_cap():
    sides, rings = 24, 6
    assert len(_mg_polys(shapes.dome(CYL_CENTER, 400, sides=sides, rings=rings))) == sides * rings + 1
    assert len(_mg_polys(shapes.dome(CYL_CENTER, 400, sides=sides, rings=rings, cap=False))) == sides * rings


def test_dome_spans_base_to_base_plus_radius():
    base_z, radius = 100.0, 400.0
    d = shapes.dome([-71.06, 42.36, base_z], radius, sides=12, rings=6, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(d)
          for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(base_z)             # base ring
    assert max(zs) == pytest.approx(base_z + radius)     # top point


def test_dome_color_default_and_absolute():
    d = shapes.dome(CYL_CENTER, 400)
    assert d.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color(("#ff9933", 40)))
    assert all(p.find("altitudeMode").text == "absolute" for p in _mg_polys(d))


# --- sphere -----------------------------------------------------------------

SPH_CENTER = [-71.06, 42.36, 500.0]


def test_sphere_is_multigeometry_placemark():
    sp = shapes.sphere(SPH_CENTER, 300)
    assert sp.tag == "Placemark" and sp.find("name").text == "Sphere"
    assert sp.find("MultiGeometry") is not None


def test_sphere_panel_count():
    sides, rings = 20, 10
    assert len(_mg_polys(shapes.sphere(SPH_CENTER, 300, sides=sides, rings=rings))) == sides * rings


def test_sphere_spans_center_plus_minus_radius():
    cz, radius = 500.0, 300.0
    sp = shapes.sphere([-71.06, 42.36, cz], radius, sides=12, rings=8)
    zs = [float(v.split(",")[2]) for p in _mg_polys(sp)
          for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(cz - radius)   # south pole
    assert max(zs) == pytest.approx(cz + radius)   # north pole


def test_sphere_color_default_and_absolute():
    sp = shapes.sphere(SPH_CENTER, 300)
    assert sp.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color(("#9933ff", 40)))
    assert all(p.find("altitudeMode").text == "absolute" for p in _mg_polys(sp))


# --- solid axis orientation -------------------------------------------------

def _all_verts(pm):
    return [[float(x) for x in v.split(",")]
            for p in _mg_polys(pm) for v in p.find(".//coordinates").text.split()]


def test_cylinder_horizontal_axis_displaces_top():
    center = [-71.06, 42.36, 100.0]
    height = 500.0
    c = shapes.cylinder(center, 100, height, azimuth=90, tilt=0, sides=24)
    top_cap = _mg_polys(c)[-1]  # walls, bottom cap, then top cap
    verts = [[float(x) for x in v.split(",")] for v in top_cap.find(".//coordinates").text.split()][:-1]
    clon = sum(v[0] for v in verts) / len(verts)
    clat = sum(v[1] for v in verts) / len(verts)
    cz = sum(v[2] for v in verts) / len(verts)
    assert kmlb.distance(center, [clon, clat]) == pytest.approx(height, abs=2.0)  # east by height
    assert kmlb.bearing(center, [clon, clat]) == pytest.approx(90, abs=1.0)       # due east
    assert cz == pytest.approx(100.0, abs=1.0)                                    # horizontal -> same alt


def test_cone_anchor_top_puts_apex_at_point():
    # Uniform anchoring: anchor='top' sits the apex at the point and the base
    # hangs back along the axis, the same direction the other solids move.
    center = [-71.06, 42.36, 300.0]
    height = 500.0
    c = shapes.cone(center, 200, height, anchor="top", sides=12, cap=False)
    tri = _mg_polys(c)[0].find(".//coordinates").text.split()
    apex = [float(x) for x in tri[2].split(",")]          # 3rd vertex = shared apex
    base = [float(x) for x in tri[0].split(",")]          # 1st vertex = base ring
    assert kmlb.distance(center, [apex[0], apex[1]]) == pytest.approx(0.0, abs=1.0)
    assert apex[2] == pytest.approx(300.0)                # apex at the point
    assert base[2] == pytest.approx(300.0 - height)       # base hangs back down the axis


def test_cone_anchor_matches_cylinder_direction():
    # The cone's anchor now moves it the same direction as a cylinder under a
    # downward axis (tilt=-90): 'base' at the point, body extending down.
    center = [-71.06, 42.36, 400.0]
    height = 300.0
    c = shapes.cone(center, 100, height, tilt=-90, anchor="base", sides=12, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c) for v in p.find(".//coordinates").text.split()]
    assert max(zs) == pytest.approx(400.0)               # base disc at the point
    assert min(zs) == pytest.approx(400.0 - height)      # apex below (axis points down)


def test_dome_orientation_preserves_panels_and_tilts_pole():
    center = [-71.06, 42.36, 100.0]
    radius = 400.0
    d = shapes.dome(center, radius, azimuth=90, tilt=0, sides=12, rings=6, cap=False)
    assert len(_mg_polys(d)) == 12 * 6
    # horizontal pole -> the farthest-east vertex sits ~radius east at ~center alt
    pole = max(_all_verts(d), key=lambda v: v[0])
    assert kmlb.distance(center, [pole[0], pole[1]]) == pytest.approx(radius, abs=5.0)
    assert pole[2] == pytest.approx(100.0, abs=5.0)


# --- solid anchor (base / center / top) -------------------------------------

def test_sphere_anchor_base_rests_on_point():
    cz, radius = 100.0, 300.0
    sp = shapes.sphere([-71.06, 42.36, cz], radius, anchor="base", sides=12, rings=8)
    zs = [float(v.split(",")[2]) for p in _mg_polys(sp) for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(cz)                 # bottom pole sits at the point
    assert max(zs) == pytest.approx(cz + 2 * radius)    # sphere extends up


def test_sphere_anchor_top_hangs_below_point():
    cz, radius = 500.0, 300.0
    sp = shapes.sphere([-71.06, 42.36, cz], radius, anchor="top", sides=12, rings=8)
    zs = [float(v.split(",")[2]) for p in _mg_polys(sp) for v in p.find(".//coordinates").text.split()]
    assert max(zs) == pytest.approx(cz)                 # top pole at the point
    assert min(zs) == pytest.approx(cz - 2 * radius)    # sphere hangs below


def test_sphere_anchor_center_is_default():
    cz, radius = 500.0, 300.0
    a = shapes.sphere([-71.06, 42.36, cz], radius)
    b = shapes.sphere([-71.06, 42.36, cz], radius, anchor="center")
    za = [v for p in _mg_polys(a) for v in p.find(".//coordinates").text.split()]
    zb = [v for p in _mg_polys(b) for v in p.find(".//coordinates").text.split()]
    assert za == zb


def test_cylinder_anchor_top_hangs():
    base_z, height = 300.0, 400.0
    c = shapes.cylinder([-71.06, 42.36, base_z], 100, height, anchor="top", sides=12, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c) for v in p.find(".//coordinates").text.split()]
    assert max(zs) == pytest.approx(base_z)             # top face at the point
    assert min(zs) == pytest.approx(base_z - height)    # body hangs below


def test_cone_anchor_center_straddles():
    base_z, height = 400.0, 500.0
    c = shapes.cone([-71.06, 42.36, base_z], 200, height, anchor="center", sides=12, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c) for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(base_z - height / 2)
    assert max(zs) == pytest.approx(base_z + height / 2)


def test_dome_anchor_top_puts_pole_at_center():
    base_z, radius = 200.0, 400.0
    d = shapes.dome([-71.06, 42.36, base_z], radius, anchor="top", sides=12, rings=6, cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(d) for v in p.find(".//coordinates").text.split()]
    assert max(zs) == pytest.approx(base_z)             # pole at the point
    assert min(zs) == pytest.approx(base_z - radius)    # rim hangs below


# --- 2D shapes -------------------------------------------------------------

def _ring_coords(boundary):
    """[lon, lat, z] vertices of a LinearRing under a boundary element."""
    text = boundary.find("LinearRing").find("coordinates").text
    return [[float(x) for x in v.split(",")] for v in text.split()]


def _linestring_coords(placemark):
    text = placemark.find("LineString").find("coordinates").text
    return [[float(x) for x in v.split(",")] for v in text.split()]


def test_circle_returns_polygon_of_radius():
    center = [-71.0655, 42.3543, 0]
    c = shapes.circle(center, 37.5, steps=48)
    assert c.tag == "Placemark"
    assert c.find("Polygon") is not None
    assert c.find("name").text == "Circle"
    verts = _outer_vertices(c)
    assert len(verts) == 49                     # 48 steps + closing vertex
    for v in verts:
        assert kmlb.distance(center, v) == pytest.approx(37.5, abs=0.5)


def test_ellipse_axes_match_semilengths():
    center = [-70.9645, 42.3603, 0]
    e = shapes.ellipse(center, 600, 330, orient=0, steps=64)
    assert e.find("Polygon") is not None
    dists = [kmlb.distance(center, v) for v in _outer_vertices(e)]
    assert max(dists) == pytest.approx(600, abs=2)
    assert min(dists) == pytest.approx(330, abs=2)


def test_rectangle_corners_measured_from_upper_left():
    corner = [-71.0217, 42.3407, 0]
    r = shapes.rectangle(corner, 1260, 185)      # default azimuth=90 (width runs east)
    verts = _outer_vertices(r)
    assert len(verts) == 5                       # 4 corners + closing vertex
    dists = sorted(kmlb.distance(corner, v) for v in verts[:-1])
    assert dists[0] == pytest.approx(0, abs=2)                     # the corner itself
    assert dists[1] == pytest.approx(185, abs=2)                  # height edge (south)
    assert dists[2] == pytest.approx(1260, abs=2)                 # width edge (east)
    assert dists[3] == pytest.approx(math.hypot(1260, 185), abs=2)  # diagonal


def test_rectangle_azimuth_is_first_edge_bearing():
    corner = [-71.0217, 42.3407, 0]
    # verts[0] is the corner; verts[1] is the far end of the first ('width') edge,
    # so its bearing from the corner must equal 'azimuth'.
    for az, length in [(90, 1000), (180, 800), (45, 600)]:
        r = shapes.rectangle(corner, length, 400, azimuth=az)
        verts = _outer_vertices(r)
        assert kmlb.bearing(corner, verts[1]) == pytest.approx(az, abs=0.5)
        assert kmlb.distance(corner, verts[1]) == pytest.approx(length, abs=2)


def test_rectangle_default_first_edge_runs_due_east():
    corner = [-71.0217, 42.3407, 0]
    verts = _outer_vertices(shapes.rectangle(corner, 500, 500))
    assert kmlb.bearing(corner, verts[1]) == pytest.approx(90, abs=0.5)  # width runs east


def test_ngon_vertex_count_and_radius():
    center = [-71.0111, 42.3382, 0]
    p = shapes.ngon(center, 100, 5)
    verts = _outer_vertices(p)
    assert len(verts) == 6                        # 5 sides + closing vertex
    for v in verts[:-1]:
        assert kmlb.distance(center, v) == pytest.approx(100, abs=1)


def test_ngon_requires_three_sides():
    with pytest.raises(ValueError):
        shapes.ngon([-71.0, 42.0, 0], 100, 2)


@pytest.mark.parametrize("call", [
    lambda: shapes.wedge([-71.0, 42.0, 0], 90, 30, 500, steps=1),
    lambda: shapes.circle([-71.0, 42.0, 0], 100, steps=2),
    lambda: shapes.ellipse([-71.0, 42.0, 0], 100, 50, steps=2),
    lambda: shapes.annulus([-71.0, 42.0, 0], 50, 100, steps=2),
    lambda: shapes.con_rings([-71.0, 42.0, 0], [100, 200], steps=2),
    lambda: shapes.fresnel_zone([-71.08, 42.35, 220], [-71.02, 42.39, 180], 5800, cross_rings=1),
    lambda: shapes.fresnel_zone([-71.08, 42.35, 220], [-71.02, 42.39, 180], 5800, ring_strips=2),
])
def test_builders_reject_too_few_vertices(call):
    # too-small count params raise a clear ValueError instead of crashing or
    # silently emitting a degenerate polygon.
    with pytest.raises(ValueError):
        call()


def test_annulus_has_outer_and_inner_ring():
    center = [-70.9795, 42.3658, 0]
    a = shapes.annulus(center, 160, 225)          # (inner, outer)
    poly = a.find("Polygon")
    outer = _ring_coords(poly.find("outerBoundaryIs"))
    inner = _ring_coords(poly.find("innerBoundaryIs"))
    assert kmlb.distance(center, outer[0]) == pytest.approx(225, abs=1)
    assert kmlb.distance(center, inner[0]) == pytest.approx(160, abs=1)


def test_annulus_rejects_inner_ge_outer():
    with pytest.raises(ValueError):
        shapes.annulus([-71.0, 42.0, 0], 100, 100)


def test_arc_returns_line_at_radius():
    center = [-70.9285, 42.3199, 0]
    a = shapes.arc(center, 3000, 60, 200, steps=32)
    assert a.find("LineString") is not None
    verts = _linestring_coords(a)
    assert len(verts) == 33                       # steps + 1 (open path)
    for v in verts:
        assert kmlb.distance(center, v) == pytest.approx(3000, abs=3)


def test_ribbon_keeps_even_width():
    path = [[-71.051781, 42.358581], [-71.051176, 42.356909], [-71.053736, 42.353987]]
    c = shapes.ribbon(path, 45)
    verts = _outer_vertices(c)
    assert len(verts) == 2 * len(path) + 1        # left + right + closing vertex
    # ring = left[0..2] + right[2..0] + left[0]; endpoints have no turn, so each
    # side sits a clean half-width from the path and the two are a full width apart.
    assert kmlb.distance(path[0], verts[0]) == pytest.approx(22.5, abs=0.5)
    assert kmlb.distance(path[0], verts[5]) == pytest.approx(22.5, abs=0.5)
    assert kmlb.distance(verts[0], verts[5]) == pytest.approx(45, abs=1)


def test_ribbon_per_point_width():
    # A width list tapers the ribbon: each vertex sits half its own width from the
    # path. A straight path keeps the miter factor at 1 so the offsets are exact.
    path = [[-71.05, 42.35], [-71.05, 42.36], [-71.05, 42.37]]
    c = shapes.ribbon(path, [20, 80, 20])
    verts = _outer_vertices(c)
    assert kmlb.distance(path[0], verts[0]) == pytest.approx(10, abs=0.5)    # 20 m end
    assert kmlb.distance(path[1], verts[1]) == pytest.approx(40, abs=0.5)    # 80 m middle


def test_ribbon_width_list_must_match_path():
    with pytest.raises(ValueError):
        shapes.ribbon([[-71.0, 42.0], [-71.0, 42.1]], [20, 30, 40])


def test_ribbon_requires_two_points():
    with pytest.raises(ValueError):
        shapes.ribbon([[-71.0, 42.0]], 45)


def test_con_rings_explicit_list():
    c = shapes.con_rings([-70.8901, 42.3279, 0], [500, 1000, 1500])
    assert c.tag == "Folder"
    lines = c.findall("Placemark")
    assert len(lines) == 3
    assert [p.find("name").text for p in lines] == ["500 m", "1000 m", "1500 m"]
    assert all(p.find("LineString") is not None for p in lines)


def test_con_rings_generator_form():
    c = shapes.con_rings([-70.8901, 42.3279, 0], start=1852, interval=1852, count=3)
    assert [p.find("name").text for p in c.findall("Placemark")] == ["1852 m", "3704 m", "5556 m"]


def test_con_rings_needs_a_form():
    with pytest.raises(ValueError):
        shapes.con_rings([-70.8901, 42.3279, 0])


def test_con_rings_default_name_and_attributes():
    c = shapes.con_rings([-70.8901, 42.3279, 0], [500, 1000])
    assert c.find("name").text == "Concentric Rings"
    # each ring carries a default attribute table with its ring number and radius
    descs = [p.find("description").text for p in c.findall("Placemark")]
    assert all(d for d in descs)
    assert "Ring" in descs[0] and "500" in descs[0]
    assert "Ring" in descs[1] and "1000" in descs[1]


# --- fishnet ---------------------------------------------------------------

def test_fishnet_cell_count():
    g = shapes.fishnet([-71.0488, 42.3433, 0], 20, 3, 4)
    assert g.tag == "Folder"
    cells = g.findall("Placemark")
    assert len(cells) == 12                        # cols * rows
    assert all(p.find("Polygon") is not None for p in cells)
    assert len(_outer_vertices(cells[0])) == 5     # square: 4 corners + close


def test_fishnet_first_cell_touches_corner():
    corner = [-71.0488, 42.3433, 0]
    g = shapes.fishnet(corner, 20, 3, 4)
    verts = _outer_vertices(g.findall("Placemark")[0])
    assert kmlb.distance(corner, verts[0]) == pytest.approx(0.0, abs=0.5)   # upper-left


def test_fishnet_rectangular_cell_dim():
    corner = [-71.0488, 42.3433, 0]
    g = shapes.fishnet(corner, [60, 20], 1, 1)     # 60 east-west, 20 north-south
    verts = _outer_vertices(g.findall("Placemark")[0])
    assert kmlb.distance(corner, verts[1]) == pytest.approx(60, abs=0.5)    # east edge
    assert kmlb.distance(corner, verts[3]) == pytest.approx(20, abs=0.5)    # south edge


def test_fishnet_azimuth_is_first_edge_bearing():
    corner = [-71.05, 42.36, 0]
    # azimuth is the compass bearing of the top (column) edge from the corner;
    # verts[1] is that edge's far end. Increasing azimuth turns the grid clockwise.
    for az in (90, 180, 45):
        g = shapes.fishnet(corner, 50, 1, 1, azimuth=az)
        verts = _outer_vertices(g.findall("Placemark")[0])
        assert kmlb.bearing(corner, verts[1]) == pytest.approx(az, abs=1)


def test_fishnet_ids_name_and_attribute_cells():
    g = shapes.fishnet([-71.05, 42.36, 0], 20, 2, 1, ids=["A", "B"])
    cells = g.findall("Placemark")
    assert [p.find("name").text for p in cells] == ["A", "B"]
    first = cells[0]
    data = {d.get("name"): d.find("value").text for d in first.find("ExtendedData").findall("Data")}
    assert data["ID"] == "A" and data["Row"] == "0" and data["Column"] == "0"


def test_fishnet_default_cell_names():
    g = shapes.fishnet([-71.05, 42.36, 0], 20, 2, 2)
    assert g.findall("Placemark")[0].find("name").text == "r0c0"


def test_fishnet_rejects_zero_dims():
    with pytest.raises(ValueError):
        shapes.fishnet([-71.0, 42.0, 0], 20, 0, 3)


def test_fishnet_rejects_mismatched_ids():
    with pytest.raises(ValueError):
        shapes.fishnet([-71.0, 42.0, 0], 20, 3, 3, ids=["only", "two"])


# --- hex_grid --------------------------------------------------------------

def test_hex_grid_cell_count():
    g = shapes.hex_grid([-71.0488, 42.3433, 0], 30, 2, 2)
    cells = g.findall("Placemark")
    assert len(cells) == 4
    assert len(_outer_vertices(cells[0])) == 7     # hexagon: 6 corners + close


def _shares_vertex(cell_a, cell_b, tol=0.05):
    va = _outer_vertices(cell_a)
    vb = _outer_vertices(cell_b)
    return any(kmlb.distance(a, b) < tol for a in va for b in vb)


def test_hex_grid_stays_tessellated_when_rotated():
    # Neighbouring hexes share a vertex at any azimuth (the old grid lost this).
    corner = [-71.05, 42.36, 0]
    for az in (0, 30, 45):
        g = shapes.hex_grid(corner, 40, 2, 1, azimuth=az)
        cells = g.findall("Placemark")
        assert _shares_vertex(cells[0], cells[1]), f"lost tessellation at az={az}"


def test_hex_grid_rejects_zero_dims():
    with pytest.raises(ValueError):
        shapes.hex_grid([-71.0, 42.0, 0], 20, 3, 0)


# --- hex_field -------------------------------------------------------------

def test_hex_field_cell_count():
    # A filled hexagon of N rings holds 1 + 3*N*(N+1) cells.
    for rings, expect in [(1, 7), (2, 19), (3, 37)]:
        g = shapes.hex_field([-71.05, 42.36, 0], 30, rings)
        cells = g.findall("Placemark")
        assert len(cells) == expect
        assert len(_outer_vertices(cells[0])) == 7   # hexagon: 6 corners + close


def test_hex_field_center_cell_is_number_one_on_center():
    center = [-71.05, 42.36, 0]
    g = shapes.hex_field(center, 40, 2)
    cells = g.findall("Placemark")
    assert cells[0].find("name").text == "1"          # first cell is the center
    verts = _outer_vertices(cells[0])[:-1]
    cx = sum(v[0] for v in verts) / 6
    cy = sum(v[1] for v in verts) / 6
    assert kmlb.distance(center, [cx, cy]) == pytest.approx(0.0, abs=0.5)


def test_hex_field_auto_ids_number_1_to_n_outward():
    g = shapes.hex_field([-71.05, 42.36, 0], 30, 2)
    names = [p.find("name").text for p in g.findall("Placemark")]
    assert names == [str(i) for i in range(1, 20)]    # 1..19 in cell order


def test_hex_field_list_ids_label_cells_in_order():
    labels = [f"c{i}" for i in range(7)]              # rings=1 -> 7 cells
    g = shapes.hex_field([-71.05, 42.36, 0], 30, 1, ids=labels)
    cells = g.findall("Placemark")
    assert [p.find("name").text for p in cells] == labels
    # the center cell (first) reports ring 0 in its attribute table
    data = {d.get("name"): d.find("value").text for d in cells[0].find("ExtendedData").findall("Data")}
    assert data["ID"] == "c0" and data["Ring"] == "0"


def test_hex_field_rejects_wrong_length_ids():
    with pytest.raises(ValueError):
        shapes.hex_field([-71.0, 42.0, 0], 20, 1, ids=["too", "few"])


def test_hex_field_rejects_zero_rings():
    with pytest.raises(ValueError):
        shapes.hex_field([-71.0, 42.0, 0], 20, 0)


def test_grid_labels_add_a_labels_folder_of_centroid_points():
    # default: no subfolders, cells sit directly in the grid folder
    plain = shapes.fishnet([-71.05, 42.36, 0], 20, 3, 2)
    assert plain.find("Folder") is None                       # no nested folder
    assert len(plain.findall("Placemark")) == 6
    # labels=True: cells and labels each in their own subfolder
    g = shapes.fishnet([-71.05, 42.36, 0], 20, 3, 2, labels=True)
    subs = {f.find("name").text: f for f in g.findall("Folder")}
    assert set(subs) == {"Cells", "Labels"}
    assert len(subs["Cells"].findall("Placemark")) == 6       # the polygon cells
    lf = subs["Labels"]
    pts = lf.findall("Placemark")
    assert len(pts) == 6                                       # one label per cell
    assert all(p.find("Point") is not None for p in pts)      # points, not polygons
    assert lf.find("Style") is not None                       # shared label style present
    names = {p.find("name").text for p in pts}
    assert "r0c0" in names


def test_hex_field_labels_named_by_cell_number():
    g = shapes.hex_field([-71.05, 42.36, 0], 30, 1, labels=True)
    lf = [f for f in g.findall("Folder") if f.find("name").text == "Labels"][0]
    names = [p.find("name").text for p in lf.findall("Placemark")]
    assert names == [str(i) for i in range(1, 8)]             # 7 cells, labelled 1..7


def test_hex_field_stays_tessellated_when_rotated():
    center = [-71.05, 42.36, 0]
    for az in (0, 90, 137):
        cells = shapes.hex_field(center, 40, 1, azimuth=az).findall("Placemark")
        # cell 1 is the center, cell 2 is a first-ring neighbour: they share an edge
        assert _shares_vertex(cells[0], cells[1]), f"lost tessellation at az={az}"


def test_hex_grid_rejects_mismatched_nested_ids():
    with pytest.raises(ValueError):
        shapes.hex_grid([-71.0, 42.0, 0], 20, 2, 2, ids=[["a", "b"]])   # 1x2, needs 2x2


def test_hex_grid_corner_is_top_left():
    # Corner anchoring matches fishnet: the first hex's bounds start at the corner,
    # so nothing sits north or west of it.
    corner = [-71.05, 42.36, 0]
    verts = _outer_vertices(shapes.hex_grid(corner, 40, 2, 2).findall("Placemark")[0])
    assert not any(v[1] > corner[1] + 1e-9 for v in verts)   # nothing north of corner
    assert not any(v[0] < corner[0] - 1e-9 for v in verts)   # nothing west of corner


# --- 2D extrude + string coords --------------------------------------------

def test_circle_extrude_flows_through():
    c = shapes.circle([-71.0, 42.0, 50], 100, extrude=True, z_mode="ABS")
    assert c.find("Polygon/extrude").text == "1"


def test_shape_accepts_string_coordinates():
    center = ["-71.0", "42.0", "0"]        # e.g. a CSV row
    c = shapes.circle(center, 100)
    for v in _outer_vertices(c):
        assert kmlb.distance([-71.0, 42.0], v) == pytest.approx(100, abs=1)


def test_shape_accepts_string_scalar_dimensions():
    # radius/height/counts read from a CSV cell (strings) are coerced, not rejected.
    c = shapes.circle([-71.0, 42.0, 0], "100", steps="24")
    assert len(_outer_vertices(c)) == 25
    for v in _outer_vertices(c):
        assert kmlb.distance([-71.0, 42.0], v) == pytest.approx(100, abs=1)
    cyl = shapes.cylinder(["-71.0", "42.0", "100"], "50", "200")
    assert cyl.find("MultiGeometry") is not None
    a = shapes.annulus([-71.0, 42.0, 0], "160", "260")
    assert a.find("Polygon") is not None
    cube = shapes.cube([-71.0, 42.0, 0], "40")           # scalar string size
    assert len(_mg_polys(cube)) == 6


# --- 3D solid: style_to_use / cam / headers-attrs ---------------------------

def test_cylinder_style_to_use_overrides_inline_color():
    c = shapes.cylinder(CYL_CENTER, 100, 200, style_to_use="myStyle")
    assert c.find("styleUrl").text == "#myStyle"
    assert c.find("Style") is None                 # inline style suppressed


def test_cylinder_cam_appended():
    cam = kmlb.camera([-71.06, 42.36, 500], 90, 45)
    c = shapes.cylinder(CYL_CENTER, 100, 200, cam=cam)
    assert c.find("Camera") is not None


def test_solid_headers_attrs_override():
    c = shapes.cylinder(CYL_CENTER, 100, 200, headers=["Callsign"], attrs=["ABC"])
    assert "<b>Callsign</b>: ABC" in c.find("description").text


# --- cube ------------------------------------------------------------------

def test_cube_panel_count_with_and_without_cap():
    assert len(_mg_polys(shapes.cube(CYL_CENTER, 100))) == 6          # 4 walls + 2 caps
    assert len(_mg_polys(shapes.cube(CYL_CENTER, 100, cap=False))) == 4


def test_cube_box_size_spans():
    base_z = 100.0
    c = shapes.cube([-71.06, 42.36, base_z], [200, 120, 300], cap=False)
    zs = [float(v.split(",")[2]) for p in _mg_polys(c) for v in p.find(".//coordinates").text.split()]
    assert min(zs) == pytest.approx(base_z)
    assert max(zs) == pytest.approx(base_z + 300)


# --- pyramid ---------------------------------------------------------------

def test_pyramid_panel_count():
    sides = 4
    assert len(_mg_polys(shapes.pyramid(CYL_CENTER, 150, 300, sides))) == sides + 1     # faces + cap
    assert len(_mg_polys(shapes.pyramid(CYL_CENTER, 150, 300, sides, cap=False))) == sides


def test_pyramid_apex_over_center():
    center = [-71.06, 42.36, 100.0]
    p = shapes.pyramid(center, 150, 300, 4, cap=False)
    apex = _mg_polys(p)[0].find(".//coordinates").text.split()[2]   # shared 3rd vertex
    lon, lat, z = (float(x) for x in apex.split(","))
    assert kmlb.distance(center, [lon, lat]) == pytest.approx(0.0, abs=1.0)
    assert z == pytest.approx(100.0 + 300)


def test_pyramid_requires_three_sides():
    with pytest.raises(ValueError):
        shapes.pyramid(CYL_CENTER, 150, 300, 2)


def test_pyramid_default_color_keyed_by_edge_count():
    # An unstyled pyramid colors by base edge count from PYRAMID_PALETTE and cycles.
    palette = shapes.PYRAMID_PALETTE
    for sides in (3, 4, 5, 6, 7):
        p = shapes.pyramid(CYL_CENTER, 150, 300, sides)
        expected = base._kml_color(*base._resolve_color(palette[(sides - 3) % len(palette)]))
        assert p.find("Style/PolyStyle/color").text == expected
    # different edge counts within one palette cycle -> different colors
    tri = shapes.pyramid(CYL_CENTER, 150, 300, 3).find("Style/PolyStyle/color").text
    sq = shapes.pyramid(CYL_CENTER, 150, 300, 4).find("Style/PolyStyle/color").text
    assert tri != sq


def test_pyramid_explicit_color_overrides_palette():
    p = shapes.pyramid(CYL_CENTER, 150, 300, 4, color="white")
    assert p.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color("white"))


# --- soccer ball -----------------------------------------------------------

def test_soccer_ball_is_folder_of_pentagons_and_hexagons():
    b = shapes.soccer_ball([-71.06, 42.36, 500], 150)
    assert b.tag == "Folder"
    placemarks = b.findall("Placemark")
    assert len(placemarks) == 2
    counts = sorted(len(p.find("MultiGeometry").findall("Polygon")) for p in placemarks)
    assert counts == [12, 20]           # 12 pentagons, 20 hexagons


def test_soccer_ball_two_tone_colors():
    b = shapes.soccer_ball([-71.06, 42.36, 500], 150, colors=("red", "white"))
    pent = [p for p in b.findall("Placemark") if p.find("name").text.endswith("Pentagons")][0]
    hexa = [p for p in b.findall("Placemark") if p.find("name").text.endswith("Hexagons")][0]
    assert pent.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color("red"))
    assert hexa.find("Style/PolyStyle/color").text == base._kml_color(*base._resolve_color("white"))


def test_soccer_ball_radius():
    center = [-71.06, 42.36, 500.0]
    radius = 150.0
    b = shapes.soccer_ball(center, radius, anchor="center")
    verts = [[float(x) for x in v.split(",")]
             for p in b.findall("Placemark") for poly in p.find("MultiGeometry").findall("Polygon")
             for v in poly.find(".//coordinates").text.split()]
    # every face vertex sits ~radius from the center in 3D (horizontal + vertical).
    for v in verts:
        horiz = kmlb.distance(center, [v[0], v[1]])
        r3d = math.hypot(horiz, v[2] - center[2])
        assert r3d == pytest.approx(radius, abs=2.0)


def test_soccer_ball_single_color_both_faces():
    # A single color, or a single (color, opacity) pair, colors both face types.
    for cols in ["red", ("red", 50)]:
        b = shapes.soccer_ball([-71.06, 42.36, 500], 100, colors=cols)
        pent = [p for p in b.findall("Placemark") if p.find("name").text.endswith("Pentagons")][0]
        hexa = [p for p in b.findall("Placemark") if p.find("name").text.endswith("Hexagons")][0]
        assert pent.find("Style/PolyStyle/color").text == hexa.find("Style/PolyStyle/color").text


def test_soccer_ball_rejects_bad_colors():
    with pytest.raises(ValueError):
        shapes.soccer_ball([-71.06, 42.36, 500], 100, colors=("red",))


def test_fresnel_zone_cam_attaches_to_folder_and_bare_tube():
    cam = kmlb.camera([-71.08, 42.35, 300], 90, 60)
    f = shapes.fresnel_zone(FZ_A, FZ_B, 900, cam=cam)
    assert any(c.tag == "Camera" for c in f)                       # folder gets the view
    tube = shapes.fresnel_zone(FZ_A, FZ_B, 900, include_path=False,
                               center_ring_color=None, cam=cam)
    assert tube.tag == "Placemark" and any(c.tag == "Camera" for c in tube)

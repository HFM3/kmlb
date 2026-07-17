"""Unit tests for the pure builders in ``kmlb.base``."""

import xml.etree.ElementTree as ET

import pytest

import kmlb
from kmlb import base


# --- _altitude_modes --------------------------------------------------------

@pytest.mark.parametrize("abbr,expected", [
    ("CTG", "clampToGround"),
    ("RTG", "relativeToGround"),
    ("ABS", "absolute"),
    ("CSF", "clampToSeaFloor"),
    ("RSF", "relativeToSeaFloor"),
    ("ctg", "clampToGround"),   # case-insensitive
    ("abs", "absolute"),
    ("csf", "clampToSeaFloor"),
])
def test_altitude_modes_known(abbr, expected):
    assert base._altitude_modes(abbr) == expected


def test_altitude_modes_unknown_falls_back():
    assert base._altitude_modes("nope") == "clampToGround"


def test_altitude_modes_default():
    assert base._altitude_modes() == "clampToGround"


# --- _set_altitude_mode (standard vs gx: sea-floor element) -----------------

@pytest.mark.parametrize("abbr,full", [
    ("CTG", "clampToGround"),
    ("ABS", "absolute"),
])
def test_set_altitude_mode_standard_uses_plain_tag(abbr, full):
    parent = ET.Element("Point")
    el = base._set_altitude_mode(parent, abbr)
    assert el.tag == "altitudeMode"
    assert el.text == full
    assert parent.find("altitudeMode") is el


@pytest.mark.parametrize("abbr,full", [
    ("CSF", "clampToSeaFloor"),
    ("RSF", "relativeToSeaFloor"),
])
def test_set_altitude_mode_seafloor_uses_gx_tag(abbr, full):
    parent = ET.Element("Point")
    el = base._set_altitude_mode(parent, abbr)
    assert el.tag == "gx:altitudeMode"
    assert el.text == full


def test_point_seafloor_emits_gx_altitude_mode():
    pm = base.point([-71.0, 42.3, -120], "Dive site", z_mode="CSF")
    # The tag is the literal string "gx:altitudeMode"; find() would parse the
    # colon as a namespace prefix, so inspect the children directly.
    tags = {child.tag: child.text for child in pm.find("Point")}
    assert tags.get("gx:altitudeMode") == "clampToSeaFloor"
    assert "altitudeMode" not in tags


def test_kml_root_declares_gx_namespace():
    pm = base.point([0, 0, -50], "Wreck", z_mode="RSF")
    doc = base.kml("Survey", [pm])
    assert 'xmlns:gx="http://www.google.com/kml/ext/2.2"' in doc
    assert "<gx:altitudeMode>relativeToSeaFloor</gx:altitudeMode>" in doc


# --- _kml_color -------------------------------------------------------------

def test_kml_color_full_opacity():
    # '#a2d402' -> ABGR with alpha ff
    assert base._kml_color("#a2d402", 100) == "ff02d4a2"


def test_kml_color_zero_opacity():
    assert base._kml_color("#a2d402", 0) == "0002d4a2"


@pytest.mark.parametrize("bad", [-1, 101, 200])
def test_kml_color_opacity_out_of_range(bad):
    with pytest.raises(ValueError):
        base._kml_color("#a2d402", bad)


# --- look_at ---------------------------------------------------------------

def test_look_at_builds_lookat():
    cam = base.look_at([-71.0, 42.3, 0], distance=500, azimuth=90, tilt=45)
    assert cam.tag == "LookAt"
    assert cam.find("longitude").text == "-71.0"
    assert cam.find("range").text == "500"
    # default z_mode is ABS -> absolute
    assert cam.find("altitudeMode").text == "absolute"


# --- camera ----------------------------------------------------------------

def test_camera_builds_camera():
    cam = base.camera([-71.0, 42.3, 5], heading=120, tilt=95)
    assert cam.tag == "Camera"
    assert cam.find("longitude").text == "-71.0"
    assert cam.find("latitude").text == "42.3"
    assert cam.find("altitude").text == "5"
    assert cam.find("heading").text == "120"
    assert cam.find("tilt").text == "95"
    assert cam.find("roll").text == "0.0"
    # default z_mode is ABS -> absolute
    assert cam.find("altitudeMode").text == "absolute"


def test_camera_defaults_no_viewer_options_or_fovy():
    cam = base.camera([-71.0, 42.3], heading=0, tilt=90)
    tags = {child.tag for child in cam}
    assert "gx:ViewerOptions" not in tags
    assert "gx:fovy" not in tags


def test_camera_two_element_coords_default_altitude():
    cam = base.camera([-71.0, 42.3], heading=0, tilt=90)
    assert cam.find("altitude").text == "0"


def test_camera_streetview_emits_option_without_enabled_attr():
    cam = base.camera([-71.0, 42.3], heading=0, tilt=90, streetview=True)
    # gx: tags carry a literal colon; find() would treat it as a namespace, so
    # walk the children directly.
    viewer = [c for c in cam if c.tag == "gx:ViewerOptions"][0]
    option = [c for c in viewer if c.tag == "gx:option"][0]
    assert option.get("name") == "streetview"
    assert option.get("enabled") is None


def test_camera_pano_id_forces_streetview_and_emits_pano_id():
    cam = base.camera([-71.0, 42.3], heading=0, tilt=90, pano_id="ABC123")
    viewer = [c for c in cam if c.tag == "gx:ViewerOptions"][0]
    tags = {c.tag: c.text for c in viewer}
    assert tags.get("gx:streetViewPanoId") == "ABC123"
    # the streetview option is present even though streetview was not passed
    option = [c for c in viewer if c.tag == "gx:option"][0]
    assert option.get("name") == "streetview"


def test_camera_date_and_fov_emitted_when_given():
    cam = base.camera([-71.0, 42.3], heading=0, tilt=90, streetview=True,
                      date="2025-08", fov=70)
    viewer = [c for c in cam if c.tag == "gx:ViewerOptions"][0]
    viewer_tags = {c.tag: c.text for c in viewer}
    assert viewer_tags.get("gx:streetViewDate") == "2025-08"
    cam_tags = {c.tag: c.text for c in cam}
    assert cam_tags.get("gx:fovy") == "70"


def test_camera_attaches_as_default_view():
    view = base.camera([-71.0, 42.3], heading=0, tilt=90)
    pm = base.point([-71.0, 42.3], "P", cam=view)
    assert list(pm)[-1].tag == "Camera"


# --- _parse_street_view_url -------------------------------------------------

SAMPLE_SV_URL = (
    "https://www.google.com/maps/@42.3544682,-71.0510368,3a,75y,121.94h,94.79t/"
    "data=!3m7!1e1!3m5!1sLy4z4nJtSJLvtopnW3Zxhg!2e0!6shttps:%2F%2Fexample"
    "%3Fpanoid%3DLy4z4nJtSJLvtopnW3Zxhg%26yaw%3D121.9!7i16384!8i8192?entry=ttu"
)


def test_parse_street_view_url_extracts_all_parts():
    parts = base._parse_street_view_url(SAMPLE_SV_URL)
    assert parts["lat"] == 42.3544682
    assert parts["lon"] == -71.0510368
    assert parts["heading"] == 121.94
    assert parts["tilt"] == 94.79
    assert parts["fov"] == 75.0
    assert parts["pano_id"] == "Ly4z4nJtSJLvtopnW3Zxhg"


def test_parse_street_view_url_pano_id_fallback():
    # No '!1s' token; the pano id must come from the embedded 'panoid=' value.
    url = "https://www.google.com/maps/@42.35,-71.05,3a,75y,10h,90t/data=!6spanoid=XYZ789!7i16384"
    assert base._parse_street_view_url(url)["pano_id"] == "XYZ789"


def test_parse_street_view_url_rejects_non_street_view():
    with pytest.raises(ValueError):
        base._parse_street_view_url("https://www.google.com/maps/place/Boston")


# --- street_view ------------------------------------------------------------

def test_street_view_builds_placemark_with_camera():
    pm = base.street_view(SAMPLE_SV_URL, "Site")
    assert pm.tag == "Placemark"
    assert pm.find("name").text == "Site"
    assert pm.find("Point").find("coordinates").text == "-71.0510368,42.3544682,0"
    cam = pm.find("Camera")
    assert cam is not None
    viewer = [c for c in cam if c.tag == "gx:ViewerOptions"][0]
    viewer_tags = {c.tag: c.text for c in viewer}
    assert viewer_tags.get("gx:streetViewPanoId") == "Ly4z4nJtSJLvtopnW3Zxhg"
    option = [c for c in viewer if c.tag == "gx:option"][0]
    assert option.get("name") == "streetview"


def test_street_view_maps_url_angle():
    pm = base.street_view(SAMPLE_SV_URL, "Site")
    cam = pm.find("Camera")
    assert cam.find("heading").text == "121.94"
    assert cam.find("tilt").text == "94.79"
    assert {c.tag: c.text for c in cam}.get("gx:fovy") == "75.0"


def test_street_view_overrides_win_over_url():
    pm = base.street_view(SAMPLE_SV_URL, "Site", heading=10, tilt=80, zoom=40,
                          roll=5, altitude=12)
    cam = pm.find("Camera")
    assert cam.find("heading").text == "10"
    assert cam.find("tilt").text == "80"
    assert cam.find("roll").text == "5"
    assert cam.find("altitude").text == "12"
    assert {c.tag: c.text for c in cam}.get("gx:fovy") == "40"


def test_street_view_date_optional():
    with_date = base.street_view(SAMPLE_SV_URL, "Site", date="2025-08")
    viewer = [c for c in with_date.find("Camera") if c.tag == "gx:ViewerOptions"][0]
    assert any(c.tag == "gx:streetViewDate" for c in viewer)

    without_date = base.street_view(SAMPLE_SV_URL, "Site")
    viewer = [c for c in without_date.find("Camera") if c.tag == "gx:ViewerOptions"][0]
    assert not any(c.tag == "gx:streetViewDate" for c in viewer)


# --- point -----------------------------------------------------------------

def test_point_basic():
    pm = base.point([-71.0, 42.3, 0], "Marker")
    assert pm.tag == "Placemark"
    assert pm.find("name").text == "Marker"
    assert pm.find("visibility").text == "1"
    pt = pm.find("Point")
    assert pt.find("coordinates").text == "-71.0,42.3,0"
    assert pt.find("altitudeMode").text == "clampToGround"


def test_point_hidden_sets_visibility_zero():
    pm = base.point([0, 0, 0], "Hidden", hidden=True)
    assert pm.find("visibility").text == "0"


def test_point_attributes_populate_extended_data():
    pm = base.point([0, 0, 0], "P", headers=["A", "B"], attrs=[1, 2])
    data = pm.find("ExtendedData").findall("Data")
    assert [d.get("name") for d in data] == ["A", "B"]
    assert [d.find("value").text for d in data] == ["1", "2"]
    assert "<b>A</b>: 1<br>" in pm.find("description").text


def test_point_style_url_attached():
    pm = base.point([0, 0, 0], "P", style_to_use="myStyle")
    assert pm.find("styleUrl").text == "#myStyle"


def test_point_camera_appended():
    cam = base.look_at([0, 0, 0], 100, 0, 0)
    pm = base.point([0, 0, 0], "P", cam=cam)
    assert pm.find("LookAt") is not None


# --- search_poi ------------------------------------------------------------

def test_search_poi_uses_address_and_defaults_name():
    pm = base.search_poi("1600 Amphitheatre Pkwy")
    assert pm.find("address").text == "1600 Amphitheatre Pkwy"
    assert pm.find("name").text == "1600 Amphitheatre Pkwy"
    # No fixed coordinates: Google Earth geocodes the address.
    assert pm.find("Point") is None


def test_search_poi_custom_description_and_snippet():
    pm = base.search_poi(
        "User Address", hidden=True, name="Label",
        desc="Balloon text", blurb="Short summary",
    )
    assert pm.find("name").text == "Label"
    assert pm.find("visibility").text == "0"
    assert pm.find("address").text == "User Address"
    assert pm.find("snippet").text == "Short summary"
    assert pm.find("description").text == "Balloon text"


def test_search_poi_no_snippet_by_default():
    pm = base.search_poi("Somewhere")
    assert pm.find("snippet") is None


def test_search_poi_description_sits_above_attribute_table():
    pm = base.search_poi("X", headers=["A"], attrs=[1], desc="explicit")
    descriptions = pm.findall("description")
    assert len(descriptions) == 1            # never two <description> elements
    # Blurb above the auto-built table, separated by a line break.
    assert descriptions[0].text == "explicit<br><b>A</b>: 1<br>"
    # Attributes still populate ExtendedData.
    assert pm.find("ExtendedData").find("Data").get("name") == "A"


def test_search_poi_description_falls_back_to_attributes():
    pm = base.search_poi("X", headers=["Park"], attrs=["Greenway"])
    assert pm.find("description").text == "<b>Park</b>: Greenway<br>"


def test_search_poi_children_in_kml_schema_order():
    pm = base.search_poi("X", name="N", desc="D", blurb="S", style_to_use="st")
    tags = [child.tag for child in list(pm)]
    # KML 2.2 AbstractFeatureType sequence for the elements search_poi emits.
    assert tags == ["name", "visibility", "address", "snippet", "description",
                    "styleUrl", "ExtendedData"]


# --- line ------------------------------------------------------------------

def test_line_coordinates_and_flags():
    coords = [[-71.0, 42.0, 0], [-71.1, 42.1, 0]]
    ln = base.line(coords, "Path")
    ls = ln.find("LineString")
    assert ls.find("tessellate").text == "1"   # follow_terrain default True
    assert ls.find("extrude").text == "0"       # extrude default False
    assert ls.find("coordinates").text.strip() == "-71.0,42.0,0 -71.1,42.1,0"


def test_line_style_url_prefixed_with_hash():
    ln = base.line([[0, 0, 0], [1, 1, 0]], "L", style_to_use="ls")
    assert ln.find("styleUrl").text == "#ls"


def test_line_flag_inversion():
    ln = base.line([[0, 0, 0], [1, 1, 0]], "L", follow_terrain=False, extrude=True)
    ls = ln.find("LineString")
    assert ls.find("tessellate").text == "0"
    assert ls.find("extrude").text == "1"


# --- polygon ---------------------------------------------------------------

def test_polygon_outer_ring():
    ring = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]
    pg = base.polygon([ring], "Poly")
    poly = pg.find("Polygon")
    outer = poly.find("outerBoundaryIs").find("LinearRing")
    assert outer.find("coordinates").text.strip().startswith("0,0,0")
    assert poly.find("innerBoundaryIs") is None


def test_polygon_with_hole():
    outer = [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 0, 0]]
    hole = [[1, 1, 0], [2, 1, 0], [2, 2, 0], [1, 1, 0]]
    pg = base.polygon([outer, hole], "Poly")
    poly = pg.find("Polygon")
    assert poly.find("innerBoundaryIs") is not None


# --- optional z (altitude) -------------------------------------------------

def test_point_optional_z_defaults_to_zero():
    pm = base.point([-71.05, 42.36], "P")
    assert pm.find("Point").find("coordinates").text == "-71.05,42.36,0"


def test_point_explicit_z_preserved():
    pm = base.point([-71.05, 42.36, 12], "P")
    assert pm.find("Point").find("coordinates").text == "-71.05,42.36,12"


def test_point_optional_z_keeps_explicit_altitude_mode():
    # Omitting z must not override an explicitly requested altitude mode.
    pm = base.point([-71.05, 42.36], "P", z_mode="ABS")
    assert pm.find("Point").find("altitudeMode").text == "absolute"


def test_line_optional_z_defaults_to_zero():
    ln = base.line([[-71.05, 42.36], [-71.06, 42.37]], "L")
    assert ln.find("LineString").find("coordinates").text.strip() == \
        "-71.05,42.36,0 -71.06,42.37,0"


def test_line_mixed_2d_and_3d_coords():
    ln = base.line([[-71.05, 42.36], [-71.06, 42.37, 5]], "L")
    assert ln.find("LineString").find("coordinates").text.strip() == \
        "-71.05,42.36,0 -71.06,42.37,5"


def test_polygon_optional_z_outer_and_inner_rings():
    outer = [[0, 0], [4, 0], [4, 4], [0, 0]]
    hole = [[1, 1], [2, 1], [2, 2], [1, 1]]
    pg = base.polygon([outer, hole], "Poly")
    poly = pg.find("Polygon")
    assert poly.find("outerBoundaryIs").find("LinearRing").find(
        "coordinates").text.strip().startswith("0,0,0")
    assert poly.find("innerBoundaryIs").find("LinearRing").find(
        "coordinates").text.strip().startswith("1,1,0")


# --- description / snippet across feature builders -------------------------

def _make(builder):
    """Call point/line/polygon with a minimal valid geometry."""
    if builder is base.point:
        return lambda **kw: base.point([0, 0], "F", **kw)
    if builder is base.line:
        return lambda **kw: base.line([[0, 0], [1, 1]], "F", **kw)
    return lambda **kw: base.polygon([[[0, 0], [1, 0], [1, 1], [0, 0]]], "F", **kw)


@pytest.mark.parametrize("builder", [base.point, base.line, base.polygon])
def test_snippet_emitted_only_when_given(builder):
    make = _make(builder)
    assert make().find("snippet") is None
    pm = make(blurb="On State St")
    assert pm.find("snippet").text == "On State St"


@pytest.mark.parametrize("builder", [base.point, base.line, base.polygon])
def test_description_only_is_whole_balloon(builder):
    pm = _make(builder)(desc="Historic tower.")
    assert pm.find("description").text == "Historic tower."


@pytest.mark.parametrize("builder", [base.point, base.line, base.polygon])
def test_description_sits_above_attribute_table(builder):
    pm = _make(builder)(desc="Historic tower.", headers=["City"], attrs=["Boston"])
    assert pm.find("description").text == "Historic tower.<br><b>City</b>: Boston<br>"
    # ExtendedData still carries the structured attributes.
    assert pm.find("ExtendedData").find("Data").get("name") == "City"


@pytest.mark.parametrize("builder", [base.point, base.line, base.polygon])
def test_attributes_only_balloon_unchanged(builder):
    pm = _make(builder)(headers=["City"], attrs=["Boston"])
    assert pm.find("description").text == "<b>City</b>: Boston<br>"


@pytest.mark.parametrize("builder", [base.point, base.line, base.polygon])
def test_snippet_precedes_description(builder):
    pm = _make(builder)(blurb="S", desc="D")
    tags = [c.tag for c in list(pm)]
    assert tags.index("snippet") < tags.index("description")


# --- style builders --------------------------------------------------------

def test_point_style_element():
    st = base.point_style("pStyle")
    assert st.tag == "Style"
    assert st.get("id") == "pStyle"
    assert st.find("IconStyle") is not None
    assert st.find("LabelStyle") is not None


def test_line_style_element():
    st = base.line_style("lStyle")
    assert st.get("id") == "lStyle"
    assert st.find("LineStyle").find("width").text == "3.0"


def test_polygon_style_element():
    st = base.polygon_style("gStyle")
    assert st.get("id") == "gStyle"
    assert st.find("PolyStyle") is not None
    assert st.find("LineStyle") is not None


# --- folder ----------------------------------------------------------------

def test_folder_open_collapsed_semantics():
    pm = base.point([0, 0, 0], "P")
    collapsed = base.folder("F", [pm], collapsed=True)
    expanded = base.folder("F", [pm], collapsed=False)
    assert collapsed.find("open").text == "0"   # collapsed -> not open
    assert expanded.find("open").text == "1"     # expanded -> open
    # contained item is appended
    assert collapsed.find("Placemark") is not None


def test_folder_hidden_default_visibility_zero():
    f = base.folder("F", [])
    assert f.find("visibility").text == "0"   # hidden default True


# --- kml -------------------------------------------------------------------

def test_kml_returns_valid_xml_string():
    pm = base.point([-71.0, 42.3, 0], "P")
    s = kmlb.kml("Doc", [pm])
    assert s.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    # round-trips through ElementTree
    root = ET.fromstring(s[s.index("<kml"):])
    assert root.tag.endswith("kml")


def test_kml_writes_file(tmp_path):
    pm = base.point([-71.0, 42.3, 0], "P")
    out = tmp_path / "nested" / "doc.kml"
    s = kmlb.kml("Doc", [pm], path=str(out))
    assert out.exists()
    assert out.read_text(encoding="utf-8") == s


def test_kml_open_semantics():
    s_collapsed = kmlb.kml("Doc", [], collapsed=True)
    s_expanded = kmlb.kml("Doc", [], collapsed=False)
    assert "<open>0</open>" in s_collapsed
    assert "<open>1</open>" in s_expanded


def test_kml_styles_included():
    st = base.point_style("pStyle")
    pm = base.point([0, 0, 0], "P", style_to_use="pStyle")
    s = kmlb.kml("Doc", [pm], styles=[st])
    assert 'id="pStyle"' in s


# --- networklink_kml -------------------------------------------------------

_KML_NS = "{http://www.opengis.net/kml/2.2}"


def test_networklink_basic():
    s = base.networklink_kml("Link", "https://example.com/feed.kml")
    root = ET.fromstring(s[s.index("<kml"):])
    link = root.find(f"{_KML_NS}NetworkLink").find(f"{_KML_NS}Link")
    assert link.find(f"{_KML_NS}href").text == "https://example.com/feed.kml"
    assert link.find(f"{_KML_NS}refreshInterval").text == "300"


def test_networklink_no_refresh():
    s = base.networklink_kml("Link", "https://example.com/feed.kml", refresh_interval=-1)
    root = ET.fromstring(s[s.index("<kml"):])
    link = root.find(f"{_KML_NS}NetworkLink").find(f"{_KML_NS}Link")
    assert link.find(f"{_KML_NS}refreshInterval") is None


def test_networklink_writes_file(tmp_path):
    out = tmp_path / "nl.kml"
    base.networklink_kml("Link", "https://example.com/feed.kml", write_path=str(out))
    assert out.exists()


# --- color/icon shorthands & auto-default styling --------------------------

def test_point_style_accepts_color_name_and_icon_shorthand():
    st = base.point_style("s", color="red", icon="triangle")
    assert st.find("IconStyle").find("color").text == "ff0000ff"
    assert st.find("IconStyle").find("Icon").find("href").text.endswith("shapes/triangle.png")


def test_point_style_tether_line():
    # point_style can color/size the extruded-point tether via a LineStyle.
    st = base.point_style("p", line_color=("red", 50), line_width=4)
    assert st.find("LineStyle").find("color").text == base._kml_color("#ff0000", 50)
    assert st.find("LineStyle").find("width").text == "4"


def test_line_style_accepts_bare_hex():
    st = base.line_style("l", color="#00ff00")
    assert st.find("LineStyle").find("color").text == "ff00ff00"


def test_polygon_style_accepts_name_opacity_pair():
    st = base.polygon_style("p", fill_color=("red", 50))
    assert st.find("PolyStyle").find("color").text == "800000ff"


def test_bare_point_gets_inline_default_style():
    pm = base.point([0, 0, 0], "P")
    assert pm.find("Style") is not None
    assert pm.find("styleUrl") is None


def test_bare_line_and_polygon_get_inline_default_style():
    assert base.line([[0, 0, 0], [1, 1, 0]], "L").find("Style") is not None
    poly = base.polygon([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]], "P")
    assert poly.find("Style") is not None


def test_styled_feature_has_no_inline_style():
    pm = base.point([0, 0, 0], "P", style_to_use="x")
    assert pm.find("Style") is None
    assert pm.find("styleUrl").text == "#x"


def test_default_point_style_is_yellow():
    st = base._default_point_style()
    assert st.find("IconStyle").find("color").text == base._kml_color("#ffff00", 100)
    assert st.find("LineStyle") is None  # no tether unless extruded


def test_default_extruded_point_has_yellow_tether():
    st = base._default_point_style(True)
    assert st.find("LineStyle").find("color").text == base._kml_color("#ffff00", 100)
    assert st.find("LineStyle").find("width").text == "2.0"


def test_point_extrude_flag_and_tether_default():
    flat = base.point([0, 0, 0], "P")
    assert flat.find("Point").find("extrude").text == "0"
    assert flat.find("Style").find("LineStyle") is None
    raised = base.point([0, 0, 80], "P", z_mode="RTG", extrude=True)
    assert raised.find("Point").find("extrude").text == "1"
    assert raised.find("Style").find("LineStyle").find("color").text == base._kml_color("#ffff00", 100)


def test_default_line_style_is_red():
    st = base._default_line_style()
    assert st.find("LineStyle").find("color").text == base._kml_color("#ff0000", 100)
    assert st.find("PolyStyle") is None  # flat line has no wall fill


def test_default_extruded_line_has_3d_wall_fill():
    # An extruded line keeps the red stroke but its wall is filled like a 3D polygon.
    st = base._default_line_style(True)
    assert st.find("LineStyle").find("color").text == base._kml_color("#ff0000", 100)
    assert st.find("PolyStyle").find("color").text == base._kml_color("#495a7f", 45)


def test_extruded_line_uses_wall_fill_default():
    ln = base.line([[0, 0, 50], [1, 1, 50]], "L", z_mode="ABS",
                   extrude=True)
    assert ln.find("Style").find("PolyStyle").find("color").text == base._kml_color("#495a7f", 45)


def test_default_polygon_flat_colors():
    st = base._default_polygon_style(False)
    assert st.find("PolyStyle").find("color").text == base._kml_color("#00aaff", 30)
    assert st.find("LineStyle").find("color").text == base._kml_color("#ffff00", 100)


def test_default_polygon_3d_colors():
    st = base._default_polygon_style(True)
    assert st.find("PolyStyle").find("color").text == base._kml_color("#495a7f", 45)
    assert st.find("LineStyle").find("color").text == base._kml_color("#ffaa00", 100)


def test_flat_polygon_uses_flat_default():
    poly = base.polygon([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]], "P")
    assert poly.find("Style").find("LineStyle").find("color").text == base._kml_color("#ffff00", 100)


def test_extruded_polygon_uses_3d_default():
    poly = base.polygon([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0]]], "P",
                        extrude=True)
    assert poly.find("Style").find("LineStyle").find("color").text == base._kml_color("#ffaa00", 100)


def test_raised_polygon_without_extrude_stays_flat():
    # Only extrude=True polygons count as 3D; a raised ABS polygon is flat.
    poly = base.polygon([[[0, 0, 50], [1, 0, 50], [1, 1, 50], [0, 0, 50]]], "P",
                        z_mode="ABS")
    assert poly.find("Style").find("PolyStyle").find("color").text == base._kml_color("#00aaff", 30)

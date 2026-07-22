# kmlb - A straightforward Google Earth KML builder
# Copyright (c) 2026 @HFM3 (https://github.com/HFM3)
# SPDX-License-Identifier: MIT
"""Functions for creating KML features, styles, and documents."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal, Optional, Sequence, Tuple, Union
from urllib.parse import unquote

from .colors import get as _color_hex
from .icons import get as _resolve_icon

__all__ = [
    "look_at",
    "camera",
    "point",
    "street_view",
    "search_poi",
    "line",
    "polygon",
    "point_style",
    "line_style",
    "polygon_style",
    "folder",
    "kml",
    "networklink_kml",
]

# Abbreviated altitude modes accepted across the public API. ``Literal`` gives
# editors autocomplete and allows type checkers flag typos before runtime; the
# values are expanded to their full KML names by ``_altitude_modes``. The two
# sea-floor codes (CSF, RSF) are Google gx: extensions, useful for ocean and
# bathymetry work, and are written as <gx:altitudeMode> rather than the standard
# <altitudeMode> element.
AltitudeMode = Literal["CTG", "RTG", "ABS", "CSF", "RSF"]

# A (hex color, opacity) pair, e.g. ``('#a2d402', 100)``; opacity is 0-100.
Color = tuple[str, int]

# A color argument accepted by the style builders: a palette name ("red"), a
# hex string ("#a2d402"), or a (name-or-hex, opacity) pair.
ColorInput = Union[str, Tuple[str, int]]

# A single map coordinate: [longitude, latitude] or [longitude, latitude, elevation].
# Order is x = longitude, y = latitude; elevation (meters above the altitude-mode
# datum) is optional and defaults to 0. So both [-71.05, 42.36] and
# [-71.05, 42.36, 30] are valid coordinates.
Coordinate = Sequence[float]


# Standard altitude modes, written as a plain <altitudeMode> element.
_STD_ALTITUDE_MODES = {'CTG': 'clampToGround',
                       'RTG': 'relativeToGround',
                       'ABS': 'absolute'}

# Google gx: extension altitude modes, measured against the sea floor. These
# must be written as <gx:altitudeMode> and require the xmlns:gx namespace on the
# KML root. Ocean and bathymetry work relies on these.
_GX_ALTITUDE_MODES = {'CSF': 'clampToSeaFloor',
                      'RSF': 'relativeToSeaFloor'}


def _altitude_modes(z_mode: str = "CTG") -> str:
    """
    Expands an abbreviated altitude mode to its full length name.

    INPUT:
        z_mode (String):
            Can be set to any of the following abbreviations:
                CTG = clampToGround
                    Ignores any elevation value and places the feature on the surface of the ground.
                RTG = relativeToGround
                    Measures the elevation from the ground level directly below the coordinates.
                ABS = absolute
                    Elevation relative to mean sea level.
                CSF = clampToSeaFloor
                    Ignores any elevation value and places the feature on the sea floor.
                RSF = relativeToSeaFloor
                    Measures the elevation from the sea floor directly below the coordinates.

    OUTPUT:
        full_mode (String):
            The expanded equivalent of the abbreviated input.
            Unrecognized values fall back to 'clampToGround'.
    """

    code = z_mode.upper()

    if code in _STD_ALTITUDE_MODES:
        return _STD_ALTITUDE_MODES[code]
    if code in _GX_ALTITUDE_MODES:
        return _GX_ALTITUDE_MODES[code]
    return 'clampToGround'


def _set_altitude_mode(parent: ET.Element, z_mode: str) -> ET.Element:
    """
    Appends the altitude-mode element for ``z_mode`` to ``parent``.

    Standard modes use a plain <altitudeMode> element. The sea-floor modes are
    Google gx: extensions and use <gx:altitudeMode> instead, so the matching tag
    is chosen here. Unrecognized values fall back to clampToGround written as a
    standard <altitudeMode>. Returns the element that was created.
    """

    code = z_mode.upper()
    tag = 'gx:altitudeMode' if code in _GX_ALTITUDE_MODES else 'altitudeMode'

    element = ET.SubElement(parent, tag)
    element.text = _altitude_modes(code)
    return element


def _kml_color(hex6_color: str, opacity: int = 100) -> str:
    """
    Converts a hex color code to a KML-compatible color string.

    OVERVIEW:
        Returns a KML equivalent of the provided color code & opacity.

        In a '.kml' file, color (Red, Green, Blue) and opacity (Alpha) are expressed together in the
        following order: ABGR (whereas a hex color code is in RGB order.)

        If '#a2d402' (R=a2, G=d4, B=02) with 100% opacity (A=ff) is provided, the KML compatible
        equivalent of 'ff02d4a2' will be returned where:

         - 'ff' = Alpha
         - '02' = Blue
         - 'd4' = Green
         - 'a2' = Red

    INPUTS:
        hex6_color (String): A hex color code.
            Example: '#a2d402'

            (Note: Retain the preceding "#" symbol)

        opacity (Integer) [optional]: A value between 0 and 100 where 0 is transparent.
            (Default = 100)

    OUTPUT:
        _kml_color (String):
            KML compatible equivalent of the input hex color code.
    """

    r = hex6_color[1:3]
    g = hex6_color[3:5]
    b = hex6_color[5:]

    if 0 > opacity or opacity > 100:
        raise ValueError("Opacity value must be between 0 and 100")

    opacity_hex = format(int(round(opacity / 100 * 255, 0)), '02x')
    kml_color_code = str(opacity_hex + b + g + r).lower()

    return kml_color_code


def _resolve_color(value: ColorInput) -> Tuple[str, int]:
    """Normalize a color argument to a ``(#rrggbb, opacity)`` pair.

    Accepts a palette name, a ``#rrggbb`` hex string, or a ``(name|hex, opacity)``
    pair. A bare string defaults to full (100) opacity.
    """
    if isinstance(value, str):
        spec, opacity = value, 100
    else:
        spec, opacity = value
    hex6 = spec if spec.startswith('#') else _color_hex(spec)
    return hex6, opacity


def _floatify(coord: Coordinate) -> list:
    """Coerce a coordinate's string components to float.

    Lets string coordinates feed the builders directly, e.g. a CSV row such as
    ['-71.05', '42.36', '30']. Numbers are left untouched so existing int/float
    coordinates keep their exact formatting; only strings are converted. Returns a
    new [lon, lat] or [lon, lat, z] list, preserving the coordinate's length.
    """
    return [c if isinstance(c, (int, float)) else float(c) for c in coord]


def _coord_text(coord: Coordinate) -> str:
    """Format a coordinate as a KML 'lon,lat,elev' string.

    The elevation (z) value is optional: a 2-element [lon, lat] coordinate is
    treated as having an elevation of 0. KML's <coordinates> element always
    expects three comma-separated values.
    """
    lon, lat = coord[0], coord[1]
    elev = coord[2] if len(coord) > 2 else 0
    return f"{lon},{lat},{elev}"


def _description_text(desc: Optional[str], headers: list, attrs: list) -> str:
    """Compose the description-balloon text.

    An optional free-text/HTML ``desc`` blurb is placed above the table
    auto-built from ``headers``/``attrs`` (``<b>header</b>: value<br>``). With
    only a blurb it is the whole balloon; with only attributes it is just the table;
    with both, the blurb sits above the table separated by a line break.
    """
    table = ''.join("<b>" + str(h) + "</b>: " + str(a) + "<br>"
                    for h, a in zip(headers, attrs))
    if desc is None:
        return table
    blurb = str(desc)
    return blurb + "<br>" + table if table else blurb


def _append_extended_data(placemark: ET.Element, headers: list, attrs: list) -> None:
    """Append an ``<ExtendedData>`` table of name/value pairs to a placemark."""
    extended_data = ET.SubElement(placemark, 'ExtendedData')
    for h, a in zip(headers, attrs):
        data = ET.SubElement(extended_data, 'Data', {'name': h})
        ET.SubElement(data, 'value').text = str(a)


def look_at(coords: Coordinate, distance: float, azimuth: float, tilt: float,
            *, z_mode: AltitudeMode = "ABS") -> ET.Element:
    """
    Creates a KML 'LookAt' element to define a camera angle.

    OVERVIEW:
        A 'LookAt' orbits a target: it frames the coordinate given by 'coords'
        from 'distance' meters away, at the given 'azimuth' and 'tilt'. The result
        can be passed as the 'cam' argument to a feature or document to set a
        default view.

    INPUT:
        coords (List of three Floats):
            A list of x, y, z coordinates as [x, y, z].
        distance (Float):
            Camera distance in meters from the point specified by 'coords'.
        azimuth (Float):
            The direction that the camera will face in degrees from 0-360.
        tilt (Float):
            The tilt of the camera towards the object.
            Values range from 0 to 90 degrees.
            A value of 0 degrees indicates viewing from directly above.
            A value of 90 degrees indicates viewing along the horizon.
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') (Default = 'ABS').
            'CSF' and 'RSF' clamp to or measure from the sea floor.

    OUTPUT:
        lookat (Element):
            A KML 'LookAt' element.
    """

    # Create point's coordinate string.
    coords = _floatify(coords)
    lookat = ET.Element('LookAt')
    ET.SubElement(lookat, 'longitude').text = f"{coords[0]}"
    ET.SubElement(lookat, 'latitude').text = f"{coords[1]}"
    ET.SubElement(lookat, 'altitude').text = f"{coords[2]}"
    ET.SubElement(lookat, 'heading').text = f"{azimuth}"
    ET.SubElement(lookat, 'tilt').text = f"{tilt}"
    ET.SubElement(lookat, 'range').text = f"{distance}"
    _set_altitude_mode(lookat, z_mode)

    return lookat


def camera(coords: Coordinate, heading: float, tilt: float, *, roll: float = 0.0,
           streetview: bool = False, fov: Optional[float] = None,
           z_mode: AltitudeMode = "ABS") -> ET.Element:
    """
    Creates a KML 'Camera' element to define a viewpoint.

    OVERVIEW:
        A 'Camera' positions the eye in space and aims it, unlike 'LookAt' which orbits a target
        point. The result can be passed as the 'cam' argument to 'point', 'line', 'polygon',
        'folder', or 'kml' to set a default view.

        Set 'streetview' to True to have the camera enter Google Street View at the
        camera's location. No panorama id is needed: Google Earth snaps to the
        nearest available panorama, and 'heading', 'tilt', and 'fov' aim and zoom
        the view. (To open one exact, known panorama from a Google Maps link, use
        'street_view' instead.)

    INPUTS:
        coords (List of two or three Floats):
            A coordinate as [x, y] or [x, y, z]. The z (altitude) value is optional; if omitted it
            is treated as 0.
        heading (Float):
            The direction that the camera faces in degrees from 0-360.
        tilt (Float):
            The tilt of the camera in degrees.
            A value of 0 degrees points the camera straight down.
            A value of 90 degrees points the camera at the horizon.
            Values above 90 degrees point the camera up toward the sky.
        roll (Float) [Optional]:
            The rotation of the camera about the axis it looks along, in degrees (Default = 0.0).
        streetview (Bool) [Optional]:
            True = the camera enters Street View at its location, snapping to the
            nearest panorama (no panorama id required) (Default = False).
        fov (Float) [Optional]:
            The camera's field of view ('gx:fovy') in degrees. A smaller value zooms
            in. Emitted only when provided (Default = None).
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') (Default = 'ABS').
            'CSF' and 'RSF' clamp to or measure from the sea floor.

    OUTPUT:
        camera (Element):
            A KML 'Camera' element.
    """

    cam = ET.Element('Camera')

    coords = _floatify(coords)
    lon = coords[0]
    lat = coords[1]
    alt = coords[2] if len(coords) > 2 else 0

    ET.SubElement(cam, 'longitude').text = f"{lon}"
    ET.SubElement(cam, 'latitude').text = f"{lat}"
    ET.SubElement(cam, 'altitude').text = f"{alt}"
    ET.SubElement(cam, 'heading').text = f"{heading}"
    ET.SubElement(cam, 'tilt').text = f"{tilt}"
    ET.SubElement(cam, 'roll').text = f"{roll}"
    _set_altitude_mode(cam, z_mode)

    # Street View toggle goes first (matching Google Earth's export ordering) and
    # the field-of-view zoom ('gx:fovy') goes last.
    if streetview:
        cam.insert(0, _viewer_options(streetview=True))
    if fov is not None:
        ET.SubElement(cam, 'gx:fovy').text = f"{fov}"

    return cam


def point(coords: Coordinate, name: str, *, headers: Optional[list] = None,
          attrs: Optional[list] = None, desc: Optional[str] = None,
          blurb: Optional[str] = None, z_mode: AltitudeMode = "CTG",
          style_to_use: Optional[str] = None, hidden: bool = False,
          extrude: bool = False, cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a KML point marker.

    OVERVIEW:
        Creates a KML point element that can be included in a KML document.

    INPUTS:
        coords (List of Floats):
            A coordinate as [x, y] or [x, y, z]. The z (elevation) value is
            optional; if omitted it is treated as 0.
        name (String):
            The name to be given to the point.
        headers (List) [Optional]:
            A list of titles (headers) for the attributes of the point feature.
        attrs (List) [Optional]:
            A list of the properties (attributes) of the point.
        desc (String) [Optional]:
            Free text/HTML for the description balloon, rendered above the
            headers/attributes table. On its own it is the whole balloon.
        blurb (String) [Optional]:
            A short summary shown beneath the name in Google Earth's places list.
            Emitted as a '<snippet>' element only when provided.
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') (Default = 'CTG').
            'CSF' and 'RSF' clamp to or measure from the sea floor.
        style_to_use (String) [Optional]:
            The name of the point style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').
        extrude (Bool) [Optional]:
            True = draw a vertical tether line from the point down to the ground.
            Only visible when the point is raised (a non-'CTG' z_mode with a
            non-zero elevation). (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view of the point.

    OUTPUTS:
        placemark (Element):
            An XML element representing a KML Placemark.
    """

    # Create placemark
    coords = _floatify(coords)
    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)

    # Set 'visibility' value
    visibility = 1
    if hidden is True:
        visibility = 0
    ET.SubElement(placemark, 'visibility').text = str(visibility)

    # Assign style
    if style_to_use is not None:
        ET.SubElement(placemark, "styleUrl").text = '#' + str(style_to_use)
    else:
        placemark.append(_default_point_style(extrude))

    # Normalize attribute lists.
    if headers is None:
        headers = []
    if attrs is None:
        attrs = []

    # Short places-list summary, then the description balloon.
    if blurb is not None:
        ET.SubElement(placemark, 'snippet').text = str(blurb)
    ET.SubElement(placemark, "description").text = _description_text(desc, headers, attrs)

    # Create KML point as a child of placemark
    kml_point = ET.SubElement(placemark, 'Point')

    # Assign altitude mode to point
    _set_altitude_mode(kml_point, z_mode)

    # Set 'extrude' value (draws a tether to the ground when the point is raised)
    ET.SubElement(kml_point, 'extrude').text = str(1 if extrude else 0)

    # Create point's coordinate string.
    ET.SubElement(kml_point, 'coordinates').text = _coord_text(coords)

    # Create point's 'extended data' attribute table.
    _append_extended_data(placemark, headers, attrs)

    # Placemark Default Camera Angle
    if cam is not None:
        placemark.append(cam)

    return placemark


def _viewer_options(streetview: bool = False, pano_id: Optional[str] = None,
                    date: Optional[str] = None) -> Optional[ET.Element]:
    """
    Builds the 'gx:ViewerOptions' Street View block for a Camera, or 'None' when
    no Street View options are requested.

    The 'streetview' option is emitted whenever Street View is requested outright
    or a specific panorama is named.
    """

    if not (streetview or pano_id is not None or date is not None):
        return None

    viewer_options = ET.Element('gx:ViewerOptions')
    if streetview or pano_id is not None:
        ET.SubElement(viewer_options, 'gx:option', {'name': 'streetview'})
    if pano_id is not None:
        ET.SubElement(viewer_options, 'gx:streetViewPanoId').text = str(pano_id)
    if date is not None:
        ET.SubElement(viewer_options, 'gx:streetViewDate').text = str(date)

    return viewer_options


def _parse_street_view_url(url: str) -> dict:
    """
    Extracts Street View parameters from a Google Maps URL.

    OVERVIEW:
        Reads the location, camera angle, and panorama id out of a Google Maps Street View link.
        The location is the '@<lat>,<lon>' pair that follows '/maps/', the camera tokens are the
        comma-separated values ending in 'y' (field of view), 'h' (heading), and 't' (tilt), and
        the panorama id is the '!1s<id>' token in the 'data=' segment, with the 'panoid=<id>'
        parameter in the embedded thumbnail URL as a fallback.

    INPUT:
        url (String):
            A Google Maps Street View URL.

    OUTPUT:
        parts (Dictionary):
            A dictionary with keys 'lon', 'lat', 'heading', 'tilt', 'fov', and 'pano_id'.
            'heading', 'tilt', and 'fov' are 'None' when the URL does not contain them.

    Raises 'ValueError' when the location or panorama id cannot be found.
    """

    text = str(url)

    # Location: the '@lat,lon' pair (latitude first) that follows '/maps/@'.
    coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', text)

    # Panorama id: the '!1s<id>' token, or the embedded 'panoid=<id>' as a fallback.
    pano_match = re.search(r'!1s([^!?/]+)', text)
    if pano_match is None:
        pano_match = re.search(r'panoid(?:%3D|=)([^&%!]+)', text)

    if coord_match is None or pano_match is None:
        raise ValueError(
            "URL is not a recognized Google Maps Street View link. Expected a "
            "'.../@<lat>,<lon>,...' location and a panorama id ('!1s<id>' or 'panoid=<id>')."
        )

    def _token(suffix: str) -> Optional[float]:
        # Camera tokens look like '75y', '121.94h', '94.79t'.
        match = re.search(r'(-?\d+\.?\d*)' + suffix + r'\b', text)
        return float(match.group(1)) if match else None

    return {
        'lon': float(coord_match.group(2)),
        'lat': float(coord_match.group(1)),
        'heading': _token('h'),
        'tilt': _token('t'),
        'fov': _token('y'),
        'pano_id': unquote(pano_match.group(1)),
    }


def street_view(url: str, name: str = "Street View", *, headers: Optional[list] = None,
                attrs: Optional[list] = None, desc: Optional[str] = None,
                blurb: Optional[str] = None, style_to_use: Optional[str] = None,
                hidden: bool = False, extrude: bool = False,
                heading: Optional[float] = None, tilt: Optional[float] = None,
                roll: float = 0.0, zoom: Optional[float] = None, altitude: float = 0.0,
                z_mode: AltitudeMode = "ABS", date: Optional[str] = None) -> ET.Element:
    """
    Creates a KML point marker that opens a Google Street View panorama.

    OVERVIEW:
        Parses a Google Maps Street View URL and builds a point placemark whose default camera
        opens the exact panorama the URL points to. The location, heading, tilt, field of view, and
        panorama id are read from the URL; opening the placemark in Google Earth enters Street View
        at that panorama.

        A URL cannot carry a camera altitude or a panorama capture date, so those are supplied
        through the 'altitude' and 'date' arguments. The 'heading', 'tilt', 'zoom', and 'roll'
        arguments override the camera angle parsed from the URL for tight adjustment.

    INPUTS:
        url (String):
            A Google Maps Street View URL.
        name (String) [Optional]:
            The name to be given to the point (Default = 'Street View').
        headers (List) [Optional]:
            A list of titles (headers) for the attributes of the point feature.
        attrs (List) [Optional]:
            A list of the properties (attributes) of the point.
        desc (String) [Optional]:
            Free text/HTML for the description balloon, rendered above the
            headers/attributes table. On its own it is the whole balloon.
        blurb (String) [Optional]:
            A short summary shown beneath the name in Google Earth's places list.
            Emitted as a '<snippet>' element only when provided.
        style_to_use (String) [Optional]:
            The name of the point style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').
        extrude (Bool) [Optional]:
            True = draw a vertical tether line from the point down to the ground (Default = False).
        heading (Float) [Optional]:
            Overrides the camera heading parsed from the URL, in degrees from 0-360 (Default = None).
        tilt (Float) [Optional]:
            Overrides the camera tilt parsed from the URL, in degrees where 0 points straight down
            and 90 points at the horizon (Default = None).
        roll (Float) [Optional]:
            The rotation of the camera about the axis it looks along, in degrees (Default = 0.0).
        zoom (Float) [Optional]:
            Overrides the camera field of view ('gx:fovy') parsed from the URL, in degrees. A
            smaller value zooms in (Default = None).
        altitude (Float) [Optional]:
            The altitude of the Street View camera in meters (Default = 0.0).
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') for the camera (Default = 'ABS').
        date (String) [Optional]:
            The capture date of the Street View panorama to prefer, such as '2025-08' (Default = None).

    OUTPUT:
        placemark (Element):
            An XML element representing a KML Placemark.
    """

    parsed = _parse_street_view_url(url)

    # Camera angle: an explicit override wins, then the value parsed from the URL,
    # then a sane fallback for the rare URL that omits a token.
    if heading is None:
        heading = parsed['heading'] if parsed['heading'] is not None else 0.0
    if tilt is None:
        tilt = parsed['tilt'] if parsed['tilt'] is not None else 90.0
    if zoom is None:
        zoom = parsed['fov'] if parsed['fov'] is not None else 60.0

    lon = parsed['lon']
    lat = parsed['lat']

    cam = camera([lon, lat, altitude], heading, tilt, roll=roll, z_mode=z_mode)

    # The Street View-only pieces attach around the generic camera: the
    # 'gx:ViewerOptions' toggle goes first (matching Google Earth's export
    # ordering) and 'gx:fovy' (zoom) goes last.
    viewer_options = _viewer_options(streetview=True, pano_id=parsed['pano_id'], date=date)
    if viewer_options is not None:
        cam.insert(0, viewer_options)
    ET.SubElement(cam, 'gx:fovy').text = f"{zoom}"

    return point([lon, lat], name, headers=headers, attrs=attrs, desc=desc,
                 blurb=blurb, style_to_use=style_to_use, hidden=hidden,
                 extrude=extrude, cam=cam)


def search_poi(poi: str, name: Optional[str] = None, *, headers: Optional[list] = None,
               attrs: Optional[list] = None, desc: Optional[str] = None,
               blurb: Optional[str] = None, style_to_use: Optional[str] = None,
               hidden: bool = False) -> ET.Element:
    """
    Creates a KML point marker from a Point of Interest (POI) or an address.

    OVERVIEW:
        Creates a KML point element whose location is resolved by Google Earth from a search
        string. Rather than storing fixed coordinates, the placemark carries an '<address>'
        element; Google Earth geocodes that address when the placemark is loaded and places the
        point accordingly.

    INPUTS:
        poi (String):
            The string equivalent of what would be typed into a search bar to locate a POI or an address.
        name (String) [Optional]:
            The name to be given to the point. If no name is provided, the 'poi' argument's value will be used as the point's name.
        headers (List) [Optional]:
            A list of titles (headers) for the attributes of the point feature.
        attrs (List) [Optional]:
            A list of the properties (attributes) of the point.
        desc (String) [Optional]:
            Free text/HTML for the placemark's description balloon, rendered above the
            headers/attributes table. On its own it is the whole balloon.
        blurb (String) [Optional]:
            A short summary shown beneath the placemark's name in Google Earth's places list. Emitted
            as a '<snippet>' element only when provided.
        style_to_use (String) [Optional]:
            The name of the point style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').

    OUTPUTS:
        placemark (Element):
            An XML element representing a KML Placemark.
    """

    # Create placemark
    placemark = ET.Element('Placemark')

    # Name (defaults to the search string).
    if name is None:
        name = poi
    ET.SubElement(placemark, 'name').text = str(name)

    # Set 'visibility' value.
    visibility = 1
    if hidden is True:
        visibility = 0
    ET.SubElement(placemark, 'visibility').text = str(visibility)

    # Assign address to point. Google Earth geocodes it at display time.
    ET.SubElement(placemark, 'address').text = str(poi)

    # Short places-list summary.
    if blurb is not None:
        ET.SubElement(placemark, 'snippet').text = str(blurb)

    # Description balloon: an explicit 'description' blurb sits above the
    # headers/attributes table. Exactly one <description> is emitted.
    if headers is None:
        headers = []
    if attrs is None:
        attrs = []
    ET.SubElement(placemark, "description").text = _description_text(desc, headers, attrs)

    # Assign style.
    if style_to_use is not None:
        ET.SubElement(placemark, "styleUrl").text = '#' + str(style_to_use)

    # Create point's 'extended data' attribute table.
    _append_extended_data(placemark, headers, attrs)

    return placemark


def line(coords: Sequence[Coordinate], name: str, *, headers: Optional[list] = None,
         attrs: Optional[list] = None, desc: Optional[str] = None,
         blurb: Optional[str] = None, z_mode: AltitudeMode = "CTG",
         style_to_use: Optional[str] = None, hidden: bool = False,
         follow_terrain: bool = True, extrude: bool = False,
         cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a KML line/polyline.

    OVERVIEW:
        Creates a KML line/polyline element that can be included in a KML document.

    INPUTS:
        coords (List of coordinate sets):
            A list of the coordinate sets comprising the line. Each set is
            [x, y] or [x, y, z]; the z (elevation) value is optional and is
            treated as 0 when omitted.
        name (String):
            The name to be given to the line.
        headers (List) [Optional]:
            A list of titles (headers) for the attributes of the line feature.
        attrs (List) [Optional]:
            A list of the properties (attributes) of the line.
        desc (String) [Optional]:
            Free text/HTML for the description balloon, rendered above the
            headers/attributes table. On its own it is the whole balloon.
        blurb (String) [Optional]:
            A short summary shown beneath the name in Google Earth's places list.
            Emitted as a '<snippet>' element only when provided.
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') (Default = 'CTG').
            'CSF' and 'RSF' clamp to or measure from the sea floor.
        style_to_use (String) [Optional]:
            The name of the line style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the line will be visible (Default = 'False').
        follow_terrain (Bool) [Optional]:
            True = Line will follow terrain and the curvature of the Earth.
            False = Line will take a path through terrain/Earth if needed. (Default = True).
            Note: Only works when `z_mode` is set to 'CTG'.
        extrude (Bool) [Optional]:
            True = Vertices of the line are extruded toward the center of the Earth. (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view of the line.

    OUTPUT:
        placemark (Element):
            An XML element representing a KML Placemark.
    """

    # Create placemark
    coords = [_floatify(c) for c in coords]
    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)

    # Set 'visibility' value
    visibility = 1
    if hidden is True:
        visibility = 0
    ET.SubElement(placemark, 'visibility').text = str(visibility)

    # Assign style
    if style_to_use is not None:
        ET.SubElement(placemark, "styleUrl").text = '#' + str(style_to_use)
    else:
        placemark.append(_default_line_style(extrude))

    # Normalize attribute lists.
    if headers is None:
        headers = []
    if attrs is None:
        attrs = []

    # Short places-list summary, then the description balloon.
    if blurb is not None:
        ET.SubElement(placemark, 'snippet').text = str(blurb)
    ET.SubElement(placemark, "description").text = _description_text(desc, headers, attrs)

    # Create KML line as a child of placemark
    linestring = ET.SubElement(placemark, 'LineString')

    # Assign altitude mode to line
    _set_altitude_mode(linestring, z_mode)

    # Set 'tessellate' value
    tessellate = 1
    if follow_terrain is False:
        tessellate = 0
    ET.SubElement(linestring, 'tessellate').text = str(tessellate)

    # Set 'extrude' value
    ET.SubElement(linestring, 'extrude').text = str(1 if extrude else 0)

    # Create line's coordinate string.
    coord_string = ''
    for coord_set in coords:
        coord_string += _coord_text(coord_set) + " "
    ET.SubElement(linestring, 'coordinates').text = coord_string

    # Create line's 'extended data' attribute table.
    _append_extended_data(placemark, headers, attrs)

    # Placemark Default Camera Angle
    if cam is not None:
        placemark.append(cam)

    return placemark


def polygon(coords: Sequence[Sequence[Coordinate]], name: str, *, headers: Optional[list] = None,
            attrs: Optional[list] = None, desc: Optional[str] = None,
            blurb: Optional[str] = None, z_mode: AltitudeMode = "CTG",
            style_to_use: Optional[str] = None, hidden: bool = False,
            follow_terrain: bool = True, extrude: bool = False,
            cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a KML polygon.

    OVERVIEW:
        Creates a KML polygon element that can be included in a KML document.

    INPUTS:
        coords (List of linear rings):
            A list of linear rings containing coordinates that comprise the polygon. The first ring
            is the outer boundary; any additional rings are inner boundaries (holes).
            Each coordinate is [x, y] or [x, y, z]; the z (elevation) value is
            optional and is treated as 0 when omitted.
        name (String):
            The name to be given to the polygon.
        headers (List) [Optional]:
            A list of titles (headers) for the attributes of the polygon feature.
        attrs (List) [Optional]:
            A list of the properties (attributes) of the polygon.
        desc (String) [Optional]:
            Free text/HTML for the description balloon, rendered above the
            headers/attributes table. On its own it is the whole balloon.
        blurb (String) [Optional]:
            A short summary shown beneath the name in Google Earth's places list.
            Emitted as a '<snippet>' element only when provided.
        z_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS', 'CSF', 'RSF') (Default = 'CTG').
            'CSF' and 'RSF' clamp to or measure from the sea floor.
        style_to_use (String) [Optional]:
            The name of the polygon style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the polygon will be visible (Default = 'False').
        follow_terrain (Bool) [Optional]:
            True = Polygon will follow terrain and the curvature of the Earth.
            False = Polygon will take a path through terrain/Earth if needed. (Default = True).
            Note: Only works when `z_mode` is set to 'CTG'.
        extrude (Bool) [Optional]:
            True = Vertices of the polygon are extruded toward the center of the Earth. (Default = False).
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view of the polygon.

    OUTPUT:
        placemark (Element):
            An XML element representing a KML Placemark.
    """

    # Create placemark
    coords = [[_floatify(c) for c in ring] for ring in coords]
    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)

    # Set 'visibility' value
    visibility = 1
    if hidden is True:
        visibility = 0
    ET.SubElement(placemark, 'visibility').text = str(visibility)

    # Assign style
    if style_to_use is not None:
        ET.SubElement(placemark, "styleUrl").text = '#' + str(style_to_use)
    else:
        placemark.append(_default_polygon_style(extrude))

    # Normalize attribute lists.
    if headers is None:
        headers = []
    if attrs is None:
        attrs = []

    # Short places-list summary, then the description balloon.
    if blurb is not None:
        ET.SubElement(placemark, 'snippet').text = str(blurb)
    ET.SubElement(placemark, "description").text = _description_text(desc, headers, attrs)

    # Create KML polygon as a child of placemark
    kml_polygon = ET.SubElement(placemark, 'Polygon')

    # Assign altitude mode to polygon
    _set_altitude_mode(kml_polygon, z_mode)

    # Set 'tessellate' value
    tessellate = 1
    if follow_terrain is False:
        tessellate = 0
    ET.SubElement(kml_polygon, 'tessellate').text = str(tessellate)

    # Set 'extrude' value
    ET.SubElement(kml_polygon, 'extrude').text = str(1 if extrude else 0)

    # Create outer boundary
    outer_boundary = ET.SubElement(kml_polygon, 'outerBoundaryIs')
    outer_boundary_lr = ET.SubElement(outer_boundary, 'LinearRing')

    # Outer boundary coordinate string.
    coord_string = ''
    for coord_set in coords[0]:
        coord_string += _coord_text(coord_set) + " "
    ET.SubElement(outer_boundary_lr, 'coordinates').text = coord_string

    # Create inner boundary/boundaries.
    for ring in coords[1:]:
        inner_boundary = ET.SubElement(kml_polygon, 'innerBoundaryIs')
        inner_boundary_lr = ET.SubElement(inner_boundary, 'LinearRing')

        # Inner boundary coordinate string.
        coord_string = ''
        for coord_set in ring:
            coord_string += _coord_text(coord_set) + " "
        ET.SubElement(inner_boundary_lr, 'coordinates').text = coord_string

    # Create polygon's 'extended data' attribute table.
    _append_extended_data(placemark, headers, attrs)

    # Placemark Default Camera Angle
    if cam is not None:
        placemark.append(cam)

    return placemark


def point_style(name: str,
                *,
                icon: str = "circle",
                color: ColorInput = ('#ffff00', 100), scale: float = 1.2,
                label_color: ColorInput = ('#ffffff', 100), label_size: float = 1.0,
                line_color: ColorInput = ('#ffff00', 100), line_width: float = 2.0) -> ET.Element:
    """
    Defines a KML point style.

    OVERVIEW:
        Defines the icon, color, label, and tether-line properties of a KML point
        marker. The tether line is the vertical line drawn down to the ground when a
        point is created with extrude=True.

    INPUTS:
        name (String):
            The name of the style.
            Note: Style name must be unique within the KML.
        icon (String) [Optional]:
            URL to the icon to use.
        color (Tuple) [Optional]:
            Defines the color and opacity of the icon to use.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).
            Example: ('#a2d402', 100)
        scale (Float) [Optional]:
            Point marker's icon size.
        label_color (Tuple) [Optional]:
            Defines the color and opacity of the labels to use.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).
        label_size (Float) [Optional]:
            Text size of the point's label.
        line_color (Tuple) [Optional]:
            Defines the color and opacity of the tether line drawn to the ground for
            an extruded point. A (color, opacity) tuple, hex color and 0-100 opacity.
        line_width (Float) [Optional]:
            Thickness of the tether line for an extruded point.

    OUTPUT:
        style (Element):
            An XML element representing a KML style definition.

    Notes
    -----
    Icons: http://kml4earth.appspot.com/icons.html
    """
    style = ET.Element("Style", id=name)
    icon_style = ET.SubElement(style, "IconStyle")
    ET.SubElement(icon_style, "color").text = _kml_color(*_resolve_color(color))
    ET.SubElement(icon_style, "scale").text = str(scale)

    icon_icon = ET.SubElement(icon_style, "Icon")
    ET.SubElement(icon_icon, "href").text = _resolve_icon(icon)

    label_style = ET.SubElement(style, "LabelStyle")
    ET.SubElement(label_style, "scale").text = str(label_size)
    ET.SubElement(label_style, "color").text = _kml_color(*_resolve_color(label_color))

    line_style = ET.SubElement(style, "LineStyle")
    ET.SubElement(line_style, "color").text = _kml_color(*_resolve_color(line_color))
    ET.SubElement(line_style, "width").text = str(line_width)

    return style


def line_style(name: str, *, color: ColorInput = ('#ff0000', 100), width: float = 3.0,
               extrude_color: ColorInput = ('#34c9eb', 35)) -> ET.Element:
    """
    Defines a KML line style.

    OVERVIEW:
        Defines the color and width of a KML line style.

    INPUTS:
        name (String):
            The name of the style.
            Note: Style name must be unique within the KML.
        color (Tuple) [Optional]:
            Defines the color and opacity of the line.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).
            Example: ('#a2d402', 100)
        width (Float) [Optional]:
            Line thickness.
        extrude_color (Tuple) [Optional]:
            Defines the color and opacity of the area below the line.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).

    OUTPUT:
        style (Element):
            An XML element representing a KML style definition.
    """

    style = ET.Element("Style", id=name)
    styled_line = ET.SubElement(style, "LineStyle")

    ET.SubElement(styled_line, "color").text = _kml_color(*_resolve_color(color))
    ET.SubElement(styled_line, "width").text = str(width)

    styled_extrude = ET.SubElement(style, "PolyStyle")
    ET.SubElement(styled_extrude, "color").text = _kml_color(*_resolve_color(extrude_color))

    return style


def polygon_style(name: str, *, fill_color: ColorInput = ('#03cafc', 40),
                  outline_color: ColorInput = ('#fcdf03', 100), outline_width: float = 3.0) -> ET.Element:
    """
    Defines a KML polygon style.

    OVERVIEW:
        Defines the outline and fill properties of a KML polygon style.

    INPUTS:
        name (String):
            The name of the style.
            Note: Style name must be unique within the KML.
        fill_color (Tuple) [Optional]:
            Defines the color and opacity of the polygon's fill.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).
            Example: ('#a2d402', 100)
        outline_color (Tuple) [Optional]:
            Defines the color and opacity of the polygon's outline.
            A tuple containing color and opacity respectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0 (min) and 100 (max).
        outline_width (Float) [Optional]:
            Outline thickness.

    OUTPUT:
        style (Element):
            An XML element representing a KML style definition.
    """

    style = ET.Element("Style", id=name)

    poly_color = ET.SubElement(style, "PolyStyle")
    ET.SubElement(poly_color, "color").text = _kml_color(*_resolve_color(fill_color))

    outline = ET.SubElement(style, "LineStyle")
    ET.SubElement(outline, "color").text = _kml_color(*_resolve_color(outline_color))
    ET.SubElement(outline, "width").text = str(outline_width)

    return style


def _default_point_style(extruded: bool = False) -> ET.Element:
    """Inline default style for an unstyled point.

    When the point is extruded to the ground, a yellow 2pt LineStyle colors the
    tether down to the surface, matching the point's icon color.
    """
    style = ET.Element('Style')
    icon_style = ET.SubElement(style, 'IconStyle')
    ET.SubElement(icon_style, 'color').text = _kml_color('#ffff00', 100)
    ET.SubElement(icon_style, 'scale').text = '1.1'
    icon = ET.SubElement(icon_style, 'Icon')
    ET.SubElement(icon, 'href').text = _resolve_icon('circle')
    label = ET.SubElement(style, 'LabelStyle')
    ET.SubElement(label, 'scale').text = '1.0'
    ET.SubElement(label, 'color').text = _kml_color('#ffffff', 100)
    if extruded:
        line_s = ET.SubElement(style, 'LineStyle')
        ET.SubElement(line_s, 'color').text = _kml_color('#ffff00', 100)
        ET.SubElement(line_s, 'width').text = '2.0'
    return style


def _default_line_style(extruded: bool = False) -> ET.Element:
    """Inline default style for an unstyled line.

    The line keeps a red stroke. When the line is extruded to the ground its wall
    is filled to match a 3D polygon (a 45%-opacity steel-grey fill).
    """
    style = ET.Element('Style')
    line_s = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_s, 'color').text = _kml_color('#ff0000', 100)
    ET.SubElement(line_s, 'width').text = '3.0'
    if extruded:
        poly = ET.SubElement(style, 'PolyStyle')
        ET.SubElement(poly, 'color').text = _kml_color('#495a7f', 45)
    return style


def _default_polygon_style(three_d: bool = False) -> ET.Element:
    """Inline default style for an unstyled polygon.

    A flat polygon gets a yellow outline over a light-blue fill. A 3D polygon
    (one extruded to the ground with extrude=True) gets an orange
    outline over a steel-grey fill so its walls read against imagery.
    """
    if three_d:
        outline, fill, fill_opacity = '#ffaa00', '#495a7f', 45
    else:
        outline, fill, fill_opacity = '#ffff00', '#00aaff', 30
    style = ET.Element('Style')
    poly = ET.SubElement(style, 'PolyStyle')
    ET.SubElement(poly, 'color').text = _kml_color(fill, fill_opacity)
    line_s = ET.SubElement(style, 'LineStyle')
    ET.SubElement(line_s, 'color').text = _kml_color(outline, 100)
    ET.SubElement(line_s, 'width').text = '2.0'
    return style


def folder(name: str, items: Sequence[ET.Element], *, desc: str = '',
           collapsed: bool = True, hidden: bool = True,
           cam: Optional[ET.Element] = None) -> ET.Element:
    """
    Creates a KML folder and fills it with the specified KML elements.

    OVERVIEW:
        Creates a folder to organize loose KML elements such as points, lines, polygons, or even
        other folders.

    INPUTS:
        name (String):
            The name of the folder to be created.
        items (List):
            A list of loose items to include in the new folder.
        desc (String) [Optional]:
            A small body of descriptive text for the folder.
        collapsed (Bool) [Optional]:
            True = Folder is collapsed.
            False = Folder is open/expanded.
        hidden (Bool) [Optional]:
            True = Folder is hidden.
            False = Folder is visible.
                Note: A folder's visibility is ultimately determined by the visibility of the contents within. The
                default is to have folders set to hidden so that empty folders are not visible. If an item gets added
                to a folder and that item is set to be visible, the containing folder will become visible as well -
                even if the folder is set to hidden. (Default = `True`)
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view of the folder.

    OUTPUT:
        new_folder (Element):
            An XML element representing a KML folder.
    """

    new_folder = ET.Element("Folder")
    ET.SubElement(new_folder, "name").text = str(name)
    ET.SubElement(new_folder, "description").text = str(desc)

    # KML's <open> is 1 for expanded and 0 for collapsed, the inverse of the
    # `collapsed` flag.
    open_value = 0 if collapsed else 1
    ET.SubElement(new_folder, "open").text = str(open_value)

    # Set 'visibility' value
    visibility = 0
    if hidden is False:
        visibility = 1

    ET.SubElement(new_folder, 'visibility').text = str(visibility)

    for item in items:
        new_folder.append(item)

    # Folder Default Camera Angle
    if cam is not None:
        new_folder.append(cam)

    return new_folder


def kml(name: str, features: Sequence[ET.Element], *, path: Optional[str] = None,
        desc: str = '', styles: Optional[Sequence[ET.Element]] = None,
        collapsed: bool = True, cam: Optional[ET.Element] = None) -> str:
    """
    Creates a KML document string and optionally writes it to a file.

    OVERVIEW:
        Creates an XML string that defines the KML document. This string can be written to a text
        file with a '.kml' extension.

    INPUTS:
        name (String):
            The name of the KML.
        features (List):
            A list of the defined point, line, polygon, and/or folder objects to include in the KML.
        path (String) [Optional]:
            The path to the file where the KML will be written. The KML's file name is defined in the path.
            Necessary folders will be created if they do not exist.
            Note: The file path should end in '.kml'.
        desc (String) [Optional]:
            A small body of descriptive text for the KML.
        styles (List) [Optional]:
            A list of the defined style objects to include in the KML.
        collapsed (Bool) [Optional]:
            True = Root folder is collapsed.
            False = Root folder is open/expanded.
        cam (Element) [Optional]:
            A KML 'LookAt' or 'Camera' element that sets the default camera view for the document.

    OUTPUT:
        kml_string (String):
            The XML string of the KML file.
    """

    kml_doc = ET.Element('kml', {'xmlns': 'http://www.opengis.net/kml/2.2',
                                 'xmlns:gx': 'http://www.google.com/kml/ext/2.2'})
    body = ET.SubElement(kml_doc, "Document")
    ET.SubElement(body, "name").text = str(name)
    ET.SubElement(body, "description").text = str(desc)

    # KML's <open> is 1 for expanded and 0 for collapsed, the inverse of the
    # `collapsed` flag.
    open_value = 0 if collapsed else 1
    ET.SubElement(body, "open").text = str(open_value)

    if styles is not None:
        for style in styles:
            body.append(style)

    for item in features:
        body.append(item)

    # KML Default Camera Angle
    if cam is not None:
        body.append(cam)

    kml_string = '<?xml version="1.0" encoding="UTF-8"?>'
    kml_string += ET.tostring(kml_doc, encoding='unicode', method='xml')

    if path is not None:
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w", encoding="utf-8") as f:
            f.write(kml_string)

    return kml_string


def networklink_kml(name: str, link_path: str, *, write_path: Optional[str] = None,
                    desc: str = '', refresh_interval: int = 300,
                    view_refresh: int = 0, collapsed: bool = True) -> str:
    """
    Creates a network link KML document string and optionally writes it to a file.

    OVERVIEW:
        Creates an XML string that defines a KML document with a network link. This string can be
        written to a text file with a '.kml' extension.

    INPUTS:
        name (String):
            The name of the KML.
        link_path (String):
            URL to the hosted KML.
        write_path (String) [Optional]:
            The path to the file where the KML will be written. The KML's file name is defined in the path.
            Necessary folders will be created if they do not exist.
            Note: The file path should end in '.kml'.
        desc (String) [Optional]:
            A small body of descriptive text for the KML.
        refresh_interval (Int) [Optional]:
            Number of seconds between file refreshes. (-1 = no refresh)
        view_refresh (Int) [Optional]:
            Number of seconds after camera movement stops before the area is refreshed. (-1 = no refresh)
        collapsed (Bool) [Optional]:
            True = Root folder is collapsed.
            False = Root folder is open/expanded.

    OUTPUT:
        kml_string (String):
            The XML string of the KML file.
    """

    kml_doc = ET.Element('kml', {'xmlns': 'http://www.opengis.net/kml/2.2'})
    ntwrk = ET.SubElement(kml_doc, "NetworkLink")
    ET.SubElement(ntwrk, "name").text = str(name)
    ET.SubElement(ntwrk, "description").text = str(desc)

    # KML's <open> is 1 for expanded and 0 for collapsed, the inverse of the
    # `collapsed` flag.
    open_value = 0 if collapsed else 1
    ET.SubElement(ntwrk, "open").text = str(open_value)

    style = ET.SubElement(ntwrk, "Style")
    list_style = ET.SubElement(style, "ListStyle")
    ET.SubElement(list_style, "listItemType").text = 'check'

    link = ET.SubElement(ntwrk, "Link")
    ET.SubElement(link, "href").text = link_path
    if refresh_interval > -1:
        ET.SubElement(link, "refreshMode").text = 'onInterval'
        ET.SubElement(link, "refreshInterval").text = str(refresh_interval)

    if view_refresh > -1:
        ET.SubElement(link, "viewRefreshMode").text = 'onStop'
        ET.SubElement(link, "viewRefreshTime").text = str(view_refresh)

    kml_string = '<?xml version="1.0" encoding="UTF-8"?>'
    kml_string += ET.tostring(kml_doc, encoding='unicode', method='xml')

    if write_path is not None:
        filepath = Path(write_path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w", encoding="utf-8") as f:
            f.write(kml_string)

    return kml_string

"""
Functions for creating KML files.

Example
-------
>>> # This example runs through creating a KML of Fenwy PArk in Boston, MA.
>>> # 1) Define Styles
>>> # 2) Define Geometries (Point, Line, Polygon)
>>> # 3) Add Geometries to folder
>>> # 4) Create KML string

>>> import kmlb

>>> # DEFINE STYLES
>>> # point style
>>> hp_style = kmlb.point_style('Bases Style', 'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png', ('#f2392c', 100))

>>> # line style
>>> wt_style = kmlb.line_style('Warning Track Style', ('#0ff563', 100))

>>> # polygon style
>>> ba_style = kmlb.polygon_style('Bases Area Style')

>>> # CREATE A POINT
>>> pt_coordinates = [-71.097769, 42.346249, 0]  # [Longitude, Latitude, Elevation]
>>> point_name = 'Home Plate'
>>> pt_property_titles = ['City', 'Park', 'Base']
>>> pt_properties = ['Boston', 'Fenway', 'Home']
>>> style_name = 'Bases Style'  # Would be defined ahead of time with 'point_style' function.
>>> home_plate = kmlb.point(pt_coordinates, point_name, pt_property_titles, pt_properties, 'CTG', style_name)

>>> # CREATE A POLYLINE
>>> warning_track_boundary_coords = [[-71.097727, 42.346729, 0],\
                                     [-71.097721, 42.347030, 0],\
                                     [-71.097023, 42.347030, 0],\
                                     [-71.096694, 42.346892, 0],\
                                     [-71.096457, 42.346414, 0],\
                                     [-71.096499, 42.346359, 0],\
                                     [-71.096695, 42.346306, 0],\
                                     [-71.096971, 42.346287, 0]]

>>> pl_property_titles = ['City', 'Park', 'Line']
>>> pl_properties = ['Boston', 'Fenway', 'Warning track']
>>> wt = kmlb.line(warning_track_boundary_coords, 'Warning Track', pl_property_titles, pl_properties, style_to_use='Warning Track Style')

>>> # CREATE A POLYGON
>>> bases = [[-71.097769, 42.346249, 0],\
             [-71.097440, 42.346251, 0],\
             [-71.097441, 42.346496, 0],\
             [-71.097772, 42.346491, 0],\
             [-71.097769, 42.346249, 0]]

>>> # Hole for pitcher's mound
>>> mound = [[-71.097656, 42.346331, 0],\
             [-71.097580, 42.346331, 0],\
             [-71.097580, 42.346387, 0],\
             [-71.097656, 42.346387, 0],\
             [-71.097656, 42.346331, 0]]

>>> poly_coordinates = [bases, mound]
>>> poly_property_titles = ['City', 'Park', 'Description']
>>> poly_properties = ['Boston', 'Fenway', 'Area inside of bases']
>>> bases_area = kmlb.polygon(poly_coordinates, 'Bases Area', poly_property_titles, poly_properties, style_to_use='Bases Area Style')

>>> # CREATE / POPULATE A FOLDER
>>> fenway = kmlb.folder('Fenway Park', [home_plate, wt, bases_area], 'Sample placemarks.')

>>> # CREATE KML STRING
>>> k = kmlb.kml('Fenway Park', [hp_style, wt_style, ba_style], [fenway])

"""

import xml.etree.ElementTree as ET


def altitude_modes(altitude_mode='CTG'):
    """
    Expands an abbreviated altitude mode to its full length name.

    INPUT:
        altitude_mode (String):
            Can be set to any of the following abbrevations:
                CTG = clampToGround
                    Ignores any altitude value and places the feature on the surface of the ground.
                RTG = relativeToGround
                    Measures the altitude from the ground level directly below the coordinates.
                ABS = absolute
                    Altitude relative to mean sea level.

    OUTPUT:
        full_mode (String):
            The expanded equivalent of the abbreviated input.


    Parameters
    ----------
    altitude_mode : str

    Returns
    -------
    full_mode : str

    """

    # Abbreviation dictionary
    abbreviations = {'ABS': 'absolute',
                     'CTG': 'clampToGround',
                     'RTG': 'relativeToGround'}

    altitude_mode = altitude_mode.upper()

    if altitude_mode in abbreviations:
        full_mode = abbreviations[altitude_mode]
    else:
        full_mode = 'clampToGround'

    return full_mode


def kml_color(hex6_color, opacity=100):
    """
    Converts hex color code to work within a KML.

    OVERVIEW:
        Retrurns a KML equivalent of the provided color code & opacity.


        In a '.kml' file, color (Red, Blue, Green) and opacity (Alpha) are expressed together in in the following order:
        ABGR (whereas a hex color code is in RGB order.)

         If '#a2d402' (R=a2, G=d4, B=02) with 100% opacity (A=ff) is provided, the KML compatible equivelant of
         'ff02d4a2 will be returned where:

         - 'ff' = Alpha
         - '02' = Blue
         - 'd4' = Green
         - 'a2' = Red

    INPUTS:
        hex6_color (String): A hex color code.
            Example: '#a2d402'

            (Note: Retain the preceding "#" symbol)

        opacity (Integer) [optional]: A value between 0 and 100 where 0 is transparent
            Default = 100.

    OUTPUT:
        kml_color (String):
            KML compatible equivelant of input hex color code.

    Parameters
    ----------
    hex6_color : str
    opacity : int, optional


    Returns
    -------
    kml_color: str

    """

    r = hex6_color[1:3]
    g = hex6_color[3:5]
    b = hex6_color[5:]

    if 0 > opacity or opacity > 100:
        raise ValueError("Opacity value must be between 0 and 100")

    opacity_hex = format(int(round(opacity / 100 * 255, 0)), '02x')
    kml_color_code = str(opacity_hex + b + g + r).lower()

    return kml_color_code


def point(coords, name, headers, attributes, altitude_mode="CTG", style_to_use=None, hidden=False):
    """
    Creates a KML point marker.

    OVERVIEW:
        Creates a KML point element that can be included in a KML document.

    INPUTS:
        coords (List of three Floats):
            A list of x, y, z coordinates as [x, y, z].
        name (String):
            The name to be given to the point.
        headers (List of Strings):
            A list of titles (headers) to the attributes of the point feature.
        attributes (List of Strings):
            A list of the properties (attributes) of the point.
        altitude_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS') (Default = 'CTG').
        style_to_use (String) [Optional]:
            The name of the point style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').

    OUTPUTS:
        placemark (Object):
            An XML element representing a KML Placemark.

    Parameters
    ----------
    coords : list[float]
    name : str
    headers : list[str]
    attributes : list[str]
    altitude_mode : {'CTG', 'RTG', 'ABS'}, optional
    style_to_use : str, optional
    hidden : bool, optional

    Returns
    -------
    object

    Example
    -------
    A point marking home plate at Fenway Park in Boston, MA.

    >>> coordinates = [-71.097769, 42.346249, 0]  # [Longitude, Latitude, Elevation]
    >>> point_name = 'Home Plate'
    >>> property_titles = ['City', 'Park', 'Base']
    >>> properties = ['Boston', 'Fenway', 'Home']
    >>> style_name = 'Bases Style'  # Would be defined ahead of time with 'point_style' function.

    >>> home_plate = point(coordinates, point_name, property_titles, properties, 'CTG', style_name)

    """

    # Create placemark
    placemark = ET.Element('Placemark')
    ET.SubElement(placemark, 'name').text = str(name)

    # Set 'visibility' value
    visibility = 1
    if hidden is True:
        visibility = 0
    ET.SubElement(placemark, 'visibility').text = str(visibility)

    # Assign style
    if style_to_use is not None:
        ET.SubElement(placemark, "styleUrl").text = str(style_to_use)

    # Format attributes for KML description balloon
    attribute_str = ''
    for cell in range(len(headers)):
        attribute_str += "<b>" + str(headers[cell]) + "</b>: " + str(attributes[cell]) + "<br>"
    ET.SubElement(placemark, "description").text = attribute_str

    # Create KML point as a child of placemark
    kml_point = ET.SubElement(placemark, 'Point')

    # Assign altitude mode to point
    ET.SubElement(kml_point, 'altitudeMode').text = altitude_modes(altitude_mode)

    # Create point's coordinate string.
    ET.SubElement(kml_point, 'coordinates').text = f"{coords[0]},{coords[1]},{coords[2]}"

    # Create point's 'extended data' attribute table.
    extended_data = ET.SubElement(placemark, 'ExtendedData')
    for cell in range(len(headers)):
        data = ET.SubElement(extended_data, 'Data', {'name': headers[cell]})
        ET.SubElement(data, 'displayName').text = str(headers[cell])
        ET.SubElement(data, 'value').text = str(attributes[cell])

    return placemark


def line(coords, name, headers, attributes, altitude_mode="CTG",
         style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False):
    """
    Creates a KML line/polyline.

    OVERVIEW:
        Creates a KML line/polyline element that can be included in a KML document.

    INPUTS:
        coords (List of coordinate sets):
            A list of the coordinate sets [x, y, z] comprising the line.
        name (String):
            The name to be given to the line.
        headers (List of Strings):
            A list of titles (headers) to the attributes of the point feature.
        attributes (List of Strings):
            A list of the properties (attributes) of the point.
        altitude_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS') (Default = 'CTG').
        style_to_use (String) [Optional]:
            The name of the line style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').
        follow_terrain (Bool) [Optional]:
            True = Line will follow terrain and curve]ature of the Earth.
            False = Line will take path through terrain/Earth if needed. (Default = True).
            Note: Only works when `altitude_mode` is set to 'CTG'.
        extrude_to_ground (Bool) [Optional]:
            True = Vertices of the line are extruded toward the center of the Earth's center. (Default = False).

    OUTPUT:
        placemark (Object):
            An XML element representing a KML Placemark.

    Parameters
    ----------
    coords : collection
    name : str
    headers : list[str]
    attributes : list[str]
    altitude_mode : {'CTG', 'RTG', 'ABS'}, optional
    style_to_use : str, optional
    hidden : bool, optional
    follow_terrain : bool, optional
        True = Line will follow terrain and curve of the Earth. (Default = True).
    extrude_to_ground : bool, optional
        True = Vertices of the line are extruded toward the center of the Earth's center. (Default = False).

    Returns
    -------
    object

    Example
    -------
    A line marking the warning track boundary at Fenway Park in Boston, MA.

   >>> warning_track_boundary_coords = [[-71.097727, 42.346729, 0],\
                                        [-71.097721, 42.347030, 0],\
                                        [-71.097023, 42.347030, 0],\
                                        [-71.096694, 42.346892, 0],\
                                        [-71.096457, 42.346414, 0],\
                                        [-71.096499, 42.346359, 0],\
                                        [-71.096695, 42.346306, 0],\
                                        [-71.096971, 42.346287, 0]]

    >>> property_titles = ['City', 'Park', 'Line']
    >>> properties = ['Boston', 'Fenway', 'Warning track']

    >>> wt = line(warning_track_boundary_coords, 'Warning Track', property_titles, properties, style_to_use='Warning Track Style')

    """

    # Create placemark
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

    # Format attributes for KML description balloon
    attribute_str = ''
    for cell in range(len(headers)):
        attribute_str += "<b>" + str(headers[cell]) + "</b>: " + str(attributes[cell]) + "<br>"
    ET.SubElement(placemark, "description").text = attribute_str

    # Create KML line as a child of placemark
    linestring = ET.SubElement(placemark, 'LineString')

    # Assign altitude mode to line
    ET.SubElement(linestring, 'altitudeMode').text = altitude_modes(altitude_mode)

    # Set 'tessellate' value
    tessellate = 1
    if follow_terrain is False:
        tessellate = 0
    ET.SubElement(linestring, 'tessellate').text = str(tessellate)

    # Set 'extrude' value
    extrude = 1
    if extrude_to_ground is False:
        extrude = 0
    ET.SubElement(linestring, 'extrude').text = str(extrude)

    # Create line's coordinate string.
    coord_string = ''
    for coord_set in coords:
        coord_string += f"{coord_set[0]},{coord_set[1]},{coord_set[2]} "
    ET.SubElement(linestring, 'coordinates').text = coord_string

    # Create line's 'extended data' attribute table.
    extended_data = ET.SubElement(placemark, 'ExtendedData')
    for cell in range(len(headers)):
        data = ET.SubElement(extended_data, 'Data', {'name': headers[cell]})
        ET.SubElement(data, 'displayName').text = str(headers[cell])
        ET.SubElement(data, 'value').text = str(attributes[cell])

    return placemark


def polygon(coords, name, headers, attributes, altitude_mode="CTG",
            style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False):
    """Creates a KML element of a polygon.

    Creates a KML polygon.

    OVERVIEW:
        Creates a KML line/polyline element that can be included in a KML document.

        A polygone is made up of 'linear rings' which are

    INPUTS:
        coords (List of coordinate sets):
            A list of linear rings containing coordinates that comprise the polygon.
        name (String):
            The name to be given to the line.
        headers (List of Strings):
            A list of titles (headers) to the attributes of the point feature.
        attributes (List of Strings):
            A list of the properties (attributes) of the point.
        altitude_mode (String) [Optional]:
            An abbreviated altitude mode ('CTG', 'RTG', 'ABS') (Default = 'CTG').
        style_to_use (String) [Optional]:
            The name of the line style to be used (Default = None).
        hidden (Bool) [Optional]:
            A value of 'True' or 'False' where 'False' means the point will be visible (Default = 'False').
        follow_terrain (Bool) [Optional]:
            True = Line will follow terrain and curve]ature of the Earth.
            False = Line will take path through terrain/Earth if needed. (Default = True).
            Note: Only works when `altitude_mode` is set to 'CTG'.
        extrude_to_ground (Bool) [Optional]:
            True = Vertices of the line are extruded toward the center of the Earth's center. (Default = False).

    OUTPUT:
        placemark (Object):
            An XML element representing a KML Placemark.

    Parameters
    ----------
    coords : collection
    name : str
    headers : list[str]
    attributes : list[str]
    altitude_mode : {'CTG', 'RTG', 'ABS'}, optional
    style_to_use : str, optional
    hidden : bool, optional
    follow_terrain : bool, optional
    extrude_to_ground : bool, optional

    Returns
    -------
    object

    Notes
    -----
    To close polygon, last coordinate set is a duplicate of first coordinate set.

    Example
    -------
    A polygon marking the area between the bases at Fenway Park in Boston, MA.

    >>> # Bases polygon
    >>> bases = [[-71.097769, 42.346249, 0],\
                 [-71.097440, 42.346251, 0],\
                 [-71.097441, 42.346496, 0],\
                 [-71.097772, 42.346491, 0],\
                 [-71.097769, 42.346249, 0]]

    >>> # Hole for pitcher's mound
    >>> mound = [[-71.097656, 42.346331, 0],\
                 [-71.097580, 42.346331, 0],\
                 [-71.097580, 42.346387, 0],\
                 [-71.097656, 42.346387, 0],\
                 [-71.097656, 42.346331, 0]]

    >>> coordinates = [bases, mound]

    >>> property_titles = ['City', 'Park', 'Description']
    >>> properties = ['Boston', 'Fenway', 'Area inside of bases']

    >>> bases_area = polygon(coordinates, 'Bases Area', property_titles, properties, style_to_use='Bases Area Style')

    """

    # Create placemark
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

    # Format attributes for KML description balloon
    attribute_str = ''
    for cell in range(len(headers)):
        attribute_str += "<b>" + str(headers[cell]) + "</b>: " + str(attributes[cell]) + "<br>"
    ET.SubElement(placemark, "description").text = attribute_str

    # Create KML polygon as a child of placemark
    kml_polygon = ET.SubElement(placemark, 'Polygon')

    # Assign altitude mode to polygon
    ET.SubElement(kml_polygon, 'altitudeMode').text = altitude_modes(altitude_mode)

    # Set 'tessellate' value
    tessellate = 1
    if follow_terrain is False:
        tessellate = 0
    ET.SubElement(kml_polygon, 'tessellate').text = str(tessellate)

    # Set 'extrude' value
    extrude = 1
    if extrude_to_ground is False:
        extrude = 0
    ET.SubElement(kml_polygon, 'extrude').text = str(extrude)

    # Create outer boundary
    outer_boundary = ET.SubElement(kml_polygon, 'outerBoundaryIs')
    outer_boundary_lr = ET.SubElement(outer_boundary, 'LinearRing')

    # Outer boundary coordinate string.
    coord_string = ''
    for coord_set in coords[0]:
        coord_string += f"{coord_set[0]},{coord_set[1]},{coord_set[2]} "
    ET.SubElement(outer_boundary_lr, 'coordinates').text = coord_string

    # Create inner boundary/boundaries.
    for ring in coords[1:]:
        inner_boundary = ET.SubElement(kml_polygon, 'innerBoundaryIs')
        inner_boundary_lr = ET.SubElement(inner_boundary, 'LinearRing')

        # Inner boundary coordinate string.
        coord_string = ''
        for coord_set in ring:
            coord_string += f"{coord_set[0]},{coord_set[1]},{coord_set[2]} "
        ET.SubElement(inner_boundary_lr, 'coordinates').text = coord_string

    # Create polygon's 'extended data' attribute table.
    extended_data = ET.SubElement(placemark, 'ExtendedData')
    for cell in range(len(headers)):
        data = ET.SubElement(extended_data, 'Data', {'name': headers[cell]})
        ET.SubElement(data, 'displayName').text = str(headers[cell])
        ET.SubElement(data, 'value').text = str(attributes[cell])

    return placemark


def point_style(name, icon="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", color=('#ffff00', 100),
                scale=1.2, label_color=('#ffffff', 100), label_size=1.0):
    """
    Defines a KML point style.

    OVERVIEW:
        Defines the icon, color, and label properties of a KML point marker.

    INPUTS:
        name (String):
            The name of the style.
            Note: Style name must be unique within the KML.
        icon (String) [Optional]:
            URL to the icon to use
        color (Tuple) [Optional]:
            Defines the color and opacity of the icon to use.
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).
            Example: ('#a2d402', 100)
        scale (Float) [Optional]:
            Point marker's icon size.
        label_color (Tuple) [Optional]:
            Defines the color and opacity of the labels to use.
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).
        label_size (Float) [Optional]:
            Text size of point's label.

    OUTPUT:
        style (Object):
            An XML element representing a KML style definition.

    Parameters
    ----------
    name : str
    icon : str, optional
    color : tuple[str, int], optional
    scale : float, optional
    label_color : tuple[str, int], optional
    label_size : float, optional

    Returns
    -------
    object

    Notes
    -----
    Icons: http://kml4earth.appspot.com/icons.html

    Example
    -------

    Point style for home plate (Red square icon style)

    >>> hp_style = point_style('Bases Style', 'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png', ('#f2392c', 100))

    """
    style = ET.Element("Style", id=name)
    icon_style = ET.SubElement(style, "IconStyle")
    ET.SubElement(icon_style, "color").text = kml_color(*color)
    ET.SubElement(icon_style, "scale").text = str(scale)

    icon_icon = ET.SubElement(icon_style, "Icon")
    ET.SubElement(icon_icon, "href").text = str(icon)

    label_style = ET.SubElement(style, "LabelStyle")
    ET.SubElement(label_style, "scale").text = str(label_size)
    ET.SubElement(label_style, "color").text = kml_color(*label_color)

    return style


def line_style(name, color=('#ff0000', 100), width=3.0, extrude_color=('#34c9eb', 35)):
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
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).
            Example: ('#a2d402', 100)
        width (Float) [Optional]:
            Line thickness.
        extrude_color (Tuple) [Optional]:
            Defines the color and opacity of the area below the line to use.
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).

    OUTPUT:
        style (Object):
            An XML element representing a KML style definition.


    Parameters
    ----------
    name : str
    color : tuple[str, int], optional
    width : float, optional
    extrude_color : tuple[str, int], optional

    Returns
    -------
    object

    Example
    -------
    warning track line style (Green Line)
    >>> wt_style = line_style('Warning Track Style', ('#0ff563', 100))

    """

    style = ET.Element("Style", id=name)
    styled_line = ET.SubElement(style, "LineStyle")

    ET.SubElement(styled_line, "color").text = kml_color(*color)
    ET.SubElement(styled_line, "width").text = str(width)

    styled_extrude = ET.SubElement(style, "PolyStyle")
    ET.SubElement(styled_extrude, "color").text = kml_color(*extrude_color)

    return style


def polygon_style(name, fill_color=('#03cafc', 40), outline_color=('#fcdf03', 100), outline_width=1.0,):
    """
    Defines a KML polygon style.

    OVERVIEW:
        Defines the outline and fill properties of a KML polygon style.

    INPUTS:
        name (String):
            The name of the style.
            Note: Style name must be unique within the KML.
        color (Tuple) [Optional]:
            Defines the color and opacity of polygon's fill.
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).
            Example: ('#a2d402', 100)
        outline_color (Tuple) [Optional]:
            Defines the color and opacity of the polygon's outline.
            A tuple containing color and opactiy repsectively.
            Color is defined with a hex color code.
            Opacity is defined with an integer between 0(min) and 100(max).
        outline_width (Float) [Optional]:
            Outline thickness.

    OUTPUT:
        style (Object):
            An XML element representing a KML style definition.

    Parameters
    ----------
    name : str
    fill_color : tuple[str, int]
    outline_color : tuple[str, int]
    outline_width : float

    Returns
    -------
    object

    Example
    -------
    Create a polygon style with default styling

    >>> ba_style = polygon_style('Bases Area Style')

    """

    style = ET.Element("Style", id=name)

    poly_color = ET.SubElement(style, "PolyStyle")
    ET.SubElement(poly_color, "color").text = kml_color(*fill_color)

    outline = ET.SubElement(style, "LineStyle")
    ET.SubElement(outline, "color").text = kml_color(*outline_color)
    ET.SubElement(outline, "width").text = str(outline_width)

    return style


def folder(name, loose_items, description='', collapsed=True, hidden=True):
    """
    Creates a KML a folder and fills it with specified KML elements.

    OVERVIEW:
        Creates a folder to organize loose KML elements sych as points, lines, polygon or even other folders.

    INPUTS:
        name (String):
            The name of the folder to be created.
        loose_items (List):
            A list of loose item to include in the new folder.
        description (String) [Optional]:
            A small body of descriptive text for the folder.
        collapsed (Bool) [Optional]:
            True = Folder is collapsed.
            False = Folder is open/expanded.
        hidden (Bool) [Optional]:
            True = Folder is hidden.
            False = Folder is visible.
                Note: A folder's visibility is set by the visibility of the contents within. The default is to have
                folders hidden so that empty folders are not visible. If an item gets added to a folder and the item
                is set to be visible, the containing folder will become visible as well - even if if the folder set to
                hidden.

    OUTPUT:
        new_folder (Object):
            An XML element representing a KML folder.

    Parameters
    ----------
    name : str
    loose_items : list
    description : str, optional
    collapsed : bool, optional
    hidden : bool, optional

    Returns
    -------
    object

    Examples
    --------
    >>> fenway = folder('Fenway Park', [home_plate, wt, bases_area], 'Sample placemarks.')

    """

    new_folder = ET.Element("Folder")
    ET.SubElement(new_folder, "name").text = str(name)
    ET.SubElement(new_folder, "description").text = str(description)

    if collapsed is False:
        collapsed = 1
    else:
        collapsed = 0

    ET.SubElement(new_folder, "open").text = str(collapsed)

    # Set 'visibility' value
    visibility = 0
    if hidden is False:
        visibility = 1

    ET.SubElement(new_folder, 'visibility').text = str(visibility)

    for item in loose_items:
        ET.Element.append(new_folder, item)

    return new_folder


def kml(name, styles, features, description='', collapsed=True):
    """
    Creates a KML string.

    OVERVIEW:
        Creates a the XML string that defines the KML document. This string can be written to text file with a '.kml' extension.

    INPUTS:
        name (String):
            The name of the KML
    styles (List):
        A list of the defined style object to include in the KML
    features (List):
        A list of the defined point, line, polygon, and/or folder objects to include in the KML
    description (String) [Optional]:
            A small body of descriptive text for the folder.
    collapsed (Bool) [Optional]:
            True = Root folder is collapsed.
            False = Root folder is open/expanded.

    OUTPUT:
        kml_string (String):
            A string representation of the XML that forms the KML.

    Parameters
    ----------
    name : str
    styles : list
    features : list
    description : str, optional
    collapsed : bool, optional

    Returns
    -------
    str

    Examples
    --------
    >>> k = kml('Fenway Park', [hp_style, wt_style, bases_area_style], [fenway])

    """

    kml_doc = ET.Element('kml', {'xmlns': 'http://www.opengis.net/kml/2.2'})
    body = ET.SubElement(kml_doc, "Document")
    ET.SubElement(body, "name").text = str(name)
    ET.SubElement(body, "description").text = str(description)

    if collapsed is False:
        collapsed = 1
    else:
        collapsed = 0

    ET.SubElement(body, "open").text = str(collapsed)

    for style in styles:
        ET.Element.append(body, style)
    for item in features:
        ET.Element.append(body, item)

    kml_string = '<?xml version="1.0" encoding="UTF-8"?>'
    kml_string += ET.tostring(kml_doc, encoding='unicode', method='xml')

    return kml_string

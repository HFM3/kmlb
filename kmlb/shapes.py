from kmlb.gis_basics import vicenty_direct
import kmlb.base


def wedge(center, azimuth, width, radius, steps=15, name='Wedge', **kwargs):
    """
    Creates a pie wedge shaped KML polygon.

    OVERVIEW:
        Creates a pie-wedge shaped polygon that can be included in a KML document.

    INPUTS:
        center (List of coordinate sets):
            A list of [x, y, z] coordinates that will be the origin of the pie wedge.
        azimuth (Float):
            The direction that the center of the wedge's arc will point. 0 = True North
        width (Float):
            The width of the wedge in degrees.
        radius (Float):
            The length of the wedge's straight edges.
        steps (Integer) [Optional]:
            The number of vertices along the curved edge of the wedge. More steps will make a smoother arc.
            (Default = 15)
        name (String) [Optional]:
            The name to be given to the wedge object within the KML.
            (Default = 'Wedge')
        **kwargs:
            Any keyword argument accepted by the kmlb.base.polygon function.

    OUTPUT:
        wedge (Object):
            An XML element representing a KML polygon.

    Parameters
    ----------
    center : list[float]
    azimuth : float
    width : float
    radius : float
    steps : int, optional
    name : str, optional
    kwargs

    Returns
    -------
    wedge : object

    """

    # Attribute table
    headers_default = ['Azimuth', 'Width', 'Radius', 'Steps', 'Center Lat', 'Center Lng', 'Center Z']
    headers = kwargs.pop('headers', headers_default)

    attributes_default = [azimuth, width, radius, steps, center[1], center[0], center[2]]
    attributes = kwargs.pop('attributes', attributes_default)

    # Starting azimuth is a 1/2 width clockwise from provided azimuth.
    start_az = (azimuth + width / 2) % 360
    step_degrees = width / (steps - 1)

    # Determine azimuth of each step
    azimuths = [(start_az - i * step_degrees) % 360 for i in range(steps)]

    # Calculate coordinates of the steps along wedge's arc.
    coords = [vicenty_direct(center, azimuth, radius)[0] for azimuth in azimuths]

    # Add wedge vertex as initial and final coordinate to close polygon.
    coords.insert(0, center)
    coords.append(center)

    # Create polygon
    wedge_poly = kmlb.base.polygon([coords], name, headers, attributes, **kwargs)

    return wedge_poly


def circle(center, radius, steps=72, name='Circle', **kwargs):
    """
    Creates a circle shaped KML polygon.

    OVERVIEW:
        Creates a circle shaped polygon that can be included in a KML document.

    INPUTS:
        center (List of coordinate sets):
            A list of [x, y, z] coordinates that will be the origin of the pie wedge.
        radius (Float):
            The length of the wedge's straight edges.
        steps (Integer) [Optional]:
            The number of vertices along the outer edge of circle. More steps will make a smoother arc.
            (Default = 72)
        name (String) [Optional]:
            The name to be given to the wedge object within the KML.
            (Default = 'Wedge')
        **kwargs:
            Any keyword argument accepted by the kmlb.base.polygon function.

    OUTPUT:
        wedge (Object):
            An XML element representing a KML polygon.

    Parameters
    ----------
    center : list[float]
    radius : float
    steps : int, optional
    name : str, optional
    kwargs

    Returns
    -------
    circle : object

    """

    # Attribute table
    headers_default = ['Radius', 'Steps', 'Center Lat', 'Center Lng', 'Center Z']
    headers = kwargs.pop('headers', headers_default)

    attributes_default = [radius, steps, center[1], center[0], center[2]]
    attributes = kwargs.pop('attributes', attributes_default)

    # Starting azimuth is a 1/2 width clockwise from provided azimuth.
    start_az = 0
    step_degrees = 360 / steps

    # Determine azimuth of each step
    azimuths = [(start_az - i * step_degrees) % 360 for i in range(steps)]

    # Calculate coordinates of the steps along circle's edge.
    coords = [vicenty_direct(center, azimuth, radius)[0] for azimuth in azimuths]

    # Add wedge vertex as initial and final coordinate to close polygon.
    v1 = coords[0]
    coords.append(v1)

    # Create polygon
    circle_poly = kmlb.base.polygon([coords], name, headers, attributes, **kwargs)

    return circle_poly


def graduated_rings(center, start, increment, count, folder_name='Rings', point_style_to_use='RingStyle', label_angle=90, **kwargs):
    """
    Creates a folder of graduated rings and labels.

    OVERVIEW:
        Creates a folder of graduated rings and labels that can be included in a KML document.
        The rings are polyons and the labels are labeled points.

    INPUTS:
        center (List of coordinate sets):
            A list of [x, y, z] coordinates that will be the origin of the pie wedge.
        start (Integer):
            The radius of the first ring in meters.
        increment (Integer)
            The spacing between rings in meters
        count (Integer):
            The number of rings to generate
        folder_name (String) [Optional]:
            The name of the containing folder.
            (Default = Rings)
        point_style_to_use (String) [Optional]:
            The name of the point style to be used.
            (Default = 'RingStyle')
        label_angle (Float) [Optional]:
            The angle in degrees from north at which to label the rings.
            (Default = 90)
        **kwargs:
            Any keyword argument accepted by the kmlb.base.polygon function. Used to define the rings.

    OUTPUT:
        rings_folder (Object):
            An XML element representing a KML folder.

    Parameters
    ----------
    center: list[float]
    start: int
    increment: int
    count: int
    folder_name: str, optional
    point_style_to_use: str, optional
    label_angle: float, optional
    kwargs

    Returns
    -------
    rings_folder: object

    """

    radii = range(start, count * increment + increment, increment)

    ring_polys = list()
    labels = list()

    for radius in radii:
        name = f"{radius} m"
        c = circle(center, radius, name=name, **kwargs)
        ring_polys.append(c)

        label_coords = vicenty_direct(center, label_angle, radius)[0]
        label_pt = kmlb.point(label_coords, name, style_to_use=point_style_to_use)
        labels.append(label_pt)

    polygon_folder = kmlb.folder('Rings', ring_polys)
    labels_folder = kmlb.folder('Labels', labels)

    rings_folder = kmlb.folder(folder_name, [polygon_folder, labels_folder])

    return rings_folder



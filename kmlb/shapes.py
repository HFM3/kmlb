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
    headers = ['Azimuth', 'Width', 'Radius', 'Steps', 'Center']
    attributes = [azimuth, width, radius, steps, center]

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
    wedge = kmlb.base.polygon([coords], name, headers, attributes, **kwargs)

    return wedge





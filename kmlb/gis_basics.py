from math import sin, cos, sqrt, atan, atan2, tan, radians, degrees

# Ellipsoid Parameters:

# length of semi-major axis of the ellipsoid
# Radius at equator in meters (WGS-84).
r_eq = 6378137.0

# Flattening of the ellipsoid (WGS-84)
f = 1/298.257223563

# length of semi-minor axis of the ellipsoid
# radius of prime meridian
r_pm = (1-f)*r_eq


def vicenty_inverse(p1, p2, precison=3, max_iter=250, tol=10**(-12)):
    """
    OVERVIEW:
        Iteratively calculates the distance along the surface of an ellipsoid between two points.

    INPUTS:
        p1 (List of two Floats):
            Point 1. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        p2 (List of two Floats):
            Point 2. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates can be provided, but 'z' will be ignored.)
        precision (Integer) [Optional]:
            Number of decimal places to reatain in the results of distance, and bearings. (Default = 3)
        max_iter (Integer) [Optional]:
            Maximum number of iterations to run formula for if tolerance is not satisfied. (Default = 250)
        tol (float) [Optional]:
            Convergence tolerance.
            If the tolerance is larger than the difference between the longitude values calculated in the current step
            and the longitude value calculated in the previous step, the formula will stop iterating as the desired
            tolerance has been achieved. (Default = 10^(-12) or 0.000 000 000 001 of a degree)

    OUTPUTS:
        dist_m (float):
            The distance (in meters) between the provided coordinates.
        init_bearing (float):
            The forward azimuth between p1 and p2 in degrees from geographic north.
        final_bearing (float):
            The final azimuth between p1 and p2 in degrees from geographic north.

    Parameters
    ----------
    p1 : list[float]
    p2 : list[float]
    precison: int, optional
    max_iter : int, optional
    tol : float, optional

    Returns
    -------
    dist_m : (float):
    init_bearing : (float):
    final_bearing : (float):

    """

    # Convert coordinate values to float
    p1 = [float(c) for c in p1]
    p2 = [float(c) for c in p2]

    # Pull lat and lng from coordinates
    lng1, lat1 = p1[:2]
    lng2, lat2 = p2[:2]

    # Reduced latitudes (latitude on the auxiliary sphere)
    u_1 = atan((1-f) * tan(radians(lat1)))
    u_2 = atan((1-f) * tan(radians(lat2)))

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

        c = (f / 16) * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))
        lambda_prev = lam
        lam = lng_diff + (1 - c) * f * sin_alpha * (sigma + c * sin_sigma * (cos2_sigma_m + c * cos_sigma * (-1 + 2 * cos2_sigma_m ** 2)))

        # Successful convergence
        diff = abs(lambda_prev - lam)
        if diff <= tol:
            break

    u_sq = cos_sq_alpha * ((r_eq**2 - r_pm**2) / r_pm**2)
    a = 1 + (u_sq / 16384) * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    b = (u_sq / 1024) * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sig = b * sin_sigma * (cos2_sigma_m + 0.25 * b * (cos_sigma * (-1 + 2 * cos2_sigma_m ** 2) - (1 / 6) * b * cos2_sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos2_sigma_m ** 2)))

    dist_m = r_pm * a * (sigma - delta_sig)
    dist_m = round(dist_m, precison)

    init_bearing = atan2(cos_u2 * sin(lam), cos_u1 * sin_u2 - sin_u1 * cos_u2 * cos(lam))
    init_bearing = round(degrees(init_bearing), precison)
    if init_bearing < 0:
        init_bearing += 360
    final_bearing = atan2(cos_u1 * sin(lam), (sin_u1 * -1) * cos_u2 + cos_u1 * sin_u2 * cos(lam))
    final_bearing = round(degrees(final_bearing), precison)
    if final_bearing < 0:
        final_bearing += 360

    return dist_m, init_bearing, final_bearing


def vicenty_direct(p1, init_bearing, distance_m, precision=3, max_iter=250, tol=10 ** (-12)):
    """
    OVERVIEW:
        Iteratively calculates the final coordinates (p2) of a line when given a starting point (p1), azimuth, and distance.

    INPUTS:
        p1 (List of two Floats):
            Point 1. A list of x, y coordinates as [x, y].
            (Note: [x, y, z] coordinates may be provided. Z coordinate will pass through unprocessed.)
        init_bearing (Float):
            The forward azimuth from p1 (in degrees from geographic north).
        distance_m (Float):
            The distance (in meters) of p2 from p1.
        precision (Integer) [Optional]:
            Number of decimal places to reatain of the final bearing. (Default = 3)
        max_iter (Integer) [Optional]:
            Maximum number of iterations to run formula for if tolerance is not satisfied. (Default = 250)
        tol (float) [Optional]:
            Convergence tolerance.
            If the tolerance is larger than the difference between the longitude values calculated in the current step
            and the longitude value calculated in the previous step, the formula will stop iterating as the desired
            tolerance has been achieved. (Default = 10^(-12) or 0.000 000 000 001 of a degree)

    OUTPUTS:
        p2 (List of Floats):
            Point 2. A list of x, y coordinates as [x, y].
        final_bearing (Float):
            The final azimuth between p1 and p2 in degrees from geographic north.


    Parameters
    ----------
    p1 : list[float]
    init_bearing : float
    distance_m : float
    precision: int, optional
    max_iter : int, optional
    tol : float, optional

    Returns
    -------
    p2 : list[float]
    final_bearing : float

    """

    # Pull lat and lng from coordinates as floats
    p1 = [float(c) for c in p1]
    p1_x, p1_y = p1[:2]

    init_bearing = radians(init_bearing)

    # Convert lat and lng to radians
    p1_x_rads = radians(p1_x)
    p1_y_rads = radians(p1_y)

    # Pre-calculated values to make formulas shorter
    tan_u1 = (1 - f) * tan(p1_y_rads)
    cos_u1 = 1 / sqrt(1 + tan_u1**2)
    sin_u1 = tan_u1 * cos_u1
    sigma_1 = atan2(tan_u1, cos(init_bearing))
    sin_alpha = cos_u1 * sin(init_bearing)
    cos_sq_alpha = 1 - sin_alpha**2
    u_sq = cos_sq_alpha * (r_eq**2 - r_pm**2) / r_pm**2
    a = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    b = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    sigma = distance_m / (r_pm * a)

    cos_2sigma_m = None

    for i in range(max_iter):
        cos_2sigma_m = cos(2 * sigma_1 + sigma)
        delta_sigma = b * sin(sigma) * (cos_2sigma_m + b / 4 * (cos(sigma) * (-1 + 2 * cos_2sigma_m**2) - b / 6 * cos_2sigma_m * (-3 + 4 * sin(sigma)**2) * (-3 + 4 * cos_2sigma_m**2)))

        sigma_prime = distance_m / r_pm * a + delta_sigma

        diff = abs(sigma - sigma_prime)

        sigma = sigma_prime

        if diff <= tol:
            break

    j = sin_u1 * cos(sigma) + cos_u1 * sin(sigma) * cos(init_bearing)
    m = (1 - f) * sqrt(sin_alpha ** 2 + (sin_u1 * sin(sigma) - cos_u1 * cos(sigma) * cos(init_bearing)) ** 2)
    p2_y_rads = atan2(j, m)

    lam = atan2((sin(sigma) * sin(init_bearing)), (cos_u1 * cos(sigma) - sin_u1 * sin(sigma) * cos(init_bearing)))
    c = f / 16 * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))
    p = lam - (1 - c) * f * sin_alpha * (sigma + c * sin(sigma) * (cos_2sigma_m + c * cos(sigma) * (-1 + 2 * cos_2sigma_m**2)))
    p2_x_rads = p1_x_rads + p
    final_bearing = atan2(sin_alpha, (-1 * (sin_u1 * sin(sigma) - cos_u1 * cos(sigma) * cos(init_bearing))))

    p2 = [degrees(p2_x_rads), degrees(p2_y_rads)]
    p2.extend(p1[2:])
    final_bearing = round(degrees(final_bearing), precision)

    if final_bearing < 0:
        final_bearing += 360

    return p2, final_bearing


def determinant(p1, p2, p3):
    """
    OVERVIEW:
        Calculates the determinant of a three-point line.
        Used for determining if p2 --> p3 is clockwise, counterclockwise, or colinear realtive to p1 --> p2.

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
        det (float):
            The determinant of a three-point line.

    Parameters
    ----------
    p1 : list[float]
    p2 : list[float]
    p3 : list[float]

    Returns
    -------
    det : float

    """
    """
    
    negative = counterclockwise
    0 = collinear
    positive = clockwise
    :param p1: point 1 [x, y]
    :param p2: point 2 [x, y]
    :param p3: point 3 [x, y]
    :return: determinant of three-point line segment
    """
    det = (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p3[1] - p2[1]) * (p2[0] - p1[0])

    return det

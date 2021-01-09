# KMLB

## Google Earth KML Builder

A straightforward KML building package that creates:

- Placemarks
- Lines & Polylines
- Polygons (2D + 3D)



## Functions

### Point

Define a KML point element

`point()`

```python
point(coords, name, headers, attributes, altitude_mode="CTG", style_to_use=None, hidden=False)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| coords    | List   | A coordinate set: `[X, Y, Z]`                                |
| name      | String | The name to be given to the point feature. The name will be used for labeling. |

##### Optional Parameters

| Parameter     | Type   | Description                                                  |
| ------------- | ------ | ------------------------------------------------------------ |
| headers       | List   | A list of the attribute titles for the point feature         |
| attributes    | List   | A list of properties for the point feature.                  |
| altitude_mode | String | One of the abbreviated altitude mode options: `'CTG'`, `'RTG'`, `'ABS'` (Default = `'CTG'`) |
| style_to_use  | String | The name of the `point_style()` to be used (Default = `None`). |
| hidden        | Bool   | A value of `'True'` or `'False'` where `'False'` means that the point will be visible. (Default = `'False'`). |

#### Output

| Output    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### About a Point

The first thing that is needed to define a `point() ` is a **coordinate set** that marks the location where the point is to be mapped. A coordinate set contains three values: X, Y, Z

- X = Longitude in decimal degrees
- Y = Latitude in decimal degrees
- Z = Height in meters

The point will also need a **name**. The point's name will be the value used to label the point on the map.

When the point is clicked on in the map, additional information can be displayed. This additional information is defined with **headers** (optional) and **attributes** (optional) parameters. Headers & Attributes work together and can be thought of as a table with "headers" being the top row and "attributes " being the second row.

|  City  |      Building      | Height (m) |
| :----: | :----------------: | :--------: |
| Boston | Custom House Tower |    151     |

The **altitude mode** (optional) defines the way the z-coordinate (height) is defined. When no altitude mode is given, "CTG" is used.

- **CTG** = Clamp to Ground. Ignores any altitude value and places the feature on the surface of the ground.
- **RTG** = Relative to Ground. Measures the altitude from the ground level directly below the coordinates.
- **ABS** = Absolute. Altitude relative to mean sea level.

A point can optionally be stylized. The **style to use** (optional) parameter is the name of the style to be applied to the point. A point's style is defined with the `point_style()` function.

Optionally, the point can be set to be visible or not with the **hidden** (optional) parameter. Setting **hidden** to `True` will hide the point on the map when the map first opens. The map user can make the point visible again in the map. Hide points when the data is to be included, but the data may clutter the map.  Points are visible by default.

#### Example

A simple point with no style applied.

```python
import kmlb

# Define a point that marks the top of Boston's Custom House Tower

# Define a point's parameters ahead of defining the point
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']

# Define the point
placemark = kmlb.point(coords, name, attribute_titles, attributes, 'RTG')
```

### Line

Define a KML line element

`line()`

```python
line(coords, name, headers, attributes, altitude_mode="CTG", style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False):
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                               |
| :-------- | :----- | :-------------------------------------------------------- |
| coords    | List   | A set of coordinate sets : `[[X1, Y1, Z1], [X2, Y2, Z2]]` |
| name      | String | The name to be given to the line feature.                 |

##### Optional Parameters

| Parameter         | Type   | Description                                                  |
| ----------------- | ------ | ------------------------------------------------------------ |
| headers           | List   | A list of the attribute titles for the point feature         |
| attributes        | List   | A list of properties for the point feature.                  |
| altitude_mode     | String | One of the abbreviated altitude mode options: `'CTG'`, `'RTG'`, `'ABS'` (Default = `'CTG'`) |
| style_to_use      | String | The name of the line_style()` to be used (Default = `None`). |
| hidden            | Bool   | A value of `'True'` or `'False'` where `'False'` means that the point will be visible. (Default = `'False'`). |
| follow_terrain    | Bool   | Determines whether or not the line will follow terrain and curve of the Earth. (Default = `True`). |
| extrude_to_ground | Bool   | Determines whether or not the vertices of the line are extruded toward the center of the Earth's center. (Default = `False`). |

#### Output

| Output    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### About a Line

Defining a `line()` is very similar to defining a `point()` with the main difference being how coordinate arguments are passed to the function. A line is composed of two coordinates sets - a starting point and an ending point. A polyline is composed of three or more coordinates sets - a starting point, mid point/s, and an ending point. In the KMLB Package, the `line()` function can accept coordinate sets for both lines and polylines. 

To define a line, place two [X, Y, Z] coordinate sets within `[]` like so: 

```python
[[X1, Y1, Z1], [X2, Y2, Z2]]
```

To define a polyline, place three or more coordinate sets within `[]` like so: 

```python
[[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3]]
```

A line's **style to use** (optional) parameter is the name of the style to be applied to the line. A line's style is defined with the `line_style()` function.

If two vertices of a line or polyline are very far apart, the shortest distance between them, will be through the Earth. Likewise, if a mountain is  between two vertices of a line, the line will go through the mountain rather than over it. To avoid having the mapped line go through the Earth *(or any terrain that may be between vertices)* keep the **follow terrain** (optional) parameter set to `True`. 

If the line being mapped is elevated above the surface of the Earth, it is possible to fill the area below the line and above the Earth's surface with a color. If the **extrude to ground** (optional) parameter is set to `True`, the `extrude_color()` defined in `lines_style()` will be displayed.

#### Example

A simple polyline with no style applied

```python
# Define a polyline that marks the path Boston's Custom House Tower to Boston Aquarium 

# Define a line's parameters ahead of defining the line.
# Z-coord is set to zero since altitude mode will be 'CTG'
coords = [[-71.053568, 42.359053, 0],
          [-71.053266, 42.359099, 0],
          [-71.053289, 42.359289, 0],
          [-71.050779, 42.359672, 0],
          [-71.050784, 42.359200, 0],
          [-71.050429, 42.359002, 0],
          [-71.049882, 42.359063, 0]]

name = 'Path to Aquarium'
attribute_titles = ['City', 'Starting Point', 'Ending Point']
attributes = ['Boston', 'Custom House Tower', 'Boston Aquarium']

# Define the line
placemark = kmlb.line(coords, name, attribute_titles, attributes)
```


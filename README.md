# KMLB

### Google Earth KML Builder

A straightforward KML building package that creates and maps:

- Placemarks
- Lines & Polylines
- Polygons (2D + 3D)

### INTRODUCTION:

#### Create a Point:

`point()`

```python
point(coords, name, headers, attributes, altitude_mode="CTG", style_to_use=None, hidden=False)
```

The first thing that is needed to define a point is a **coordinate set** that marks the location where the point is to be mapped. A coordinate set contains three values: X, Y, Z

- X = Longitude in decimal degrees
- Y = Latitude in decimal degrees
- Z = Height in meters

The point will also need a **name**. The point's name will be the value used to label the point on the map.

When the point is clicked on in the map, additional information can be displayed. This additional info is defined with **headers** and **attributes**. Headers & Attributes work together and can be thought of as a table with "headers" being the top row and "attributes " being the second row.

|  City  |      Building      | Height (m) |
| :----: | :----------------: | :--------: |
| Boston | Custom House Tower |    151     |

The **altitude mode** (optional) defines the way the z-coordinate (height) is defined. When no altitude mode is given, "CTG" is used.

​	**CTG** = Clamp to Ground. Ignores any altitude value and places the feature on the surface of the ground. 
​	RTG = Relative to Ground. Measures the altitude from the ground level directly below the coordinates.
​	**ABS** = Absolute. Altitude relative to mean sea level.

A point can optionally be stylized. The **style to use** (optional) parameter is the name of the style to be applied to the point. A point's style is defined with the `point_style()` function.

Optionally, the point can be set to be visible or not by setting **hidden** (optional) to `True` or `False`.  Points are visible by default.

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

#### Create a Line:

`line()`

```python
line(coords, name, headers, attributes, altitude_mode="CTG", style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False)
```

Defining a `line()` is very similar to defining a `point()` with the main difference being how coordinates are passed to the function. 

A line is composed of multiple coordinates sets. A line is composed of two coordinates sets - a starting point and an ending point. A polyline is composed of more than two coordinates sets. in the KMLB Package, the `line()` function can accept coordinate sets for both lines and polylines. 

To define a line, place two [X, Y, Z] coordinate sets within `[]` like so: 

​		`[[X1, Y1, Z1], [X2, Y2, Z2]]`

To define a polyline, place three or more coordinate sets within `[]` like so: 

​		`[[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3]]`

A line's **style to use** (optional) parameter is the name of the style to be applied to the line. A line's style is defined with the `line_style()`  function.

If two nodes of a line or polyline are very far apart, the shortest distance between them, will be through the Earth. Likewise, if a mountain is  between two points of a line, the line will go through the mountain rather than over it. To avoid having the mapped line go through the Earth, or any terrain that may be between the nodes, keep the **follow terrain** (optional) parameter set to `True`. 

If the line being mapped is elevated above the surface of the Earth, it is possible to fill in the area below the line and above the Earth's surface. if the **extrude to ground** (optional) parameter is set to `True`. 

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


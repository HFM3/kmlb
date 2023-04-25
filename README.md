<div align="center">
  <img src="https://raw.githubusercontent.com/HFM3/kmlb/main/images/logo/KMLB.png" width="40%"><br>
</div>


---
![PyPI](https://img.shields.io/pypi/v/kmlb?label=PyPi) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kmlb?label=Python) ![PyPI - License](https://img.shields.io/pypi/l/kmlb?label=License)

# KMLB

## A Straightforward Google Earth KML Builder

### Create KML files that contain:

- Placemarks
- Lines & Polylines
- Polygons (2D + 3D)
- Folders

### Customize:

- Colors
- Labels
- Icons
- Coordinates
- Elevations
- Camera Angles

## Example Use

**Writing a Basic KML file with KMLB:**

```python
import kmlb

# CREATE A POINT
fountain = kmlb.point([-71.051904, 42.358988, 0], 'Rings Fountain')

# WRITE KML FILE
kmlb.kml('Boston Fountain',  # KML name
         [fountain],  # Features
         r'C:\Users\UserName\Desktop\KMLB_Tutorial.kml'  # Export path
         )

```
**Mapping a POI or an address with KMLB:**

```python
import kmlb

# CREATE A POINT FROM A POI
bos_common = kmlb.search_poi('Boston Common, Boston, MA')

# CREATE A POINT FROM AN ADDRESS
ss = kmlb.search_poi('700 Atlantic Avenue, Boston, MA', name='South Station')

# WRITE KML FILE
kmlb.kml('Boston Landmarks',  # KML name
         [bos_common, ss],  # Features
         r'C:\Users\UserName\Desktop\KMLB_Tutorial.kml'  # Export path
         )

```

**Creating a Customized KML file with KMLB:**

```python
import kmlb

# DEFINE A STYLE
pt_style = kmlb.point_style('Red Triangle',  # Point style name
                            'http://maps.google.com/mapfiles/kml/shapes/triangle.png',  # Icon
                            ('#ff0000', 100),  # Icon color
                            1.0,  # Icon scale
                            ('#ffffff', 100),  # Label color
                            1.0  # Label size
                            )

# CREATE A POINT
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']
altitude_mode = 'RTG'  # 'Relative To Ground'
style_to_use = 'Red Triangle' # Name of point style defined earlier
clock_tower = kmlb.point(coords, name, attribute_titles, attributes, altitude_mode, style_to_use)

# WRITE KML FILE
kmlb.kml('Boston Clock Tower',  # KML Name
         [clock_tower],  # Features to include
         r'C:\Users\UserName\Desktop\KMLB_Tutorial.kml',  # Export path
         'Created with KMLB Python Package',  # KML Description
         [pt_style]  # Styles to include
         )

```

# FUNCTIONS

## Geometry Functions

### Point

Defines a KML point element.

`point()`

```python
point(coords, name, headers=None, attributes=None, altitude_mode="CTG", style_to_use=None, hidden=False, camera=None)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| coords    | List   | A coordinate set: `[X, Y, Z]`                                |
| name      | String | The name to be given to the point feature. The name will be used for labeling. |

##### Optional Parameters

| Parameter     | Type    | Description                                                  |
| ------------- | ------- | ------------------------------------------------------------ |
| headers       | List    | A list of the attribute titles for the point feature         |
| attributes    | List    | A list of properties for the point feature.                  |
| altitude_mode | String  | One of the abbreviated altitude mode options: `CTG`, `RTG`, `ABS`  (Default = `'CTG'`) |
| style_to_use  | String  | The name of the `point_style()` to be used (Default = `None`). |
| hidden        | Bool    | A value of `True` or `False` where `False` means that the point will be visible. (Default = `False`). |
| camera        | Element | A KML 'LookAt' element. (Default = `None`)                   |

#### Return

| Return    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### About a Point

The first thing that is needed to define a `point()` is a **coordinate set** that marks the location of where the point is to be mapped. A coordinate set contains three values: X, Y, Z

- X = Longitude in decimal degrees
- Y = Latitude in decimal degrees
- Z = Height in meters

The point will also need a **name**. The point's name will be the value used to label the point on the map.

When the point is clicked on in the map, additional information can be displayed. This additional information is defined with **headers** (optional) and **attributes** (optional) parameters. Headers & Attributes work together and can be thought of as a table with "headers" being the top row and "attributes " being the second row.

|  City  |      Building      | Height (m) |
| :----: | :----------------: | :--------: |
| Boston | Custom House Tower |    151     |

The **altitude mode** (optional) defines the way the z-coordinate (height) is mapped. When no altitude mode is given, "CTG" is used as the default.

- **CTG** = Clamp to Ground. Ignores any altitude value and places the feature on the surface of the ground.
- **RTG** = Relative to Ground. Measures the altitude from the ground level directly below the coordinates.
- **ABS** = Absolute. Altitude relative to mean sea level.

A point can optionally be stylized. The **style to use** (optional) parameter is the name of the style to be applied to the point. A point's style is defined with the `point_style()` function.

Optionally, the point can be set to be visible or not with the **hidden** (optional) parameter. Setting **hidden** to `True` will hide the point on the map when the map first opens. The map user can make the point visible again in the map. Hide points when the data is to be included, but the data may clutter the map.  Points are visible by default.

#### Example

A point with no style applied.

```python
import kmlb

# Define a point that marks the top of Boston's Custom House Tower

# Defining the point's arguments ahead of defining the point
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']

# Define the point
placemark = kmlb.point(coords, name, attribute_titles, attributes, 'RTG')
```

### Search POI

Defines a KML point element from a POI or an address search.

`search_poi()`

```python
search_poi(poi, name=None, headers=None, attributes=None, style_to_use=None, hidden=False):
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| poi       | String | The string equivalent of what would be typed into a search bar to locate a POI or an address. |
| name      | String | The name to be given to the point feature. The name will be used for labeling. |

##### Optional Parameters

| Parameter    | Type   | Description                                                  |
| ------------ | ------ | ------------------------------------------------------------ |
| name         | String | The name to be given to the point feature. The name will be used for labeling. If no name is provided, the 'poi' argument's value will be used as the point's name. |
| headers      | List   | A list of the attribute titles for the point feature         |
| attributes   | List   | A list of properties for the point feature.                  |
| style_to_use | String | The name of the `point_style()` to be used (Default = `None`). |
| hidden       | Bool   | A value of `True` or `False` where `False` means that the point will be visible. (Default = `False`). |

#### Return

| Return    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### Example

Create a point from a POI and an address.

```python
import kmlb

# CREATE A POINT FROM A POI
bos_common = kmlb.search_poi('Boston Common, Boston, MA')

# CREATE A POINT FROM AN ADDRESS
ss = kmlb.search_poi('700 Atlantic Avenue, Boston, MA', name='South Station')

# WRITE KML FILE
kmlb.kml('Boston Landmarks',  # KML name
         [bos_common, ss],  # Features
         r'C:\Users\UserName\Desktop\KMLB_Tutorial.kml'  # Export path
         )
```

### Line

Defines a KML line element.

`line()`

```python
line(coords, name, headers=None, attributes=None, altitude_mode="CTG", style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                |
| :-------- | :----- | :--------------------------------------------------------- |
| coords    | List   | A list of coordinate sets : `[[X1, Y1, Z1], [X2, Y2, Z2]]` |
| name      | String | The name to be given to the line feature.                  |

##### Optional Parameters

| Parameter         | Type    | Description                                                  |
| ----------------- | ------- | ------------------------------------------------------------ |
| headers           | List    | A list of the attribute titles for the line feature          |
| attributes        | List    | A list of properties for the line feature.                   |
| altitude_mode     | String  | One of the abbreviated altitude mode options: `CTG`, `RTG`, `ABS` (Default = `CTG`) |
| style_to_use      | String  | The name of the `line_style()` to be used (Default = `None`). |
| hidden            | Bool    | A value of `True` or `True` where `True` means that the point will be visible. (Default = `True`). |
| follow_terrain    | Bool    | Determines whether or not the line will follow terrain and curve of the Earth. (Default = `True`). |
| extrude_to_ground | Bool    | Determines whether or not the vertices of the line are extruded toward the center of the Earth's center. (Default = `False`). |
| camera            | Element | A KML 'LookAt' element. (Default = `None`)                   |

#### Return

| Return    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### About a Line

Defining a `line()` is very similar to defining a `point()` with the main difference being how the coordinates (coords) argument is formatted prior to being passed to the `line()` function. A line is composed of two coordinates sets - a starting point and an ending point. A polyline is composed of three or more coordinates sets - a starting point, mid point/s, and an ending point. In the KMLB Package, the `line()` function can accept coordinate sets for both lines and polylines. 

To define a line, place two [X, Y, Z] coordinate sets within `[]` like so: 

```python
line_coords = [[X1, Y1, Z1], [X2, Y2, Z2]]
```

To define a polyline, place three or more coordinate sets within `[]` like so: 

```python
polyline_coords = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3]]
```

A line's **style to use** (optional) parameter is the name of the style to be applied to the line. A line's style is defined with the `line_style()` function.

If two vertices of a line or polyline are very far apart, the shortest distance between them, will be through the Earth. Likewise, if a mountain is between two vertices of a line, the line will go through the mountain rather than over it. To avoid having the mapped line go through the Earth *(or any terrain that may be between vertices)* keep the **follow terrain** (optional) parameter set to `True`. 

If the line being mapped is elevated above the surface of the Earth, it is possible to fill the area below the line and above the Earth's surface with a color. If the **extrude to ground** (optional) parameter is set to `True`, the **extrude_color** defined in `lines_style()` will be displayed.

#### Example

A polyline with no style applied.

```python
# Define a polyline that marks the path from Boston's Custom House Tower to the Boston Aquarium

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

### Polygon

Defines a KML polygon element.

`polygon()`

```python
polygon(coords, name, headers=None, attributes=None, altitude_mode="CTG", style_to_use=None, hidden=False, follow_terrain=True, extrude_to_ground=False)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| coords    | List   | A list of coordinate sets that form rings (outer/inner rings). |
| name      | String | The name to be given to the polygon feature.                 |

##### Optional Parameters

| Parameter         | Type    | Description                                                  |
| ----------------- | ------- | ------------------------------------------------------------ |
| headers           | List    | A list of the attribute titles for the polygon feature       |
| attributes        | List    | A list of properties for the polygon feature.                |
| altitude_mode     | String  | One of the abbreviated altitude mode options: `CTG`, `RTG`, `ABS` (Default = `CTG`) |
| style_to_use      | String  | The name of the `polygon_style()`to be used (Default = `None`). |
| hidden            | Bool    | A value of `True` or `True` where `True` means that the point will be visible. (Default = `True`). |
| follow_terrain    | Bool    | Determines whether or not segments of the polygon will follow terrain and curve of the Earth. (Default = `True`). |
| extrude_to_ground | Bool    | Determines whether or not the vertices of the polygon are extruded toward the center of the Earth's center. (Default = `False`). |
| camera            | Element | A KML 'LookAt' element. (Default = `None`)                   |

#### Return

| Return    | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| placemark | Object | An XML element representing a KML Placemark. |

#### About a Polygon

A `polygon()` is defined by a single ***outer ring*** and any number of ***inner rings***. Each *ring* is similar to a polyline, with the only difference being that the first and final coordinate set of the ring must match each other. The first and final coordinate sets of each ring need to match so that the polyline *"closes"* and forms a polygon.  In this way, a triangle will be defined by four vertices/coordinates sets. Each ring must contain at least three distinct coordinate sets with the first and last sets matching each other.

- **Outer Ring**: Forms the exterior boundary of a polygon. A polygon can only have one outer ring defined.
- **Inner Ring**: Forms an interior hole within a polygon's outer ring. A polygon can have any number of inner rings defined.

A polygon is structured as follows:

```python
Polygon = [OuterRing, InnerRing1, InnerRing2, ....]
```

Inner rings are optional. The geometry of a polygon can be defined with only an outer ring like so:
```python
Polygon = [OuterRing]
```

To define an outer or inner ring of a polygon, place at least four [X, Y, Z] coordinate sets within `[]` like so: 

```python
ring_coords = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3], [X1, Y1, Z1]]
```

To define a polygon without any interior holes: 

```python
outer_ring = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3], [X1, Y1, Z1]]
polygon_coords = [outering]
```

To define a polygon with two interior holes: 

```python
outer_ring = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3], [X1, Y1, Z1]]

inner_ring1 = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3], [X1, Y1, Z1]]
inner_ring2 = [[X1, Y1, Z1], [X2, Y2, Z2], [X3, Y3, Z3], [X1, Y1, Z1]]

polygon_coords = [outering, inner_ring1, inner_ring2]
```

#### Example

A polygon with a hole and no style applied.

```python
# Define a polygon that outlines a portion of the Greenway with a hole for Rings Fountain

# Define a polygon's parameters ahead of defining the polygon.
# Z-coord is set to zero since altitude mode will be 'CTG'
outer_ring = [[-71.052336,42.359485,0],
              [-71.052333,42.359422,0],
              [-71.052153,42.358787,0],
              [-71.052110,42.358758,0],
              [-71.052049,42.358746,0],
              [-71.051735,42.358797,0],
              [-71.051664,42.358840,0],
              [-71.051658,42.358890,0],
              [-71.051837,42.359527,0],
              [-71.051865,42.359551,0],
              [-71.051915,42.359569,0],
              [-71.052288,42.359514,0],
              [-71.052336,42.359485,0]]

inner_ring = [[-71.052012,42.358864,0],
              [-71.051735,42.358910,0],
              [-71.051796,42.359109,0],
              [-71.052071,42.359065,0],
              [-71.052012,42.358864,0]]

coords = [outer_ring, inner_ring]

name = 'Rings Fountain on the Greenway'
attribute_titles = ['City', 'Park']
attributes = ['Boston', 'Greenway']

# Define the polygon
placemark = kmlb.polygon(coords, name, attribute_titles, attributes)
```

## Style Functions

Styles are used to customize the appearance of the features to be displayed on the map. Note: Once a style is defined, it can be used on as many applicable features as needed.

### Point Style

Defines a KML style that can be applied to point features.

`point_style()`

```python
point_style(name, icon="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", color=('#ffff00', 100), scale=1.2, label_color=('#ffffff', 100), label_size=1.0)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| name      | String | The name to be given to the style. The name will be used to reference the defined style. Note: The name must be unique within the KML document. |

##### Optional Parameters

The default style of a point is a yellow circle with a white label.

| Parameter   | Type   | Description                                                  |
| ----------- | ------ | ------------------------------------------------------------ |
| icon        | String | URL to the icon to use to mark the point with on the map.    |
| color       | Tuple  | Defines the color and opacity of the icon.  Color is defined with a hex color code. Opacity is defined with an integer between 0 and 100. Example: `('#a2d402', 100)` |
| scale       | Float  | The point marker's icon size. (Default = 1.2`)               |
| label_color | Tuple  | Defines the color and opacity of the point's  label.         |
| label_size  | Float  | Text size of point's label. (Default = 1.0`)                 |

#### Return

| Return | Type   | Description                                         |
| ------ | ------ | --------------------------------------------------- |
| style  | Object | An XML element representing a KML style definition. |

#### About a Point's Style

Each defined style requires a name that is unique to the KML document being created. Other than **name**, each  of the other `point_style()` parameters are optional when creating a point style. The default style a yellow circle with a white label.

#### Example

A point with default style applied.

```python
# Define style
pt_style = kmlb.point_style('Default Point Style')

# Defining the point's arguments ahead of defining the point
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']

# Define point using default style.
placemark = kmlb.point(coords, name, attribute_titles, attributes, 'RTG', 'Default Point Style')
```
A point with a custom style applied.

```python
# Define a custom blue square style
pt_style = kmlb.point_style('Blue Square',
                       'http://maps.google.com/mapfiles/kml/shapes/square.png',
                       ("#0251fc", 100))

# Point Arguments
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']

# Define point using default style.
placemark = kmlb.point(coords, name, attribute_titles, attributes, 'RTG', 'Blue Square')
```

### Line Style

Defines a KML style that can be applied to line features.

`line_style()`

```python
line_style(name, color=('#ff0000', 100), width=3.0, extrude_color=('#34c9eb', 35))
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| name      | String | The name to be given to the style. The name will be used to reference the defined style. Note: The name must be unique within the KML document. |

##### Optional Parameters

The default color of a line is red with a light transparent blue extrusion color.

| Parameter     | Type  | Description                                                  |
| ------------- | ----- | ------------------------------------------------------------ |
| color         | Tuple | Defines the color and opacity of the line.  Color is defined with a hex color code. Opacity is defined with an integer between 0 and 100. Example: `('#a2d402', 100)` |
| width         | Float | Line thickness. (Default = 3.0`)                             |
| extrude_color | Tuple | Defines the color and opacity of the area below the line. Note: Only displayed when the `extrude_to_ground` parameter of the `line()` function is set to `True` and and is only displayed for portions of the line that above the ground. |

#### Return

| Return | Type   | Description                                         |
| ------ | ------ | --------------------------------------------------- |
| style  | Object | An XML element representing a KML style definition. |

#### About a Line's Style

Each defined style requires a name that is unique to the KML document being created. Other than **name**, each  of the other `line_style()` parameters are optional when creating a line style. The default color of a line is red with a light transparent blue extrusion color.

#### Example

A polyline with a custom style applied.

```python
# Define a custom yellow line style
ln_style = kmlb.line_style('Yellow Line', ('#fcce02', 100))

# Line arguments
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
placemark = kmlb.line(coords, name, attribute_titles, attributes, style_to_use='Yellow Line')
```

### Polygon Style

Defines a KML style that can be applied to polygon features.

`polygon_style()`

```python
polygon_style(name, fill_color=('#03cafc', 40), outline_color=('#fcdf03', 100), outline_width=3.0)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| name      | String | The name to be given to the style. The name will be used to reference the defined style. Note: The name must be unique within the KML document. |

##### Optional Parameters

The default fill color of a polygon is a light transparent blue with a solid yellow outline.

| Parameter     | Type  | Description                                                  |
| ------------- | ----- | ------------------------------------------------------------ |
| fill_color    | Tuple | Defines the color and opacity of the polygon's fill color.  Color is defined with a hex color code. Opacity is defined with an integer between 0 and 100. Example: `('#a2d402', 100)` |
| outline_color | Tuple | Defines the color and opacity of the polygon's outline color. |
| outline_width | Float | Outline thickness. (Default = 1.0`)                          |

#### Return

| Return | Type   | Description                                         |
| ------ | ------ | --------------------------------------------------- |
| style  | Object | An XML element representing a KML style definition. |

#### About a Polygon's Style

Each defined style requires a name that is unique to the KML document being created. Other than **name**, each  of the other `polygon_style()` parameters are optional when creating a polygon style. The default fill color of a polygon is a light transparent blue with a solid yellow outline.
#### Example

A polygon with a custom style applied.

```python
# Define a custom purple polygon style
poly_style = kmlb.polygon_style('Purple Polygon', ('#aaaaff', 60), ('#5500ff', 100), 4)

# Polygon arguments
outer_ring = [[-71.052336,42.359485,0],
              [-71.052333,42.359422,0],
              [-71.052153,42.358787,0],
              [-71.052110,42.358758,0],
              [-71.052049,42.358746,0],
              [-71.051735,42.358797,0],
              [-71.051664,42.358840,0],
              [-71.051658,42.358890,0],
              [-71.051837,42.359527,0],
              [-71.051865,42.359551,0],
              [-71.051915,42.359569,0],
              [-71.052288,42.359514,0],
              [-71.052336,42.359485,0]]

inner_ring = [[-71.052012,42.358864,0],
              [-71.051735,42.358910,0],
              [-71.051796,42.359109,0],
              [-71.052071,42.359065,0],
              [-71.052012,42.358864,0]]

coords = [outer_ring, inner_ring]

name = 'Rings Fountain on the Greenway'
attribute_titles = ['City', 'Park']
attributes = ['Boston', 'Greenway']

# Define the polygon
placemark = kmlb.polygon(coords, name, attribute_titles, attributes, style_to_use='Purple Polygon')
```

## Folder Function

### Create a Folder

Create a folder to hold loose KML geometry elements or other folders.

`folder()`

```python
folder(name, loose_items, description='', collapsed=True, hidden=True)
```

#### Parameters:

##### Required Parameters

| Parameter   | Type   | Description                                         |
| :---------- | :----- | :-------------------------------------------------- |
| name        | String | The name of the folder to be created.               |
| loose_items | List   | A list of loose items to include in the new folder. |

##### Optional Parameters

The default fill color of a polygon is a light transparent blue with a solid yellow outline.

| Parameter   | Type    | Description                                                  |
| ----------- | ------- | ------------------------------------------------------------ |
| description | String  | A small body of descriptive text for the folder.             |
| collapsed   | Bool    | Sets the folder to either be open or collapsed by default.  `False` = Folder is open/expanded. (Default = `True`) |
| hidden      | Bool    | Sets the visibility of a folder and its contents. A folder's visibility is ultimately determined by the visibility of the contents within. The default is to have folders set to hidden so that empty folders are not visible. If an item gets added to a folder and that item is set to be visible, the containing folder will become visible as well - even if the folder set to hidden. (Default = `True`) |
| camera      | Element | A KML 'LookAt' element. (Default = `None`)                   |

#### Return

| Return     | Type   | Description                               |
| ---------- | ------ | ----------------------------------------- |
| new_folder | Object | An XML element representing a KML folder. |

### Example

Create a folder to hold a point and line.

```python

# Defining the point's arguments ahead of defining the point
pt_ coords = [-71.053568, 42.359053, 151]
pt_name = 'Custom House Tower'
pt_headers = ['City', 'Building', 'Height (M)']
pt_attributes = ['Boston', 'Custom House Tower', '151']

# Define point
pt = kmlb.point(pt_coords, name, pt_headers, pt_attributes, 'RTG')

# Define a polyline that marks the path from Boston's Custom House Tower to the Boston Aquarium
line_coords = [[-71.053568, 42.359053, 0],
               [-71.053266, 42.359099, 0],
               [-71.053289, 42.359289, 0],
               [-71.050779, 42.359672, 0],
               [-71.050784, 42.359200, 0],
               [-71.050429, 42.359002, 0],
               [-71.049882, 42.359063, 0]]

ln_name = 'Path to Aquarium'
lm_headers = ['City', 'Starting Point', 'Ending Point']
ln_attributes = ['Boston', 'Custom House Tower', 'Boston Aquarium']

# Define line
line = kmlb.line(line_coords, ln_name, ln_headers, ln_attributes)

# Create folder
f = kmlb.folder('Boston Path', [pt, line], 'Point & Line')
```

## Look At Function

### Create a 'LookAt' Element

Create a folder to hold loose KLM geometry elements or other folders.

`look_at()`

```python
look_at(coords, distance, azimuth, tilt, altitude_mode="ABS")
```

When using the `look_at()` function, the coordinates define a point (in 3D space) that the camera will be focused on. Distance is how far back from that point the camera will be. Azimuth is the horizontal angle from the camera to the point. Tilt is the camera's vertical angle away from nadir towards the point.

#### Parameters:

##### Required Parameters

| Parameter | Type  | Description                                                  |
| :-------- | :---- | :----------------------------------------------------------- |
| coords    | List  | A coordinate set: `[X, Y, Z]`                                |
| distance  | Float | Camera distance in meters from the point specified by 'coords'. |
| azimuth   | Float | The direction that camera will face in degrees from 0-360.   |
| tilt      | Float | The tilt of the camera towards the object. Values range from 0 to 90 degrees. A value of 0 degrees indicates viewing from directly above. A value of 90 degrees indicates viewing along the horizon. |

##### Optional Parameters

The default fill color of a polygon is a light transparent blue with a solid yellow outline.

| Parameter     | Type   | Description                                                  |
| ------------- | ------ | ------------------------------------------------------------ |
| altitude_mode | String | An abbreviated altitude mode ('CTG', 'RTG', 'ABS') (Default = 'ABS'). |

#### Return

| Return | Type    | Description            |
| ------ | ------- | ---------------------- |
| lookat | Element | A KML 'LookAt' element |

### Example

Create a 'LookAt' element

```python
# Defining the point's arguments ahead of defining the point
pt_ coords = [-71.053568, 42.359053, 151]
pt_name = 'Custom House Tower'
pt_headers = ['City', 'Building', 'Height (M)']
pt_attributes = ['Boston', 'Custom House Tower', '151']

# Define a camera angle for point
pt_camera = kmlb.look_at(coords, 210, 50, 100, 'RTG')

# Define point with camera angle
pt = kmlb.point(pt_coords, name, pt_headers, pt_attributes, 'RTG', camera=pt_camera)
```

## 

## Creating a KML

### KML

Create a folder to hold loose KLM geometry elements or other folders.

`kml()`

```python
kml(name, features, path, description='', styles=None, collapsed=True)
```

#### Parameters:

##### Required Parameters

| Parameter | Type   | Description                                                  |
| :-------- | :----- | :----------------------------------------------------------- |
| name      | String | The name of the KML. Note: this is not the KML's file name, but rather the name that will appear within the map. |
| features  | List   | A list of feature to be written to the KML. The list of features can include points, lines, polygons, and folders. |
| path      | String | The path to the folder where the KML file will be written to. Necessary folders will be created of they do not exist. The KML's file name is defined in the path. Note: The file path should end `.kml` |

##### Optional Parameters

The default fill color of a polygon is a light transparent blue with a solid yellow outline.

| Parameter   | Type    | Description                                                  |
| ----------- | ------- | ------------------------------------------------------------ |
| description | String  | A small body of descriptive text for the KML file.           |
| styles      | List    | A list of styles to be written to and used within the KML.   |
| collapsed   | Bool    | Sets the root KML folder to either be open or collapsed by default.  `False` = Folder is open/expanded. (Default = `True`) |
| camera      | Element | A KML 'LookAt' element. (Default = `None`)                   |

#### Return

| Return | Type | Description                             |
| ------ | ---- | --------------------------------------- |
| ---    | ---  | This function does not return anything. |

# FULL EXAMPLE

Bringing Everything together to write a KML file.

```python
import kmlb

# DEFINING STYLES

# Define red triangle point style
pt_style = kmlb.point_style('Red Triangle',  # Point style name
                            'http://maps.google.com/mapfiles/kml/shapes/triangle.png',  # Icon to mark point with
                            ('#ff0000', 100),  # Icon color
                            1.0)  # Icon scale

# Define a yellow line style
ln_style = kmlb.line_style('Yellow Line', ('#fcce02', 100))

# Define purple polygon style
poly_style = kmlb.polygon_style('Purple Polygon', ('#aaaaff', 60), ('#5500ff', 100), 4)

# CREATING A POINT
coords = [-71.053568, 42.359053, 151]
name = 'Custom House Tower'
attribute_titles = ['City', 'Building', 'Height (M)']
attributes = ['Boston', 'Custom House Tower', '151']

# Define a camera angle for point
pt_camera = kmlb.look_at(coords, 100, 210, 50, 'RTG')

clock_tower = kmlb.point(coords, name, attribute_titles, attributes, 'RTG', 'Red Triangle', pt_camera)

# SEARCHING A POI
aquarium = kmlb.search_poi("New England Aquarium")

# CREATING A LINE
coords = [[-71.053266, 42.359099, 0],
          [-71.053311, 42.359285, 0],
          [-71.050779, 42.359672, 0],
          [-71.050784, 42.359200, 0],
          [-71.050429, 42.359002, 0],
          [-71.049882, 42.359063, 0]]

name = 'Path to Aquarium'
attribute_titles = ['City', 'Starting Point', 'Ending Point']
attributes = ['Boston', 'Custom House Tower', 'Boston Aquarium']

walking_path = kmlb.line(coords, name, attribute_titles, attributes, style_to_use='Yellow Line')

# CREATING A POLYGON
outer_ring = [[-71.052336, 42.359485, 0],
              [-71.052333, 42.359422, 0],
              [-71.052153, 42.358787, 0],
              [-71.052110, 42.358758, 0],
              [-71.052049, 42.358746, 0],
              [-71.051735, 42.358797, 0],
              [-71.051664, 42.358840, 0],
              [-71.051658, 42.358890, 0],
              [-71.051837, 42.359527, 0],
              [-71.051865, 42.359551, 0],
              [-71.051915, 42.359569, 0],
              [-71.052288, 42.359514, 0],
              [-71.052336, 42.359485, 0]]

inner_ring = [[-71.052012, 42.358864, 0],
              [-71.051735, 42.358910, 0],
              [-71.051796, 42.359109, 0],
              [-71.052071, 42.359065, 0],
              [-71.052012, 42.358864, 0]]

coords = [outer_ring, inner_ring]

name = 'Rings Fountain on the Greenway'
attribute_titles = ['City', 'Park']
attributes = ['Boston', 'Greenway']

greenway_park = kmlb.polygon(coords, name, attribute_titles, attributes, style_to_use='Purple Polygon')

# ADD GEOMETRIES TO FOLDER
f = kmlb.folder('Boston Shapes', [clock_tower, aquarium, walking_path, greenway_park], 'Sample Shapes')

# WRTIE KML FILE
kmlb.kml('Created with KMLB',  # KML name
         [f],  # Features (Folder containing shapes)
         r'C:\Users\UserName\Desktop\KMLB_Tutorial.kml',  # Export path
         'KML Tutorial Shapes',  # KML Description
         [pt_style, ln_style, poly_style]  # Custom styles
         )

```
<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Tutorial</div>
<h2 class="kmlb-hero__title">Build a Boston KML</h2>
<p class="kmlb-hero__sub">Map a few landmarks around Boston's waterfront in plain Python, then write it to a <code>.kml</code>. Couldn't be easier.</p>
</div>

You only need kmlb (no other dependencies):

```shell
pip install kmlb
```

!!! note
    Throughout, coordinates are `[x, y, z]` or `[longitude, latitude, elevation]`
    and elevation is in meters. Elevation is optional. Pass `[longitude, latitude]`
    and it defaults to `0`. A zero elevation sits on the ground under the default
    `z_mode="CTG"`.

!!! note
    Colors accept a palette name (`"red"`), a hex string, or a `(color, opacity)`
    pair; icons accept a shorthand (`"triangle"`, `"red-paddle"`) or a full URL. Skip
    `style_to_use` entirely and a feature still gets a tidy default style.

## Define reusable styles

Styles are defined once, given a name, and then referenced by that name from
features. We'll make a red triangle for points, a yellow line, and a translucent
purple fill for polygons.

```python
import kmlb

pt_style = kmlb.point_style(
    "redTriangle",
    icon="triangle",
    color="red",
    scale=1.0,
)
line_style = kmlb.line_style("yellowLine", color="gold", width=4)
poly_style = kmlb.polygon_style(
    "purpleFill",
    fill_color=("#aaaaff", 60),
    outline_color="purple",
    outline_width=4,
)
```

## Place the Custom House Tower in 3D

The Custom House Tower is about 151&nbsp;m tall, so we give the point an elevation
and use `z_mode="RTG"` (relative to ground) to lift it. A `look_at` camera
sets the default view, and the attributes show up in the placemark's info balloon.

```python
# [lon, lat, elev] in meters. Here elevation is set, and RTG lifts it off the ground.
tower_coords = [-71.053568, 42.359053, 151]

tower_view = kmlb.look_at(
    tower_coords, distance=100, azimuth=210, tilt=50, z_mode="RTG"
)

tower = kmlb.point(
    tower_coords,
    "Custom House Tower",
    headers=["City", "Building", "Height (m)"],
    attrs=["Boston", "Custom House Tower", 151],
    z_mode="RTG",
    style_to_use="redTriangle",
    cam=tower_view,
)
```

!!! note
    Optional arguments such as `cam`, `style_to_use`, and `z_mode` are
    keyword-only and must be passed by name. Only the required arguments (here the
    coordinates and name) are positional.

## Add a landmark by search

When you don't have coordinates, let Google&nbsp;Earth find the place.
`search_poi` stores the search text as an address; Earth geocodes it when the
file is opened.

```python
aquarium = kmlb.search_poi("New England Aquarium")
```

## Draw a walking path

A line is just an ordered list of coordinates. This one traces a path from the
tower toward the waterfront.

```python
# Each vertex is [lon, lat]. Elevation is omitted here, so it defaults to 0 (ground).
path = kmlb.line(
    [[-71.053266, 42.359099],
     [-71.053311, 42.359285],
     [-71.050779, 42.359672],
     [-71.050784, 42.359200],
     [-71.050429, 42.359002],
     [-71.049882, 42.359063]],
    "Path to Aquarium",
    headers=["City", "From", "To"],
    attrs=["Boston", "Custom House Tower", "Aquarium"],
    style_to_use="yellowLine",
)
```

## Outline a polygon with a hole

A polygon is a list of rings. The first ring is the outer boundary; any
additional rings are holes. Here, the Rings Fountain plaza on the Greenway, with
its central courtyard cut out.

```python
# Ground-level rings use [lon, lat]. Elevation defaults to 0.
outer_ring = [[-71.052336, 42.359485], [-71.052333, 42.359422],
              [-71.052153, 42.358787], [-71.052110, 42.358758],
              [-71.052049, 42.358746], [-71.051735, 42.358797],
              [-71.051664, 42.358840], [-71.051658, 42.358890],
              [-71.051837, 42.359527], [-71.051865, 42.359551],
              [-71.051915, 42.359569], [-71.052288, 42.359514],
              [-71.052336, 42.359485]]

inner_ring = [[-71.052012, 42.358864], [-71.051735, 42.358910],
              [-71.051796, 42.359109], [-71.052071, 42.359065],
              [-71.052012, 42.358864]]

fountain = kmlb.polygon(
    [outer_ring, inner_ring],
    "Rings Fountain on the Greenway",
    headers=["City", "Park"],
    attrs=["Boston", "Rose Kennedy Greenway"],
    style_to_use="purpleFill",
)
```

## Group the features and write the file

Drop the features into a folder to keep Google&nbsp;Earth's sidebar tidy, then
hand everything to `kml`. Passing `path` writes the `.kml` (and returns the
string); remember to include the styles the features reference.

```python
boston = kmlb.folder(
    "Downtown Boston",
    [tower, aquarium, path, fountain],
    desc="A few features around Boston's waterfront.",
)

kmlb.kml(
    "Boston with kmlb",
    [boston],
    path="boston.kml",
    styles=[pt_style, line_style, poly_style],
)
```

Open `boston.kml` in [Google&nbsp;Earth](https://earth.google.com/) and you'll
land on the Custom House Tower, with the path, fountain, and the searched
aquarium nearby.

## The complete script

```python
import kmlb

# 1. Styles
pt_style = kmlb.point_style(
    "redTriangle",
    icon="triangle",
    color="red",
    scale=1.0,
)
line_style = kmlb.line_style("yellowLine", color="gold", width=4)
poly_style = kmlb.polygon_style(
    "purpleFill",
    fill_color=("#aaaaff", 60),
    outline_color="purple",
    outline_width=4,
)

# 2. Custom House Tower (3D point + camera)
tower_coords = [-71.053568, 42.359053, 151]
tower_view = kmlb.look_at(tower_coords, distance=100, azimuth=210, tilt=50, z_mode="RTG")
tower = kmlb.point(
    tower_coords, "Custom House Tower",
    headers=["City", "Building", "Height (m)"],
    attrs=["Boston", "Custom House Tower", 151],
    z_mode="RTG", style_to_use="redTriangle", cam=tower_view,
)

# 3. Aquarium (by search)
aquarium = kmlb.search_poi("New England Aquarium")

# 4. Walking path
path = kmlb.line(
    [[-71.053266, 42.359099], [-71.053311, 42.359285],
     [-71.050779, 42.359672], [-71.050784, 42.359200],
     [-71.050429, 42.359002], [-71.049882, 42.359063]],
    "Path to Aquarium",
    headers=["City", "From", "To"],
    attrs=["Boston", "Custom House Tower", "Aquarium"],
    style_to_use="yellowLine",
)

# 5. Fountain polygon (with a hole)
outer_ring = [[-71.052336, 42.359485], [-71.052333, 42.359422],
              [-71.052153, 42.358787], [-71.052110, 42.358758],
              [-71.052049, 42.358746], [-71.051735, 42.358797],
              [-71.051664, 42.358840], [-71.051658, 42.358890],
              [-71.051837, 42.359527], [-71.051865, 42.359551],
              [-71.051915, 42.359569], [-71.052288, 42.359514],
              [-71.052336, 42.359485]]

inner_ring = [[-71.052012, 42.358864], [-71.051735, 42.358910],
              [-71.051796, 42.359109], [-71.052071, 42.359065],
              [-71.052012, 42.358864]]

fountain = kmlb.polygon(
    [outer_ring, inner_ring], "Rings Fountain on the Greenway",
    headers=["City", "Park"], attrs=["Boston", "Rose Kennedy Greenway"],
    style_to_use="purpleFill",
)

# 6. Folder + write
boston = kmlb.folder(
    "Downtown Boston", [tower, aquarium, path, fountain],
    desc="A few features around Boston's waterfront.",
)
kmlb.kml("Boston with kmlb", [boston], path="boston.kml",
         styles=[pt_style, line_style, poly_style])
```
<br><br><br><br><br>
Shapes
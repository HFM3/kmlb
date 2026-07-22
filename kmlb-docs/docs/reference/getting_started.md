<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Getting started</h2>
<p class="kmlb-hero__sub">From a single point to the whole library, one call at a time.</p>
</div>

## Install

kmlb is published on PyPI and has no third-party dependencies.
It runs on **Python 3.9+** and is built entirely on the standard Python library.
The files it writes are standard `.kml` documents. Open them in
[Google&nbsp;Earth](https://earth.google.com/).

```shell
pip install kmlb
```



## Quick start

Every feature is one Python call that returns an XML element. Create a feature,
bundle it into a document, and write the file. Here is the whole flow with a
single point:

```python
import kmlb

# Create a point
fountain = kmlb.point([-71.051904, 42.358988, 0], "Rings Fountain")

# Write it to a KML file
kmlb.kml(
    "Boston Fountain",                  # document name
    [fountain],                         # features to include
    path="folder/boston_fountain.kml",  # where to write it
)
```

Styles, more feature types, and folders build on that same shape. A fuller
example adds a styled point and a polygon with a hole:

```python
import kmlb

# A reusable point style and a styled marker
city = kmlb.point_style("city", icon="circle", color=("#ff8800", 100), scale=1.4)
boston = kmlb.point([-71.0589, 42.3601], "Boston", style_to_use="city")

# A polygon style controls both the fill and the outline stroke
fill = kmlb.polygon_style("fill", fill_color=("#03cafc", 40),
                          outline_color=("#03cafc", 100), outline_width=2)

# A polygon with a hole (outer ring first, then a hole)
ring = [[-71.060, 42.358], [-71.052, 42.358], [-71.052, 42.363], [-71.060, 42.358]]
hole = [[-71.057, 42.359], [-71.054, 42.359], [-71.054, 42.361], [-71.057, 42.359]]
block = kmlb.polygon([ring, hole], "Block", style_to_use="fill")

# Assemble the features and styles into a document and write it to disk
kmlb.kml("My Places", [boston, block], styles=[city, fill], path="folder/my_places.kml")
```

!!! tip "Next step"
    For a complete, real-world build, follow the [Boston waterfront tutorial](../tutorial.md).

## Example use

### Mapping a POI or an address

```python
import kmlb

# CREATE A POINT FROM A POI
bos_common = kmlb.search_poi("Boston Common, Boston, MA")

# CREATE A POINT FROM AN ADDRESS
ss = kmlb.search_poi("700 Atlantic Avenue, Boston, MA", name="South Station")

# WRITE KML FILE
kmlb.kml(
    "Boston Landmarks",          # KML name
    [bos_common, ss],            # Features
    path="folder/boston_landmarks.kml"  # Export path
)
```

### Creating a customized KML file

```python
import kmlb

# DEFINE A STYLE
pt_style = kmlb.point_style(
    "Red Triangle",                # Point style name
    icon="triangle",               # Icon (built-in shorthand)
    color=("#ff0000", 100),        # Icon color (hex, opacity)
    scale=1.0,                     # Icon scale
    label_color=("#ffffff", 100),  # Label color (hex, opacity)
    label_size=1.0,                # Label size
)

# CREATE A POINT
clock_tower = kmlb.point(
    [-71.053568, 42.359053, 151],                   # Coordinates
    "Custom House Tower",                           # Name
    headers=["City", "Building", "Height (M)"],     # Attribute titles
    attrs=["Boston", "Custom House Tower", "151"],  # Attributes
    z_mode="RTG",                                   # Relative To Ground
    style_to_use="Red Triangle",                    # Name of point style defined earlier
)

# WRITE KML FILE
kmlb.kml(
    "Boston Clock Tower",                     # KML name
    [clock_tower],                            # Features to include
    path="folder/boston_clock_tower.kml",     # Export path
    desc="Created with KMLB Python Package",  # KML description
    styles=[pt_style],                        # Styles to include
)
```

### A 3D scene

The `kmlb.shapes` module adds higher-level geometry on top of the core builders.
This scene rings a soccer ball with eight colored pyramids (bases cycling from 3 to
6 sides), all resting on the ground with `z_mode="RTG"` and placed around one center
with `destination`.

```python
import kmlb
from kmlb import shapes

center = [-71.067507, 42.355289]     # an open stretch of Boston Common

# Colors are (hex, opacity) pairs; opacity runs 0 (clear) to 100 (solid).
# One bright color per pyramid, stepping around the color wheel.
rainbow = [
    ("#ff2d2d", 88), ("#ff8c1a", 88), ("#ffe01a", 88), ("#4bd42b", 88),
    ("#1ad6c0", 88), ("#2d7dff", 88), ("#8a4bff", 88), ("#ff45c0", 88),
]

features = []
# A ring of pyramids around the center, one per color.
for i, color in enumerate(rainbow):
    # destination(origin, bearing, meters): 45 degrees apart, 24 m out
    lon, lat = kmlb.destination(center, i * 45, 24)[:2]
    # pyramid(coords, base_radius_m, height_m, sides=...): bases cycle 3, 4, 5, 6
    features.append(shapes.pyramid([lon, lat, 0], 5, 14, sides=3 + i % 4,
                                   color=color,       # fill color (hex, opacity)
                                   z_mode="RTG",      # rest it on the ground
                                   name=f"{3 + i % 4}-sided pyramid"))

# soccer_ball(coords, radius_m); anchor="base" sets it on the ground
features.append(shapes.soccer_ball([center[0], center[1], 0], 7, anchor="base",
                                   z_mode="RTG", name="Soccer ball"))

# look_at(coords, distance_m, azimuth, tilt): a three-quarter aerial view
view = kmlb.look_at([center[0], center[1], 0], 130, 35, 55, z_mode="RTG")

kmlb.kml("Pyramids and a soccer ball", features, path="pyramids.kml", cam=view)
```

[Download pyramids_soccer_ball.kml](../assets/pyramids_soccer_ball.kml){ .md-button .kmlb-download download="pyramids_soccer_ball.kml" }

!!! tip "More shapes"
    See the [Shapes reference](shapes.md) for every 2D builder and 3D solid, with
    the orientation and anchoring options used here.

## Altitude modes

The `z_mode` argument on `point`, `line`, and `polygon` features sets how the `z`
(elevation) value of a coordinate is interpreted. KMLB uses short codes that
expand to KML `<altitudeMode>` values. The two sea-floor codes are Google
`gx:` extensions, useful for ocean and bathymetry work, and are written as
`<gx:altitudeMode>`. See Google's
[KML altitude mode reference](https://developers.google.com/kml/documentation/altitudemode)
for full details.

| Code | KML value | Meaning |
|---|---|---|
| `"CTG"` | `clampToGround` | The default. Any elevation is ignored and the feature is draped on the terrain surface. |
| `"RTG"` | `relativeToGround` | Elevation is measured upward from the ground surface directly below the coordinate. |
| `"ABS"` | `absolute` | Elevation is measured from mean sea level, ignoring the terrain beneath it. |
| `"CSF"` | `clampToSeaFloor` | Any elevation is ignored and the feature is placed on the sea floor. |
| `"RSF"` | `relativeToSeaFloor` | Elevation is measured upward from the sea floor directly below the coordinate. |

!!! note "When elevation is visible"
    Elevation only has a visible effect under `"RTG"`, `"ABS"`, or `"RSF"`. With
    `"CTG"` (the default) or `"CSF"`, the feature sits flush on the ground or sea
    floor no matter its `z` value.

!!! note "Sea-floor modes"
    The sea-floor modes (`"CSF"`, `"RSF"`) are a Google Earth extension. When a
    document uses them, kmlb declares the `xmlns:gx` namespace on the KML root
    automatically.

<br><br><br><br><br>
<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Getting started</h2>
<p class="kmlb-hero__sub">See the whole KMLB library in one quick-start example.</p>
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

Every feature is one Python call that hands back an XML element. Define a style,
attach it to a point, line, or polygon, then bundle everything into a
document. That's the whole flow of the library.

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

!!! note
    For a complete, real-world build, follow the [Boston waterfront tutorial](../tutorial.md).

## Example use

### Writing a basic KML file

```python
import kmlb

# CREATE A POINT
fountain = kmlb.point([-71.051904, 42.358988, 0], "Rings Fountain")

# WRITE KML FILE
kmlb.kml(
    "Boston Fountain",          # KML name
    [fountain],                 # Features
    path="folder/boston_fountain.kml"  # Export path
)
```

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

!!! note
    Elevation only has a visible effect under `"RTG"`, `"ABS"`, or `"RSF"`. With
    `"CTG"` (the default) or `"CSF"`, the feature sits flush on the ground or sea
    floor no matter its `z` value.

!!! note
    The sea-floor modes (`"CSF"`, `"RSF"`) are a Google Earth extension. When a
    document uses them, kmlb declares the `xmlns:gx` namespace on the KML root
    automatically.

<br><br><br><br><br>
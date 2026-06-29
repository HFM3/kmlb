<div align="center">

<img src="kmlb-docs/assets/kmlb-logo.png" alt="kmlb logo" width="230">

<h1>Plain Python KML Builder</h1>

<strong>A straightforward Google&nbsp;Earth KML builder for Python.</strong>

<p>
  <a href="https://pypi.org/project/kmlb/"><img src="https://img.shields.io/pypi/v/kmlb?color=1b8a9b&label=pypi" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-1b8a9b" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-f2a81d" alt="MIT License">
</p>

<p>
  <a href="https://kmlb.dev/">kmlb.dev</a> &nbsp;&bull;&nbsp;
  <a href="https://kmlb.dev/docs/tutorial/">Tutorial</a> &nbsp;&bull;&nbsp;
  <a href="https://pypi.org/project/kmlb/">PyPI</a>
</p>

</div>

---

**Build KMLs in plain Python.**

KMLB is a dependency-free Python library for writing Google Earth KML files. Easily create points, lines, polygons, styles, and folders. 

Name a style, point a feature at it, write the file:

```python
import kmlb

style = kmlb.point_style("city", color="red", icon="triangle")
boston = kmlb.point([-71.0589, 42.3601], "Boston", style_to_use="city")

kmlb.kml("My Places", [boston], styles=[style], path="my_places.kml")
```

Open `my_places.kml` in Google Earth and there is your map. No XML, no dependencies.

```bash
pip install kmlb
```

<p align="center">
  <img src="kmlb-docs/assets/3D%20Buildings.jpg" alt="Orange wireframe building footprints extruded into 3D over Google Earth satellite imagery" width="900">
</p>

<p align="center"><sub>Building footprints extruded into 3D and viewed in Google Earth, built with KMLB polygons.</sub></p>

## The whole library

- **Features:** `point`, `search_poi`, `line`, `polygon`, grouped in `folder`s, written out with `kml`.
- **Easy styling:** `color="red"`, `icon="triangle"`. Skip the style and a feature still looks good.
- **3D:** altitude modes, ground extrusion, and `look_at` camera angles.
- **Geodesy:** `distance` and `bearing` between points, `destination` to offset a point by a bearing and distance (e.g. to draw radial lines and shapes).
- **Shapes and more:** `shapes.wedge` and `networklink_kml` for files that refresh from a URL.

Python 3.9+, standard library only.

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

## Functions

| Function | What it does |
|---|---|
| **Features** | |
| `point` | Point placemark from a `[lon, lat]` (or `[lon, lat, elev]`) coordinate. |
| `search_poi` | Placemark located by an address or search string, geocoded by Google Earth. |
| `line` | Line or polyline from an ordered list of coordinates. |
| `polygon` | Polygon from one or more rings (first ring outer, the rest holes). |
| **Styles** | |
| `point_style` | Reusable point style: icon, color, scale, and label. |
| `line_style` | Reusable line style: color and width. |
| `polygon_style` | Reusable polygon style: fill and outline. |
| **Geodesy (WGS-84)** | |
| `distance` | Distance in meters between two coordinates. |
| `bearing` | Initial bearing in degrees between two coordinates. |
| `destination` | Coordinate reached from an origin along a bearing and distance. |
| **Shapes** | |
| `shapes.wedge` | Pie-wedge (circular sector) polygon, useful for cellular coverage sectors. |
| **Views, documents, and links** | |
| `look_at` | Camera angle and view for a feature or document. |
| `folder` | Group features and other folders together. |
| `kml` | Assemble features and styles into a KML document and write it to disk. |
| `networklink_kml` | Network-link KML that refreshes from a hosted URL. |
| **Color and icon helpers** | |
| `colors` | Named color palette (`colors.RED`, or `color="red"`). |
| `icons` | Built-in marker shorthands (`icon="triangle"`, `"red-paddle"`). |

## Docs

Full reference and a step-by-step Boston tutorial at **[kmlb.dev](https://kmlb.dev/)**.

## Citing kmlb

Using KMLB in research or published work? A citation is appreciated (it is not
required under the MIT license, but documented use builds trust in the tool).
APA, Chicago, and BibTeX formats, kept current with each release, are at
**[kmlb.dev/docs/cite](https://kmlb.dev/docs/cite/)**.

```bibtex
@software{KMLB,
  author  = {Mros, III, Henry F.},
  title   = {KMLB: KML Builder},
  year    = {2026},
  version = {0.1.0},
  url     = {https://pypi.org/project/kmlb/}
}
```

## License

[MIT](pypi_package/LICENSE). Use it anywhere, including commercial work, as long as the
license notice stays.

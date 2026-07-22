<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Shapes</h2>
<p class="kmlb-hero__sub">Higher-level geometry builders: the 2D shapes <code>circle</code>, <code>ellipse</code>, <code>rectangle</code>, <code>ngon</code>, <code>annulus</code>, <code>arc</code>, <code>wedge</code>, <code>ribbon</code>, <code>con_rings</code>, <code>fishnet</code>, <code>hex_grid</code>, and <code>hex_field</code>; the 3D solids <code>cylinder</code>, <code>cone</code>, <code>dome</code>, <code>sphere</code>, <code>cube</code>, <code>pyramid</code>, and <code>soccer_ball</code>; and <code>fresnel_zone</code> (a radio link's 3D Fresnel tube).</p>
</div>

## Sample files

<div class="kmlb-downloads" markdown>
[Download shape_examples.kml](../assets/shape_examples.kml){ .md-button .kmlb-download download="shape_examples.kml" }
</div>

[![Cylinder, cone, dome, and sphere volumes over Boston in Google Earth, built with kmlb shapes](../assets/img/3d-shapes.jpg)](../assets/img/3d-shapes.jpg){ .glightbox .crop-3d }

## 2D shapes

These builders return flat KML geometry composed from the core
[`polygon`](features.md#polygon), [`line`](features.md#line), and
[`folder`](views_export.md#folder) primitives. Unless a `z_mode` is passed, 2D
planar shapes clamp to the ground and follow the terrain, so a 2-element
`[lon, lat]` center works fine. Every builder forwards extra keyword arguments (`z_mode`,
`style_to_use`, `hidden`, `headers`, `attrs`, ...) to its underlying primitive.
Each also fills a default attribute table from its defining parameters (radius,
azimuth, center, and so on); pass explicit `headers`/`attrs` to override it.

### circle

Approximates a circle of a given radius (meters) with a regular polygon of
`steps` vertices projected across the WGS-84 ellipsoid; more `steps` give a
smoother edge.

```python
circle(center, radius, *, steps=48, name="Circle", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center. |
| `radius` | `float` | required | Radius in meters. |
| `steps` | `int` | `48` | Vertices around the circle; more gives a smoother edge. |
| `name` | `str` | `'Circle'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the circle `Polygon`.

!!! failure "Raises"
    `ValueError` if `steps` is less than 3.

```python
# A 37.5 m circle around the Parkman Bandstand on Boston Common.
kmlb.shapes.circle([-71.065510, 42.354345, 0], 37.5)
```

### ellipse

Builds an ellipse from its two semi-axis lengths (meters) and an orientation. At
`orient=0` the major axis runs north-south; increasing `orient` rotates it
clockwise from true north.

```python
ellipse(center, semi_major, semi_minor, *, orient=0.0, steps=64,
        name="Ellipse", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center. |
| `semi_major` | `float` | required | Half the long-axis length, in meters. |
| `semi_minor` | `float` | required | Half the short-axis length, in meters. |
| `orient` | `float` | `0.0` | Clockwise rotation of the major axis, degrees from true north. |
| `steps` | `int` | `64` | Vertices around the ellipse. |
| `name` | `str` | `'Ellipse'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the ellipse `Polygon`.

!!! failure "Raises"
    `ValueError` if `steps` is less than 3.

```python
# A ~1200 m x 660 m ellipse off Point Shirley / Yirrell Beach, Winthrop, tilted 18 deg west of north.
kmlb.shapes.ellipse([-70.964514, 42.360287, 0], 600, 330, orient=-18)
```

### rectangle

Builds a rectangle anchored at `corner`. `azimuth` is the compass bearing (degrees
from true north) of the rectangle's first (`width`) edge running from the corner:
the default `90` runs `width` due east and `height` due south, an upright box, so
`corner` is the upper-left corner. `azimuth=0` points the first edge due north;
increasing `azimuth` turns the whole rectangle clockwise about the corner so it can
line up with a feature that is not north-up (which corner of the box `corner`
represents turns with it). `height` always runs 90 degrees clockwise of `width`.

```python
rectangle(corner, width, height, *, azimuth=90.0, name="Rectangle", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `corner` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` anchor (upper-left corner at the default `azimuth=90`). |
| `width` | `float` | required | Length of the first edge (the one bearing `azimuth`), in meters. |
| `height` | `float` | required | Length of the perpendicular edge (90 degrees clockwise of `width`), in meters. |
| `azimuth` | `float` | `90.0` | Compass bearing of the first (`width`) edge, degrees from true north (`0`=north, `90`=east). Default `90` runs `width` due east. |
| `name` | `str` | `'Rectangle'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the rectangle `Polygon`.

```python
# A ~1260 m x 185 m dock apron on the East Boston waterfront, anchored at its
# north-west corner. Default azimuth=90 runs the width edge due east.
kmlb.shapes.rectangle([-71.029345, 42.341506, 0], 1260, 185)

# The same apron rotated to line up with a quay that bears 110 degrees (its width
# edge now runs east-south-east instead of due east).
kmlb.shapes.rectangle([-71.029345, 42.341506, 0], 1260, 185, azimuth=110)
```

### ngon

Builds a regular polygon of `sides` equal edges, each vertex `radius` meters from
the center. `orient` turns it clockwise; at `orient=0` the first vertex points due
north.

```python
ngon(center, radius, sides, *, orient=0.0, name="Polygon", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center. |
| `radius` | `float` | required | Distance from center to each vertex, in meters. |
| `sides` | `int` | required | Number of sides (3 = triangle, 5 = pentagon, 6 = hexagon). |
| `orient` | `float` | `0.0` | Clockwise rotation of the first vertex, degrees from true north. |
| `name` | `str` | `'Ngon'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the regular-polygon `Polygon`.

!!! failure "Raises"
    `ValueError` if `sides` is less than 3.

```python
# A pentagon over Fort Independence, the five-bastioned fort on Castle Island.
kmlb.shapes.ngon([-71.011100, 42.338233, 0], 100, 5)
```

### annulus

Builds a filled ring: an outer circle with a smaller concentric inner circle
punched out as a hole.

```python
annulus(center, inner_radius, outer_radius, *, steps=48, name="Annulus", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center. |
| `inner_radius` | `float` | required | Inner (hole) radius, in meters; must be smaller than `outer_radius`. |
| `outer_radius` | `float` | required | Outer edge radius, in meters. |
| `steps` | `int` | `48` | Vertices around each circle. |
| `name` | `str` | `'Annulus'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing a `Polygon` with one hole.

!!! failure "Raises"
    `ValueError` if `inner_radius` is not smaller than `outer_radius`, or if `steps` is less than 3.

```python
# A 100 m-wide band (inner 160 m, outer 260 m) around Snake Island, Winthrop.
# Radii are given inner first, then outer.
kmlb.shapes.annulus([-70.979528, 42.365842, 0], 160, 260)
```

### arc

Draws a curved path at a fixed radius from a center point, sweeping from
`start_az` to `end_az` (degrees from true north). Returns a line, not a filled sector (use
[`wedge`](#wedge) for a filled sector).

```python
arc(center, radius, start_az, end_az, *, steps=32, name="Arc", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center. |
| `radius` | `float` | required | Arc radius, in meters. |
| `start_az` | `float` | required | Starting azimuth, degrees from true north. |
| `end_az` | `float` | required | Ending azimuth, degrees from true north. |
| `steps` | `int` | `32` | Segments along the arc. |
| `name` | `str` | `'Arc'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`line`](features.md#line). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the arc `LineString`.

```python
# A field-of-fire arc for Fort Warren on Georges Island: a 550 m reach sweeping
# the harbor approach from north-east (46 deg) through south-east to south (172 deg).
kmlb.shapes.arc([-70.9285, 42.3199, 0], 550, 46, 172)
```

### wedge

Builds a pie-wedge-shaped polygon: a circular sector centered on a point, opening
toward an azimuth, with a given angular width and radius. The arc is approximated
with `steps` vertices projected across the WGS-84 ellipsoid.

A wedge maps naturally onto a cellular coverage sector, which makes it a handy
way to illustrate cell-tower coverage. The `azimuth` is the direction the antenna
faces, the `width` is the sector's beamwidth, and the `radius` is its reach, so
the shape visualizes sector width, direction, and reach at a glance.

```python
wedge(origin, azimuth, width, radius, *, tilt=0.0, steps=15, name="Wedge", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `origin` | `list[float]` | required | `[lon, lat, elev]` origin of the wedge (where its two straight edges meet). |
| `azimuth` | `float` | required | Direction the center of the arc points, degrees from true north. |
| `width` | `float` | required | Angular width of the wedge, in degrees. |
| `radius` | `float` | required | Length of the wedge's straight edges, in meters. |
| `tilt` | `float` | `0.0` | Elevation tilt of the whole sector, in degrees: `0` is flat on the ground, `-90` points it straight down, `90` straight up. See the note below. |
| `steps` | `int` | `15` | Number of vertices along the arc; more steps give a smoother curve. |
| `name` | `str` | `'Wedge'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon) (e.g. `z_mode`, `style_to_use`, `hidden`, `headers`, `attrs`). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the wedge `Polygon`.

!!! failure "Raises"
    `ValueError` if `steps` is less than 2.

!!! note "Tilt and altitude"
    A tilt lifts the sector off the ground, so it only renders under a
    non-clamped altitude mode. When `tilt` is nonzero and no `z_mode` is given,
    `wedge` selects `'ABS'` (absolute) automatically and treats the center's `z`
    as an absolute (MSL) altitude. Pass an explicit `z_mode` (for example
    `z_mode='RTG'` to measure from the ground) to override.

**Examples**

A wedge opening due east

```python
# A 30°-wide wedge of radius 1 km, opening due east from a center point.
w = kmlb.shapes.wedge([-71.0589, 42.3601, 0], azimuth=90, width=30, radius=1000)
```

An antenna sector with 6° of down-tilt

```python
# The center z is an absolute altitude (antenna height above sea level); the
# sector tilts 6° below horizontal. z_mode defaults to 'ABS' when tilted.
w = kmlb.shapes.wedge([-71.0589, 42.3601, 45], azimuth=90, width=30, radius=1000, tilt=-6)
```

### ribbon

Buffers an open path into a polygon by offsetting each vertex along the bisector
of its turn (a miter join), so the ribbon keeps an even width through bends.
Useful for trails, rail lines, pipelines, and flight corridors. Pass `width` as a
single value for an even width, or as a list (one value per path point) for a
ribbon that widens and narrows along its length, such as a hurricane track's wind
field.

```python
ribbon(path, width, *, name="Ribbon", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `list[list[float]]` | required | Ordered `[lon, lat]` (or `[lon, lat, z]`) vertices, 2 or more. |
| `width` | `float` or `list[float]` | required | Total width in meters: a single value, or one value per path point. |
| `name` | `str` | `'Ribbon'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the ribbon `Polygon`.

!!! failure "Raises"
    `ValueError` if `path` has fewer than 2 points, or if a `width` list's length does not match `path`.

```python
# A 45 m-wide ribbon down a path along the Rose Kennedy Greenway.
path = [
    [-71.051781, 42.358581], [-71.051176, 42.356909],
    [-71.051159, 42.356408], [-71.051254, 42.355748],
    [-71.051645, 42.355150], [-71.051895, 42.354950],
    [-71.053736, 42.353987],
]
kmlb.shapes.ribbon(path, 45)

# A variable-width ribbon: narrow at the ends, wide in the middle.
kmlb.shapes.ribbon(path, [20, 40, 60, 80, 60, 40, 20])
```

### con_rings

Draws one unfilled circle outline per radius and returns them in a folder, so each
ring toggles on its own and carries a Ring/Radius attribute table. Give the radii
explicitly as `radii`, or generate an evenly spaced series with `start`,
`interval`, and `count`.

```python
con_rings(center, radii=None, *, start=None, interval=None, count=None,
          steps=48, name="Concentric Rings", collapsed=True, hidden=False,
          **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center all rings share. |
| `radii` | `list[float]` | `None` | Explicit radius for each ring, in meters. If `None` (the default), built from `start`/`interval`/`count`. |
| `start` | `float` | `None` | Innermost ring radius, in meters (generator form). |
| `interval` | `float` | `None` | Spacing between successive rings, in meters (generator form). |
| `count` | `int` | `None` | Number of rings to generate (generator form). |
| `steps` | `int` | `48` | Vertices around each ring. |
| `name` | `str` | `'Concentric Rings'` | Folder name. |
| `collapsed` | `bool` | `True` | Whether the folder starts collapsed in the places panel. |
| `hidden` | `bool` | `False` | Whether the folder starts hidden. |
| `**kwargs` | | | Any keyword argument accepted by [`line`](features.md#line); applied to every ring. |

!!! success "Returns"
    `Element`: a KML `Folder` of line rings.

!!! failure "Raises"
    `ValueError` if neither `radii` nor all of `start`, `interval`, and `count` are given, or if `steps` is less than 3.

```python
# Five range rings at 200 m intervals (200 m out to 1000 m) around Boston Light.
kmlb.shapes.con_rings([-70.890110, 42.327942, 0], start=200, interval=200, count=5)

# The same rings from an explicit list.
kmlb.shapes.con_rings([-70.890110, 42.327942, 0], [200, 400, 600, 800, 1000])
```

### fishnet

Tiles a `cols` by `rows` grid of rectangular cells starting from an upper-left
`corner` and returns them in a folder; cells march along the top edge (column) and
90 degrees clockwise of it (row). Pass `cell_dim` as one value for square cells, or
`[x, y]` for rectangular cells (`x` along the columns, `y` along the rows).
`azimuth` is the compass bearing of the top (column) edge: the default `90` runs
columns due east and rows due south. Increasing `azimuth` turns the whole grid
clockwise about the corner. Every cell is clickable: pass `ids` to name the cells,
and each carries an ID/Row/Column attribute table.

```python
fishnet(corner, cell_dim, cols, rows, *, azimuth=90.0, ids=None, labels=False,
        label_color=None, name="Fishnet", collapsed=True, hidden=False, **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `corner` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` anchor (upper-left corner at the default `azimuth=90`). |
| `cell_dim` | `float` or `list[float]` | required | One value (square cells) or `[x, y]` (rectangular: `x` along the columns, `y` along the rows), in meters. |
| `cols` | `int` | required | Number of columns. |
| `rows` | `int` | required | Number of rows. |
| `azimuth` | `float` | `90.0` | Compass bearing of the top (column) edge, degrees from true north (`0`=north, `90`=east). Default `90` runs columns due east. |
| `ids` | `list` | `None` | Cell IDs, as a flat row-major list (`rows * cols` values) or a nested `rows` by `cols` list. Each names its cell and appears in its attribute table. When omitted, cells are named `r{row}c{col}`. |
| `labels` | `bool` | `False` | `True` puts the cells in a `Cells` subfolder and adds a sibling `Labels` subfolder with a text label at each cell's centroid (named by its ID), so each toggles on its own. |
| `label_color` | `tuple` | `None` | Color `(hex, opacity)` for the label dots. When `None`, they match the cells' outline color. |
| `name` | `str` | `'Fishnet'` | Folder name. |
| `collapsed` | `bool` | `True` | Whether the folder starts collapsed in the places panel. |
| `hidden` | `bool` | `False` | Whether the folder starts hidden. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon); applied to every cell. |

!!! success "Returns"
    `Element`: a KML `Folder` of polygon cells.

!!! failure "Raises"
    `ValueError` if `cols` or `rows` is less than 1.

!!! note "Cell order for `ids`"
    Cells are built row by row from the corner, so a flat `ids` list is read in
    that same order: the first row fills left to right along the top edge (columns
    `0, 1, ... cols-1`), then the next row down, and so on. A flat list is therefore
    `[r0c0, r0c1, ..., r0c(cols-1), r1c0, ...]` (index `row*cols + col`); a nested
    list is indexed `ids[row][col]`. Every cell also carries `Row` and `Column`
    values in its attribute table, so placement can be confirmed in Google Earth.

```python
# A 20 m fishnet filling a rotated (diamond) parking lot in South Boston, anchored
# at the lot's north corner and rotated so the cells line up with the lot edge.
lot = [
    [-71.05038153, 42.34324057],   # west corner
    [-71.04865971, 42.34210311],   # south corner
    [-71.04721297, 42.34333098],   # east corner
    [-71.04895166, 42.34446722],   # north corner
]
cell = 20
cols = rows = max(1, round(kmlb.distance(lot[1], lot[2]) / cell))   # 9
# azimuth is the column-edge bearing, so aim it straight down the lot's top edge.
azimuth = kmlb.bearing(lot[3], lot[2])                              # north -> east corner
kmlb.shapes.fishnet(lot[3] + [0], cell, cols, rows, azimuth=azimuth)

# Rectangular 30 m x 20 m cells instead, with IDs for clickable, labelled cells.
# The flat list fills row by row: A1/A2/A3 across the top, then B1/B2/B3 below.
kmlb.shapes.fishnet(lot[3] + [0], [30, 20], 3, 2, azimuth=azimuth,
                    ids=["A1", "A2", "A3", "B1", "B2", "B3"])

# labels=True adds a "Labels" subfolder with each cell's ID shown on the map.
kmlb.shapes.fishnet(lot[3] + [0], cell, cols, rows, azimuth=azimuth, labels=True)
```

### hex_grid

Tiles a `cols` by `rows` lattice of flat-top hexagons starting from an upper-left
`corner`, each of radius `cell` meters (center to vertex), interlocked edge to
edge. `azimuth` is the compass bearing of the column direction (default `90` runs
columns due east); increasing it turns the whole grid clockwise about the corner.
The rotation is rigid, so the hexagons stay tessellated at any azimuth. Cells are
clickable and ID-able just like `fishnet`.

```python
hex_grid(corner, cell, cols, rows, *, azimuth=90.0, ids=None, labels=False,
         label_color=None, name="Hex Grid", collapsed=True, hidden=False, **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `corner` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` anchor (upper-left corner at the default `azimuth=90`). |
| `cell` | `float` | required | Hexagon radius (center to vertex), in meters. |
| `cols` | `int` | required | Number of columns. |
| `rows` | `int` | required | Number of rows. |
| `azimuth` | `float` | `90.0` | Compass bearing of the column direction, degrees from true north (`0`=north, `90`=east). Default `90` runs columns due east. |
| `ids` | `list` | `None` | Cell IDs, flat row-major or nested `rows` by `cols`. When omitted, cells are named `r{row}c{col}`. |
| `labels` | `bool` | `False` | `True` puts the cells in a `Cells` subfolder and adds a sibling `Labels` subfolder with a text label at each cell's centroid (named by its ID), so each toggles on its own. |
| `label_color` | `tuple` | `None` | Color `(hex, opacity)` for the label dots. When `None`, they match the cells' outline color. |
| `name` | `str` | `'Hex Grid'` | Folder name. |
| `collapsed` | `bool` | `True` | Whether the folder starts collapsed in the places panel. |
| `hidden` | `bool` | `False` | Whether the folder starts hidden. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon); applied to every cell. |

!!! success "Returns"
    `Element`: a KML `Folder` of polygon cells.

!!! failure "Raises"
    `ValueError` if `cols` or `rows` is less than 1.

!!! note "Cell order for `ids`"
    Cells are built row by row from the corner, so a flat `ids` list is read in
    that same order: the first row fills left to right (columns `0, 1, ... cols-1`),
    then the next row down, and so on. A flat list is therefore
    `[r0c0, r0c1, ..., r0c(cols-1), r1c0, ...]` (index `row*cols + col`); a nested
    list is indexed `ids[row][col]`. Every cell also carries `Row` and `Column`
    values in its attribute table, so placement can be confirmed in Google Earth.

```python
# A hexagonal grid filling the same rotated South Boston parking lot as the fishnet
# example above, anchored at its north corner with columns bearing 131.38 degrees.
kmlb.shapes.hex_grid([-71.048952, 42.344467, 0], 12, 10, 9, azimuth=131.38)

# labels=True adds a "Labels" subfolder with each cell's ID shown on the map.
kmlb.shapes.hex_grid([-71.048952, 42.344467, 0], 12, 10, 9, azimuth=131.38, labels=True)
```

### hex_field

Tiles a hexagon-shaped cluster of flat-top hexagons: a central cell surrounded by
`rings` rings of hexagons, so the whole cluster is itself a hexagon. Each hexagon
has a radius of `cell` meters (center to vertex) and the cells interlock edge to
edge. The total cell count is `1 + 3 * rings * (rings + 1)` (7 at `rings=1`, 19 at
`rings=2`, 37 at `rings=3`). Cells are numbered `1, 2, 3, ...` in a spiral outward
from the center, and each carries an ID/Ring attribute table.

```python
hex_field(center, cell, rings, *, azimuth=90.0, ids=None, labels=False,
          label_color=None, name="Hex Field", collapsed=True, hidden=False, **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat]` or `[lon, lat, z]` center hexagon. |
| `cell` | `float` | required | Hexagon radius (center to vertex), in meters. |
| `rings` | `int` | required | Number of rings of hexagons around the center hexagon. |
| `azimuth` | `float` | `90.0` | Clockwise rotation of the whole cluster about the center, degrees from true north. Default `90` is the base orientation; the rotation stays tessellated at any angle. |
| `ids` | `list` | `None` | Cell labels as a flat list of `1 + 3*rings*(rings+1)` values in cell order (cell 1 the center, then ring by ring); `ids[k]` names cell `k+1`. When omitted, cells are named `1`, `2`, `3`, ... |
| `labels` | `bool` | `False` | `True` puts the cells in a `Cells` subfolder and adds a sibling `Labels` subfolder with a text label at each cell's centroid (named by its ID), so each toggles on its own. |
| `label_color` | `tuple` | `None` | Color `(hex, opacity)` for the label dots. When `None`, they match the cells' outline color. |
| `name` | `str` | `'Hex Field'` | Folder name. |
| `collapsed` | `bool` | `True` | Whether the folder starts collapsed in the places panel. |
| `hidden` | `bool` | `False` | Whether the folder starts hidden. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon); applied to every cell. |

!!! success "Returns"
    `Element`: a KML `Folder` of polygon cells.

!!! failure "Raises"
    `ValueError` if `rings` is less than 1, or if `ids` is given with the wrong length.

!!! note "Cell numbering"
    Cells are numbered in a spiral outward from the center: cell `1` is the center,
    then the spiral winds through each ring (cells `2`-`7` are the first ring,
    `8`-`19` the second, and so on), so consecutive numbers are always neighbours. A
    cell's `Ring` value (in its attribute table) is its ring number, `0` for the
    center. Pass `ids` as a flat list in that same order to relabel the cells.

```python
# Three rings of 60 m hexes; cells are auto-numbered 1..37 outward from the center.
kmlb.shapes.hex_field([-71.066, 42.355, 0], 60, 3)

# Label the 7 cells of a one-ring cluster (center first, then around the ring).
kmlb.shapes.hex_field([-71.066, 42.355, 0], 60, 1,
                      ids=["hub", "A", "B", "C", "D", "E", "F"])

# labels=True adds a "Labels" subfolder showing each cell's number on the map.
kmlb.shapes.hex_field([-71.066, 42.355, 0], 60, 3, labels=True)
```

### Example: a 2D scene

Every 2D builder returns an ordinary KML element, so a scene is just a list of
them written with `kml`. This bundles a set of 2D builders into a single file,
each a plain one-line call spread across Boston Harbor.

```python
import kmlb
from kmlb import shapes

# a path for the ribbon to follow (Rose Kennedy Greenway)
greenway = [
    [-71.051781, 42.358581], [-71.051254, 42.355748],
    [-71.051895, 42.354950], [-71.053736, 42.353987],
]

features = [
    shapes.circle([-71.065510, 42.354345, 0], 37.5),                        # Parkman Bandstand
    shapes.ellipse([-70.964514, 42.360287, 0], 600, 330, orient=-18),       # Point Shirley
    shapes.rectangle([-71.029345, 42.341506, 0], 1260, 185),                # East Boston dock
    shapes.ngon([-71.011100, 42.338233, 0], 100, 5),                        # Fort Independence
    shapes.annulus([-70.979528, 42.365842, 0], 160, 260),                   # Snake Island
    shapes.arc([-70.928500, 42.319900, 0], 550, 46, 172),                   # Fort Warren
    shapes.wedge([-71.067071, 42.354500, 0], azimuth=202.44, width=90, radius=60),  # ballfield, Boston Common
    shapes.ribbon(greenway, 45),                                            # Greenway path
    shapes.con_rings([-70.890110, 42.327942, 0], start=200, interval=200, count=5),  # Boston Light
    shapes.fishnet([-71.048952, 42.344467, 0], 20, 9, 9, azimuth=131.38),   # South Boston lot
    shapes.hex_field([-71.017548, 42.334915, 1], 40, 5, z_mode="RTG", labels=True),  # Pleasure Bay lagoon, 1 m up
]

kmlb.kml("2D shapes", features, path="shapes_2d.kml")
```

[Download shapes_2d.kml](../assets/shapes_2d.kml){ .md-button .kmlb-download download="shapes_2d.kml" }

---

## 3D solids

`cylinder`, `cone`, `dome`, `sphere`, `cube`, `pyramid`, and `soccer_ball` build
point-anchored 3D volumes at **absolute altitude**, so give `coords` a real (MSL)
`z`. Most return a single `Placemark` wrapping a `<MultiGeometry>` of polygon
panels (`soccer_ball` returns a folder of two).

**Shared conventions**

- **`coords`**: the anchor point as `[lon, lat, z]`.
- **`azimuth`/`tilt`**: aim the axis. `tilt=90` (default) stands the solid
  straight up, `tilt=0` lays it horizontal, `tilt=-90` points it down; `azimuth` is
  the compass bearing it leans toward when tilted.
- **`anchor`**: slides the body along the axis so its named point sits at
  `coords`: `'base'` (near end, body extends along the axis), `'center'`
  (midpoint), or `'top'` (far end, body hangs back). All solids move the same
  direction, so `sphere(mast, 5, anchor='base')` rests the bottom pole on the mast
  tip, and a forward-opening `cone` beam is `anchor='top'` with the axis aimed by
  `azimuth`/`tilt`.
- **`headers`/`attrs`**: override the attribute table.
- **`style_to_use`**: name a shared polygon style to use instead of `color`.
- **`cam`**: a `LookAt`/`Camera` default view.

!!! note "Altitude and translucency"
    `coords`'s `z` is an absolute MSL altitude, so give it enough height to clear
    the terrain. The default fills are translucent (~40%), which Google Earth
    renders with some see-through banding on a closed solid: a viewer limitation,
    not a geometry issue. Raise the opacity for a more solid look.

### cylinder

Builds a 3D cylinder volume: two `radius` end discs `height` apart along the
axis, joined by side panels.

```python
cylinder(coords, radius, height, *, top_radius=None, azimuth=0, tilt=90,
         anchor="base", sides=32, color=("#66ff33", 40), cap=True, headers=None,
         attrs=None, style_to_use=None, name="Cylinder", z_mode="ABS", hidden=False,
         cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` anchor point; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Base circle radius in meters. |
| `height` | `float` | required | Length along the axis, in meters. |
| `top_radius` | `float` | `None` | Top circle radius in meters. `None` equals `radius` (a true cylinder); a different value tapers it into a frustum, and `0` closes it to a point like a cone. |
| `azimuth` | `float` | `0` | Compass bearing the axis leans toward; only matters when the axis is tilted. |
| `tilt` | `float` | `90` | Axis angle above horizontal: `90` = straight up, `0` = horizontal, `-90` = straight down. |
| `anchor` | `str` | `'base'` | Which point sits at `coords`: `'base'`, `'center'`, or `'top'`. See Shared conventions above. |
| `sides` | `int` | `32` | Facets around the circumference; more gives a rounder solid. |
| `color` | color | `('#66ff33', 40)` | Fill color as a palette name, `#rrggbb`, or `(color, opacity)`. The outline uses the same hue, opaque. |
| `cap` | `bool` | `True` | Close both ends with a disc. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Cylinder'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the cylinder's panels.

!!! failure "Raises"
    `ValueError` if `top_radius` is negative.

```python
# A 30 m safety cylinder over a helipad (10 m radius) at 52 m MSL.
kmlb.shapes.cylinder([-71.063187, 42.349164, 52], 10, 30)

# A tapered frustum (a cooling tower): 20 m base narrowing to an 11 m top.
kmlb.shapes.cylinder([-71.056307, 42.344475, 0], 20, 45, top_radius=11, z_mode="RTG")
```

### cone

Builds a 3D cone volume: a `radius` base disc tapering to a point `height` away
along the axis. `anchor` slides the cone along the axis the same way it
moves the other solids: `'base'` sits the base disc at `coords` with the apex out
along the axis, `'top'` sits the apex at `coords` with the base hanging back.

```python
cone(coords, radius, height, *, azimuth=0, tilt=90, anchor="base",
     sides=32, color=("#3399ff", 40), cap=True, headers=None, attrs=None,
     style_to_use=None, name="Cone", z_mode="ABS", hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` anchor point; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Base radius in meters. |
| `height` | `float` | required | Base-to-apex length along the axis, in meters. |
| `azimuth` | `float` | `0` | Compass bearing the axis leans toward; only matters when the axis is tilted. |
| `tilt` | `float` | `90` | Axis angle above horizontal: `90` = straight up, `0` = horizontal, `-90` = straight down. |
| `anchor` | `str` | `'base'` | Which point sits at `coords`: `'base'` (base disc), `'center'`, or `'top'` (apex). See Shared conventions above. |
| `sides` | `int` | `32` | Facets around the circumference; more gives a rounder solid. |
| `color` | color | `('#3399ff', 40)` | Fill color as a palette name, `#rrggbb`, or `(color, opacity)`. The outline uses the same hue, opaque. |
| `cap` | `bool` | `True` | Close the base with a disc. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Cone'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the cone's panels.

```python
# A radio antenna mast: a slender apex-up cone, 45 m tall, atop a 171 m MSL tower.
kmlb.shapes.cone([-71.060854, 42.358412, 171], 3, 45)

# Its broadcast beam: apex at the mast top (216 m), tilted down and widening toward the ground.
# cap=False leaves the wide end open, so it reads as a beam rather than a solid cone.
kmlb.shapes.cone([-71.060854, 42.358412, 216], 30, 120, anchor="top", azimuth=90, tilt=10, cap=False)
```

### dome

Builds a 3D hemisphere: a `radius` base disc rising in `rings` bands to a pole
one radius along the axis. Invert it (`tilt=-90, anchor="top"`)
for a bowl.

```python
dome(coords, radius, *, azimuth=0, tilt=90, anchor="base", sides=32,
     rings=8, color=("#ff9933", 40), cap=True, headers=None, attrs=None,
     style_to_use=None, name="Dome", z_mode="ABS", hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` anchor point; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Radius in meters. |
| `azimuth` | `float` | `0` | Compass bearing the axis leans toward; only matters when the axis is tilted. |
| `tilt` | `float` | `90` | Axis angle above horizontal: `90` = straight up, `0` = horizontal, `-90` = straight down (bowl). |
| `anchor` | `str` | `'base'` | Which point sits at `coords`: `'base'`, `'center'`, or `'top'` (pole). See Shared conventions above. |
| `sides` | `int` | `32` | Facets around the circumference; more gives a rounder solid. |
| `rings` | `int` | `8` | Horizontal bands from rim to pole; more gives a smoother curve. |
| `color` | color | `('#ff9933', 40)` | Fill color as a palette name, `#rrggbb`, or `(color, opacity)`. The outline uses the same hue, opaque. |
| `cap` | `bool` | `True` | Close the base with a disc. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Dome'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the dome's panels.

```python
# A 270 m no-fly-zone bubble over a Charles River fireworks show (base at river level).
kmlb.shapes.dome([-71.085106, 42.356654, 0], 270)
```

### sphere

Builds a full 3D sphere centered on `coords`, extending `radius` in every
direction, meshed into `sides` facets around and `rings` bands pole to pole. It
is closed, so there is no `cap`.

```python
sphere(coords, radius, *, azimuth=0, tilt=90, anchor="center", sides=24,
       rings=12, color=("#9933ff", 40), headers=None, attrs=None,
       style_to_use=None, name="Sphere", z_mode="ABS", hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` anchor point; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Radius in meters. |
| `azimuth` | `float` | `0` | Compass bearing the pole axis leans toward; only matters when the axis is tilted. |
| `tilt` | `float` | `90` | Pole-axis angle above horizontal: `90` = upright, `0` = horizontal, `-90` = inverted. |
| `anchor` | `str` | `'center'` | Which point sits at `coords`: `'center'`, `'base'` (bottom pole), or `'top'` (top pole). See Shared conventions above. |
| `sides` | `int` | `24` | Facets around the equator; more gives a rounder sphere. |
| `rings` | `int` | `12` | Bands from pole to pole; more gives a rounder sphere. |
| `color` | color | `('#9933ff', 40)` | Fill color as a palette name, `#rrggbb`, or `(color, opacity)`. The outline uses the same hue, opaque. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Sphere'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the sphere's panels.

```python
# A 30 m sphere resting bottom-pole-down on a tower tip at 188 m MSL.
kmlb.shapes.sphere([-71.052183, 42.355688, 188], 30, anchor="base")
```

### cube

Builds a cube, or a rectangular box, as six panels. Pass `size` as one
value for a cube, or `[x, y, z]` for a box: `x` across (east at azimuth 0), `y`
deep (north), `z` along the axis.

```python
cube(coords, size, *, azimuth=0, tilt=90, anchor="base", color=("#ff5050", 40),
     cap=True, headers=None, attrs=None, style_to_use=None, name="Cube",
     z_mode="ABS", hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` base center; `z` is an absolute (MSL) altitude. |
| `size` | `float` or `list[float]` | required | Edge length (cube) or `[x, y, z]` (box), in meters. |
| `azimuth` | `float` | `0` | Compass bearing the axis leans toward; only matters when tilted. |
| `tilt` | `float` | `90` | Axis angle above horizontal: `90` = straight up, `0` = horizontal, `-90` = down. |
| `anchor` | `str` | `'base'` | Which face sits at `coords`: `'base'`, `'center'`, or `'top'`. |
| `color` | color | `('#ff5050', 40)` | Fill color; the outline uses the same hue, opaque. |
| `cap` | `bool` | `True` | Close the two end faces. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Cube'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the box's panels.

```python
# A 170 m cube enclosing a park, resting on the ground (z_mode="RTG"). The park's
# two opposite corners are ~166 m apart, so a single 170 m size covers the footprint.
kmlb.shapes.cube([-71.032344, 42.336542, 0], 170, anchor="base", z_mode="RTG")

# A 60 x 30 x 120 m tower block instead: pass [x, y, z] (x along azimuth, y across, z up).
# azimuth=302 runs the long 60 m side along ~32 deg to fit the parcel.
kmlb.shapes.cube([-71.058717, 42.347704, 0], [60, 30, 120], anchor="base", azimuth=302, z_mode="RTG")
```

### pyramid

Builds a 3D pyramid: a regular polygon base of `sides` edges rising to a single
apex. The default `sides=4` gives a square pyramid, and more sides
approach a cone. `orient` spins the base about the axis so a corner or a flat side
faces a chosen direction.

```python
pyramid(coords, radius, height, sides=4, *, orient=0.0, azimuth=0, tilt=90,
        anchor="base", color=("#ffcc00", 40), cap=True, headers=None, attrs=None,
        style_to_use=None, name="Pyramid", z_mode="ABS", hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` base center; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Base center-to-corner distance, in meters. |
| `height` | `float` | required | Base-to-apex length along the axis, in meters. |
| `sides` | `int` | `4` | Number of base sides (3 or more). |
| `orient` | `float` | `0.0` | Rotation of the base about the axis, in degrees. |
| `azimuth` | `float` | `0` | Compass bearing the axis leans toward; only matters when tilted. |
| `tilt` | `float` | `90` | Axis angle above horizontal: `90` = straight up, `0` = horizontal, `-90` = down. |
| `anchor` | `str` | `'base'` | Which point sits at `coords`: `'base'`, `'center'`, or `'top'` (apex). |
| `color` | color | `None` | Fill color; the outline uses the same hue, opaque. When omitted, chosen by base edge count from `shapes.PYRAMID_PALETTE` (triangle, square, pentagon, ... each differ). |
| `cap` | `bool` | `True` | Close the base with a polygon. |
| `headers` | `list` | `None` | Titles for the attribute table (overrides the default). |
| `attrs` | `list` | `None` | Values for the attribute table, paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use instead of `color`. |
| `name` | `str` | `'Pyramid'` | Placemark name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the placemark hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` wrapping a `MultiGeometry` of the pyramid's panels.

!!! failure "Raises"
    `ValueError` if `sides` is less than 3.

```python
# Three pyramids following the Rose Kennedy Greenway, each with a 40 m-wide base
# oriented along the path (orient=125, its bearing) and resting on the ground
# (z_mode="RTG"). With no color given, each base-count takes a PYRAMID_PALETTE color.
kmlb.shapes.pyramid([-71.056663, 42.362658, 0], 20, 90, orient=125, z_mode="RTG")            # square (4-side)
kmlb.shapes.pyramid([-71.055614, 42.362052, 0], 20, 120, sides=3, orient=125, z_mode="RTG")  # triangular
kmlb.shapes.pyramid([-71.054195, 42.361390, 0], 20, 90, sides=6, orient=125, z_mode="RTG")   # hexagonal
```

### soccer_ball

Builds a soccer ball: a truncated icosahedron of 12 pentagon and 20 hexagon
faces, two-tone (dark pentagons, light hexagons by default). Returned as a folder
of two placemarks so each color toggles on its own.

```python
soccer_ball(coords, radius, *, azimuth=0, tilt=90, anchor="center",
            colors=(("#111111", 100), ("#ffffff", 100)), headers=None, attrs=None,
            style_to_use=None, name="Soccer Ball", z_mode="ABS", hidden=False,
            collapsed=True, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[lon, lat, z]` ball center; `z` is an absolute (MSL) altitude. |
| `radius` | `float` | required | Radius in meters. |
| `azimuth` | `float` | `0` | Compass bearing the pole axis leans toward. |
| `tilt` | `float` | `90` | Pole-axis angle above horizontal. |
| `anchor` | `str` | `'center'` | Which point sits at `coords`: `'center'`, `'base'`, or `'top'`. |
| `colors` | color or pair | `(('#111111', 100), ('#ffffff', 100))` | A single color for both face types, or a `(pentagon_color, hexagon_color)` pair. |
| `headers` | `list` | `None` | Titles for each placemark's attribute table. |
| `attrs` | `list` | `None` | Values paired with `headers`. |
| `style_to_use` | `str` | `None` | Name of a shared polygon style to use on both placemarks instead of `colors`. |
| `name` | `str` | `'Soccer Ball'` | Folder name. |
| `z_mode` | `str` | `'ABS'` | Altitude mode; must be non-clamped for the solid to render. |
| `hidden` | `bool` | `False` | `True` returns the folder hidden. |
| `collapsed` | `bool` | `True` | Whether the folder starts collapsed. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view for the folder. |

!!! success "Returns"
    `Element`: a KML `Folder` holding the pentagon and hexagon placemarks.

```python
# A small two-tone soccer ball resting on Boston Common.
kmlb.shapes.soccer_ball([-71.067507, 42.355289, 0], 8, anchor="base", z_mode="RTG")
```

### Example: solids along a path

Each solid is an ordinary KML element, so a scene is just a list of them. This
places one of each equally spaced along a path, then repeats with oriented variants
(a tapered cylinder (frustum) on its side, an inverted open-ended cone, a bowl, and
a sphere with its pole axis along the path).

[![Cylinder, cone, dome, and sphere volumes, and their oriented variants, over Boston Logan in Google Earth](../assets/img/3d-shapes.jpg)](../assets/img/3d-shapes.jpg){ .glightbox .crop-3d }

<p class="kmlb-caption">The 3D solids and their oriented variants, viewed in Google&nbsp;Earth.</p>

```python
import kmlb

# Path for shapes to follow
a, b = [-71.014092, 42.353934], [-71.003726, 42.375887]   # [lon, lat]
d = kmlb.distance(a, b)
az = kmlb.bearing(a, b)

# eight equally spaced points along the path, at 60 m altitude
pts = [kmlb.destination(a, az, i / 7 * d)[:2] + [60.0] for i in range(8)]

solids = [
    kmlb.shapes.cylinder(pts[0], 120, 300),
    kmlb.shapes.cone(pts[1], 140, 350),
    kmlb.shapes.dome(pts[2], 150),
    kmlb.shapes.sphere([pts[3][0], pts[3][1], 250], 150),
    # oriented variants
    kmlb.shapes.cylinder([pts[4][0], pts[4][1], 150], 120, 400, top_radius=60, azimuth=az + 90, tilt=0, anchor="center"),
    kmlb.shapes.cone(pts[5], 140, 350, tilt=-90, anchor="top", cap=False),   # inverted, open (no base cap)
    kmlb.shapes.dome(pts[6], 150, tilt=-90, anchor="top"),          # bowl
    kmlb.shapes.sphere([pts[7][0], pts[7][1], 250], 150, azimuth=az, tilt=0),
]

kmlb.kml("3D solids", solids, path="shapes_3d.kml")
```

[Download shapes_3d.kml](../assets/shapes_3d.kml){ .md-button .kmlb-download download="shapes_3d.kml" }

---

## fresnel_zone

Builds the Fresnel zone of a point-to-point radio link as a 3D ellipsoid tube
(a `MultiGeometry` of polygon panels) around the line of sight, and, by default,
the straight line-of-sight path as well. The two are returned together in a
folder so each can be toggled on its own in Google Earth.

The tube is inherently three-dimensional, so it uses absolute altitude: each
endpoint's `z` should be an absolute (MSL) antenna altitude.

```python
fresnel_zone(point_a, point_b, freq_mhz, *, name="RF Link", zone=1,
             cross_rings=25, ring_strips=16, zone_color=("yellow", 40),
             include_path=True, path_color="red", center_ring_color="cyan",
             z_mode="ABS", collapsed=True, hidden=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `point_a` | `list[float]` | required | First endpoint `[lon, lat, z]`; `z` is an absolute (MSL) altitude. |
| `point_b` | `list[float]` | required | Second endpoint `[lon, lat, z]`; `z` is an absolute (MSL) altitude. |
| `freq_mhz` | `float` | required | Link frequency in megahertz. |
| `name` | `str` | `'RF Link'` | Link name. |
| `zone` | `int` | `1` | Fresnel zone number to draw. |
| `cross_rings` | `int` | `25` | Cross-section rings along the link; more gives a smoother tube lengthwise. |
| `ring_strips` | `int` | `16` | Strips (facets) around each cross-section; more gives a rounder tube. |
| `zone_color` | color | `('yellow', 40)` | Tube color as a palette name, `#rrggbb` hex, or `(color, opacity)` pair. The outline uses the same hue at full opacity. |
| `include_path` | `bool` | `True` | `True` also draws the line-of-sight path; `False` omits it. |
| `path_color` | color | `'red'` | Line-of-sight path color, in the same forms as `zone_color`. |
| `center_ring_color` | color | `'cyan'` | Color of a hoop drawn at the widest (mid-path) cross-section, in the same forms as `zone_color`. Set to `None` to omit it. |
| `z_mode` | `str` | `'ABS'` | Altitude mode. The tube only renders under a non-clamped mode. See [Altitude modes](getting_started.md#altitude-modes). |
| `collapsed` | `bool` | `True` | `False` returns the folder expanded; `True` (default) returns it collapsed in the places panel. |
| `hidden` | `bool` | `False` | `True` returns the folder hidden. |
| `cam` | `Element` | `None` | A `LookAt`/`Camera` default view for the returned folder (or the bare tube). |

!!! success "Returns"
    `Element`: a KML `Folder` holding the tube plus the line-of-sight path and/or
    the center ring whenever either is drawn, or the tube `Placemark` on its own
    when both `include_path` is `False` and `center_ring_color` is `None`.

!!! failure "Raises"
    `ValueError` if `point_a` and `point_b` are the same location, if `cross_rings` is less than 2, or if `ring_strips` is less than 3.

!!! note "Absolute altitude"
    Endpoint `z` values must be real (MSL) antenna altitudes. The tube is drawn
    at absolute altitude so it sits in space between the towers; a `z` of `0`
    would anchor the link at sea level.

**Example**

A 5.8 GHz link between two towers

```python
# Endpoint z values are absolute antenna altitudes (meters above sea level).
link = kmlb.shapes.fresnel_zone([-71.082399, 42.347435, 228],
                                [-71.058514, 42.358468, 182],
                                freq_mhz=5800, name="North Link")
kmlb.kml("Link Study", [link], path="link.kml")
```

### Example: a combined RF scene

Shapes are ordinary KML elements. Several can be added to document. This sample
builds a down-tilted antenna sector and a point-to-point Fresnel Zone on two
corners of the same building, then writes them to a single `.kml`.

[![A blue down-tilted antenna sector and a yellow point-to-point Fresnel tube over Boston, viewed in Google Earth](../assets/img/rf-scene.jpg)](../assets/img/rf-scene.jpg){ .glightbox .crop-top }

<p class="kmlb-caption">A blue down-tilted antenna sector and a yellow point-to-point Fresnel tube over Boston.</p>

```python
import kmlb

# A 60-degree antenna sector with 15 degrees of down-tilt, on one building corner.
sector = kmlb.shapes.wedge([-71.082195, 42.347025, 228], azimuth=120, width=60,
                           radius=800, tilt=-15, name="Sector")

# A 5.8 GHz point-to-point link from another corner of the same building.
link = kmlb.shapes.fresnel_zone([-71.082399, 42.347435, 228],
                                [-71.058514, 42.358468, 182],
                                freq_mhz=5800, name="ptp-link")

kmlb.kml("RF Scene", [sector, link], path="rf_scene.kml")
```

[Download rf_scene.kml](../assets/rf_scene.kml){ .md-button .kmlb-download download="rf_scene.kml" }

<br><br><br><br><br>

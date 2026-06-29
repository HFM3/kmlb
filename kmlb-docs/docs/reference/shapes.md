<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Shapes</h2>
<p class="kmlb-hero__sub">Higher-level geometry builders. <code>wedge</code> draws a circular sector (a natural fit for cellular coverage.)</p>
</div>

## wedge

Builds a pie-wedge-shaped polygon: a circular sector centered on a point, opening
toward an azimuth, with a given angular width and radius. The arc is approximated
with `steps` vertices projected across the WGS-84 ellipsoid.

A wedge maps naturally onto a cellular coverage sector, which makes it a handy
way to illustrate cell-tower coverage. The `azimuth` is the direction the antenna
faces, the `width` is the sector's beamwidth, and the `radius` is its reach, so
the shape visualizes sector width, direction, and reach at a glance.

```python
wedge(center, azimuth, width, radius, *, steps=15, name="Wedge", **kwargs) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `center` | `list[float]` | required | `[lon, lat, elev]` origin of the wedge. |
| `azimuth` | `float` | required | Direction the center of the arc points, degrees from true north. |
| `width` | `float` | required | Angular width of the wedge, in degrees. |
| `radius` | `float` | required | Length of the wedge's straight edges, in meters. |
| `steps` | `int` | `15` | Number of vertices along the arc; more steps give a smoother curve. |
| `name` | `str` | `'Wedge'` | Placemark name. |
| `**kwargs` | | | Any keyword argument accepted by [`polygon`](features.md#polygon) (e.g. `z_mode`, `style_to_use`, `hidden`, `headers`, `attrs`). |

!!! success "Returns"
    `Element`: a KML `Placemark` containing the wedge `Polygon`.

!!! note
    By default `wedge` fills `headers`/`attrs` with the wedge's defining
    parameters (azimuth, width, radius, steps, and center). Pass your own
    `headers`/`attrs` to override them.

**Examples**

A wedge opening due east

```python
# A 30°-wide wedge of radius 1 km, opening due east from a center point.
w = kmlb.shapes.wedge([-71.0589, 42.3601, 0], azimuth=90, width=30, radius=1000)
```

<br><br><br><br><br>
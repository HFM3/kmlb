<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Geodesy</h2>
<p class="kmlb-hero__sub">Measure and project across the WGS-84 ellipsoid with Vincenty's solutions: <code>distance</code>, <code>bearing</code>, and <code>destination</code>.</p>
</div>

## distance

Measures the geodesic distance, in meters, between two coordinates across the
WGS-84 ellipsoid (Vincenty's inverse solution). For the direction between the
points, see [`bearing`](#bearing).

```python
distance(p1, p2, precision=3) -> float
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `p1` | `list[float]` | required | `[lon, lat]` or `[lon, lat, elev]`; any elevation is ignored. |
| `p2` | `list[float]` | required | A second `[lon, lat]` (or `[lon, lat, elev]`); any elevation is ignored. |
| `precision` | `int` | `3` | Decimal places to retain in the result. |

!!! success "Returns"
    `float`: the distance between the two coordinates, in meters.

**Examples**

Distance in meters between two coordinates

```python
boston = [-71.0589, 42.3601]
nyc = [-74.0060, 40.7128]
kmlb.distance(boston, nyc)  # -> 306490.491
```

Round to fewer decimal places

```python
kmlb.distance(boston, nyc, precision=0)  # -> 306490.0
```

---

## bearing

Measures the initial bearing from one coordinate to another: the forward azimuth,
in degrees (`0` to `360`) clockwise from true north, of the geodesic from `p1` to
`p2` on the WGS-84 ellipsoid (Vincenty's inverse solution). Because geodesics
curve, this is the bearing *at the start* of the path; it differs from the
bearing on arrival.

```python
bearing(p1, p2, precision=3) -> float
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `p1` | `list[float]` | required | The origin `[lon, lat]` (or `[lon, lat, elev]`); any elevation is ignored. |
| `p2` | `list[float]` | required | The target `[lon, lat]` (or `[lon, lat, elev]`); any elevation is ignored. |
| `precision` | `int` | `3` | Decimal places to retain in the result. |

!!! success "Returns"
    `float`: the initial bearing from `p1` to `p2`, in degrees (`0` to `360`)
    clockwise from true north.

**Examples**

Initial bearing between two coordinates

```python
boston = [-71.0589, 42.3601]
nyc = [-74.0060, 40.7128]
kmlb.bearing(boston, nyc)  # -> 234.338
```

Round to fewer decimal places

```python
kmlb.bearing(boston, nyc, precision=1)  # -> 234.3
```

---

## destination

Finds the coordinate reached by travelling `distance` meters from `origin` along
`bearing` (degrees clockwise from true north) across the WGS-84 ellipsoid
(Vincenty's direct solution). It is the inverse of [`distance`](#distance) /
[`bearing`](#bearing), and the building block for radial geometry: project a
point, then draw a line or polygon to it.

```python
destination(origin, bearing, distance, precision=3) -> list[float]
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `origin` | `list[float]` | required | `[lon, lat]` or `[lon, lat, elev]` start. A `z` value passes through unchanged. |
| `bearing` | `float` | required | Direction to travel, in degrees clockwise from true north (`0` = north). |
| `distance` | `float` | required | Distance to travel, in meters. |
| `precision` | `int` | `3` | Decimal places to retain for the internal bearing calculation. |

!!! success "Returns"
    `list[float]`: the destination `[lon, lat]` (or `[lon, lat, z]`).

!!! tip "Drawing radial shapes"
    Project several points around a center and connect them into a line or
    polygon to draw radial shapes. This is exactly how [`wedge`](shapes.md#wedge)
    builds its arc.

**Examples**

Travel a bearing and distance from a point

```python
start = [-71.053568, 42.359053]
kmlb.destination(start, 33, 100)  # 100 m out at bearing 33 degrees
```

Build a shape from projected points

```python
# A square: four corners 500 m out, 90 degrees apart, then closed
center = [-71.0589, 42.3601]
corners = [kmlb.destination(center, az, 500) for az in (45, 135, 225, 315)]
corners.append(corners[0])
kmlb.polygon([corners], "Square")
```

<br><br><br><br><br>
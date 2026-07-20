<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Map Objects</h2>
<p class="kmlb-hero__sub">The placemark builders: <code>point</code>, <code>search_poi</code>, <code>street_view</code>, <code>line</code>, and <code>polygon</code>. Each returns a KML element ready to drop into a <a href="../views_export/#folder">folder</a> or <a href="../views_export/#kml">kml</a> document.</p>
</div>

## point

Builds a point placemark from a single coordinate pair in `[x, y, z]` or
`[lng, lat, elev]` order.

```python
point(coords, name, *, headers=None, attrs=None, desc=None,
      blurb=None, z_mode="CTG", style_to_use=None, hidden=False,
      extrude=False, cam=None) -> Element
```

| Parameter | Type | Default | Description                                                                                                                                                                                                      |
|---|---|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `coords` | `list[float]` | required | `[longitude, latitude]` or `[longitude, latitude, elevation]`; elevation is optional and defaults to `0` (placed on the ground under the default `'CTG'` mode).                                                    |
| `name` | `str` | required | Placemark name.                                                                                                                                                                                                  |
| `headers` | `list` | `None` | Attribute names, paired positionally with `attrs`.                                                                                                                                                               |
| `attrs` | `list` | `None` | Attribute values shown in the description balloon and `ExtendedData`.                                                                                                                                            |
| `desc` | `str` | `None` | Free text/HTML for the description balloon, rendered above the `headers`/`attrs` table.                                                                                                                          |
| `blurb` | `str` | `None` | Short summary shown beneath the name in Google Earth's places list. Emitted only when provided.                                                                                                                 |
| `z_mode` | `str` | `'CTG'` | Altitude mode: CTG (clampToGround, on the ground; the default), RTG (relativeToGround, above ground level), ABS (absolute, above sea level), CSF (clampToSeaFloor, on the sea floor), or RSF (relativeToSeaFloor, above the sea floor). See [Altitude modes](getting_started.md#altitude-modes). |
| `style_to_use` | `str` | `None` | Name/ID of a [`point_style`](styles.md#point_style) to reference.                                                                                                                                                |
| `hidden` | `bool` | `False` | `True` makes the point start hidden.                                                                                                                                                                             |
| `extrude` | `bool` | `False` | Draw a vertical tether line from the point down to the ground. Visible only when the point is raised (a non-`CTG` altitude mode with a non-zero altitude).                                                       |
| `cam` | `Element` | `None` | A [`look_at`](views_export.md#look_at) or [`camera`](views_export.md#camera) element for a default view.                                                                                                                                               |

!!! success "Returns"
    `Element`: a KML `Placemark` containing a `Point`.

**Examples**

The simplest point: a coordinate and a name

```python
kmlb.point([-71.0589, 42.3601], "Boston")
```

Raise it off the ground with an elevation

```python
kmlb.point([-71.0589, 42.3601, 60], "Boston", z_mode="RTG")
```

Add a description balloon

```python
# desc: the balloon shown when you click the placemark
kmlb.point([-71.0589, 42.3601], "Boston", desc="Capital of Massachusetts.")
```

Add a places-list snippet

```python
# blurb: a short summary under the name in the Places list (not the balloon)
kmlb.point([-71.0589, 42.3601], "Boston", blurb="State capital")
```

Add an attribute table

```python
kmlb.point([-71.0589, 42.3601], "Boston",
           headers=["Population", "Founded"], attrs=[654776, 1630])
```

Reference a custom style

```python
city = kmlb.point_style("city", icon="triangle", color="red", scale=1.4)
kmlb.point([-71.0589, 42.3601], "Boston", style_to_use="city")
```

Extrude a raised point with a tether to the ground

```python
kmlb.point([-71.0589, 42.3601, 150], "Boston",
           z_mode="RTG", extrude=True)
```

Everything together

```python
city = kmlb.point_style("city", icon="triangle", color="red", scale=1.4)
view = kmlb.look_at([-71.0589, 42.3601, 0], distance=600, azimuth=210, tilt=55)
kmlb.point([-71.0589, 42.3601, 150], "Boston",
           desc="Capital of Massachusetts.", blurb="State capital",
           headers=["Population"], attrs=[654776],
           z_mode="RTG", extrude=True,
           style_to_use="city", cam=view)
```

---

## search_poi

Builds a placemark whose location is resolved by Google Earth from a search
string. Instead of fixed coordinates, the placemark carries an `<address>`
element; Google Earth geocodes that address when the file is opened and places
the point accordingly.

```python
search_poi(poi, name=None, *, headers=None, attrs=None,
           desc=None, blurb=None,
           style_to_use=None, hidden=False) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `poi` | `str` | required | What you would type into a search bar: a place name or address. |
| `name` | `str` | `None` | Placemark name. Defaults to `poi` when omitted. |
| `headers` | `list` | `None` | Attribute names. |
| `attrs` | `list` | `None` | Attribute values. |
| `desc` | `str` | `None` | Free text/HTML for the description balloon, rendered above the `headers`/`attrs` table. |
| `blurb` | `str` | `None` | Short summary shown beneath the name in Google Earth's places list. Emitted only when provided. |
| `style_to_use` | `str` | `None` | Name/ID of a point style to reference. |
| `hidden` | `bool` | `False` | `True` makes the point start hidden. |

!!! success "Returns"
    `Element`: a KML `Placemark` carrying an `<address>` rather than coordinates.

!!! note
    The address is geocoded by Google Earth at display time, so an internet
    connection is required when the KML is opened.

**Examples**

The simplest search: a place or address

```python
kmlb.search_poi("Fenway Park, Boston")
```

Give it a custom name

```python
kmlb.search_poi("4 Jersey St, Boston", "Fenway Park")
```

Add a balloon, a snippet, and a style

```python
kmlb.search_poi("Fenway Park, Boston", blurb="MLB ballpark",
                desc="Home of the Boston Red Sox", style_to_use="redTriangle")
```

---

## street_view

Builds a point placemark from a Google Maps Street View URL. The location,
heading, tilt, zoom, and panorama id are read from the URL, and the placemark's
default [`camera`](views_export.md#camera) opens that exact panorama in Google
Earth's Street View.

```python
street_view(url, name="Street View", *, headers=None, attrs=None,
            desc=None, blurb=None, style_to_use=None, hidden=False,
            extrude=False, heading=None, tilt=None, roll=0.0,
            zoom=None, altitude=0.0, z_mode="ABS", date=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | required | A Google Maps Street View URL (the `.../@lat,lng,...` share link). |
| `name` | `str` | `'Street View'` | Placemark name. |
| `headers` | `list` | `None` | Attribute names, paired positionally with `attrs`. |
| `attrs` | `list` | `None` | Attribute values shown in the description balloon and `ExtendedData`. |
| `desc` | `str` | `None` | Free text/HTML for the description balloon, rendered above the `headers`/`attrs` table. |
| `blurb` | `str` | `None` | Short summary shown beneath the name in Google Earth's places list. Emitted only when provided. |
| `style_to_use` | `str` | `None` | Name/ID of a [`point_style`](styles.md#point_style) to reference. |
| `hidden` | `bool` | `False` | `True` makes the point start hidden. |
| `extrude` | `bool` | `False` | Draw a vertical tether line from the point down to the ground. |
| `heading` | `float` | `None` | Street View view direction: override the panorama heading parsed from the URL, `0`–`360` degrees. |
| `tilt` | `float` | `None` | Street View pitch: override the panorama tilt, `0` (straight down) to `90` (horizon). |
| `roll` | `float` | `0.0` | Roll of the Street View view about the axis it looks along, in degrees. |
| `zoom` | `float` | `None` | Street View field of view in degrees; a smaller value zooms in. Overrides the value parsed from the URL. |
| `altitude` | `float` | `0.0` | Altitude of the Street View camera, in meters. |
| `z_mode` | `str` | `'ABS'` | Altitude mode for the camera. See [Altitude modes](getting_started.md#altitude-modes). |
| `date` | `str` | `None` | Preferred panorama capture date, such as `'2025-08'`. |

!!! success "Returns"
    `Element`: a KML `Placemark` containing a `Point` and a Street View `Camera`.

!!! note "These frame the Street View panorama, not Google Earth"
    `heading`, `tilt`, `roll`, and `zoom` set how the **Street View panorama** is
    framed when the placemark is opened, that is, the view direction and field of
    view *inside* Street View. They are not Google Earth's ordinary globe roll,
    tilt, or zoom, and they do not change how you fly around the map. Each
    overrides the value parsed from the URL for tight adjustment.

    A URL cannot carry a camera altitude or a panorama capture date, so those
    come from the `altitude` and `date` arguments instead.

**Examples**

The simplest Street View placemark: paste a URL

```python
url = "https://www.google.com/maps/@42.3544682,-71.0510368,3a,75y,121.94h,94.79t/data=..."
kmlb.street_view(url, "303 Congress St")
```

Fine-tune the camera angle and zoom

```python
kmlb.street_view(url, "303 Congress St", tilt=92, zoom=70)
```

Everything together

```python
kmlb.street_view(url, "303 Congress St",
                 desc="Fort Point Channel", blurb="Waterfront",
                 headers=["Neighborhood"], attrs=["Seaport"],
                 tilt=92, zoom=70, altitude=3, date="2025-08")
```

---

## line

Builds a line/polyline placemark from an ordered list of coordinates.

```python
line(coords, name, *, headers=None, attrs=None,
     desc=None, blurb=None, z_mode="CTG",
     style_to_use=None, hidden=False, follow_terrain=True,
     extrude=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[list[float]]` | required | Ordered `[lon, lat]` or `[lon, lat, elev]` vertices; elevation is optional and defaults to `0`. |
| `name` | `str` | required | Placemark name. |
| `headers` | `list` | `None` | Attribute names. |
| `attrs` | `list` | `None` | Attribute values. |
| `desc` | `str` | `None` | Free text/HTML for the description balloon, rendered above the `headers`/`attrs` table. |
| `blurb` | `str` | `None` | Short summary shown beneath the name in Google Earth's places list. Emitted only when provided. |
| `z_mode` | `str` | `'CTG'` | Altitude mode: CTG (clampToGround, on the ground; the default), RTG (relativeToGround, above ground level), ABS (absolute, above sea level), CSF (clampToSeaFloor, on the sea floor), or RSF (relativeToSeaFloor, above the sea floor). See [Altitude modes](getting_started.md#altitude-modes). |
| `style_to_use` | `str` | `None` | Name/ID of a [`line_style`](styles.md#line_style). |
| `hidden` | `bool` | `False` | `True` makes the line start hidden. |
| `follow_terrain` | `bool` | `True` | Tessellate so the line follows terrain (only with `'CTG'`). |
| `extrude` | `bool` | `False` | Drop vertices to the ground with extruded walls. |
| `cam` | `Element` | `None` | A [`look_at`](views_export.md#look_at) or [`camera`](views_export.md#camera) element for a default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` containing a `LineString`.

**Examples**

The simplest line: a list of coordinates

```python
kmlb.line([[-71.060, 42.360], [-71.050, 42.370]], "Trail")
```

A 3D line, extruded to the ground: a runway takeoff

```python
# 'extrude' drops walls from the flight path to the ground,
#   showing the climb profile as a curtain.
kmlb.line([[-71.01259, 42.35582, 4],    # runway start
           [-71.00035, 42.358, 4],      # liftoff (mid-runway)
           [-70.9763, 42.36227, 150]],  # airborne, climbing
          "Takeoff", z_mode="ABS", extrude=True)  
```

Reference a custom style

```python
trail = kmlb.line_style("trail", color="gold", width=4)
kmlb.line([[-71.060, 42.360], [-71.050, 42.370]], "Trail", style_to_use="trail")
```

---

## polygon

Builds a polygon placemark. The first ring in `coords` is the outer boundary;
any additional rings become inner boundaries (holes).

```python
polygon(coords, name, *, headers=None, attrs=None,
        desc=None, blurb=None, z_mode="CTG",
        style_to_use=None, hidden=False, follow_terrain=True,
        extrude=False, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[list[list[float]]]` | required | A list of rings; each ring is a list of `[lon, lat]` or `[lon, lat, elev]` vertices (elevation optional, defaults to `0`). Ring 0 is the outer boundary; the rest are holes. |
| `name` | `str` | required | Placemark name. |
| `headers` | `list` | `None` | Attribute names. |
| `attrs` | `list` | `None` | Attribute values. |
| `desc` | `str` | `None` | Free text/HTML for the description balloon, rendered above the `headers`/`attrs` table. |
| `blurb` | `str` | `None` | Short summary shown beneath the name in Google Earth's places list. Emitted only when provided. |
| `z_mode` | `str` | `'CTG'` | Altitude mode: CTG (clampToGround, on the ground; the default), RTG (relativeToGround, above ground level), ABS (absolute, above sea level), CSF (clampToSeaFloor, on the sea floor), or RSF (relativeToSeaFloor, above the sea floor). See [Altitude modes](getting_started.md#altitude-modes). |
| `style_to_use` | `str` | `None` | Name/ID of a [`polygon_style`](styles.md#polygon_style). |
| `hidden` | `bool` | `False` | `True` makes the polygon start hidden. |
| `follow_terrain` | `bool` | `True` | Tessellate so the polygon follows terrain (only with `'CTG'`). |
| `extrude` | `bool` | `False` | Extrude vertices toward the ground. |
| `cam` | `Element` | `None` | A [`look_at`](views_export.md#look_at) or [`camera`](views_export.md#camera) element for a default view. |

!!! success "Returns"
    `Element`: a KML `Placemark` containing a `Polygon`.

**Examples**

The simplest polygon: one ring of coordinates

```python
ring = [[-71.06, 42.36], [-71.05, 42.36], [-71.05, 42.37], [-71.06, 42.36]]
kmlb.polygon([ring], "Lot")
```

Add an inner ring to cut a hole

```python
outer = [[-71.06, 42.36], [-71.05, 42.36], [-71.05, 42.37], [-71.06, 42.36]]
hole  = [[-71.058, 42.362], [-71.054, 42.362], [-71.054, 42.366], [-71.058, 42.362]]
kmlb.polygon([outer, hole], "Block with courtyard")
```

Reference a custom style

```python
fill = kmlb.polygon_style("fill", fill_color=("#03cafc", 40))
ring = [[-71.06, 42.36], [-71.05, 42.36], [-71.05, 42.37], [-71.06, 42.36]]
kmlb.polygon([ring], "Lot", style_to_use="fill")
```

Extrude a raised polygon into a 3D shape

```python
roof = [[-71.0590, 42.3600, 30], [-71.0585, 42.3600, 30],
        [-71.0585, 42.3604, 30], [-71.0590, 42.3600, 30]]
kmlb.polygon([roof], "Canopy", z_mode="RTG", extrude=True)
```
<br><br><br><br><br>
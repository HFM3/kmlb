<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Views &amp; Export</h2>
<p class="kmlb-hero__sub">Group features into folders, set a default camera angle, and assemble everything into a complete KML document or a refreshing network link.</p>
</div>

## folder

Groups loose features into a KML folder. Folders can nest.

```python
folder(name, items, *, desc="", collapsed=True,
       hidden=True, cam=None) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Folder name. |
| `items` | `list[Element]` | required | Features (or other folders) to place in the folder. |
| `desc` | `str` | `''` | Descriptive text. |
| `collapsed` | `bool` | `True` | `True` shows the folder collapsed in the TOC; `False` expanded. |
| `hidden` | `bool` | `True` | `True` starts the folder hidden. A folder's effective visibility still follows its visible contents. |
| `cam` | `Element` | `None` | A `look_at` element for a default view. |

!!! success "Returns"
    `Element`: a KML `Folder` element.

**Examples**

Group features into a folder

```python
a = kmlb.point([-71.060, 42.360], "Stop A")
b = kmlb.point([-71.050, 42.370], "Stop B")
kmlb.folder("Stops", [a, b])
```

Open it in the sidebar, with a description

```python
kmlb.folder("Stops", [a, b], desc="Bus route", collapsed=False)
```

---

## kml

Assembles features and styles into a complete KML document, returns it as a
string, and optionally writes it to disk.

```python
kml(name, features, *, path=None, desc="", styles=None,
    collapsed=True, cam=None) -> str
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Document name. |
| `features` | `list[Element]` | required | Points, lines, polygons, and/or folders to include. |
| `path` | `str` | `None` | Output file path ending in `.kml`. Parent folders are created as needed. When omitted, nothing is written and only the string is returned. |
| `desc` | `str` | `''` | Descriptive text. |
| `styles` | `list[Element]` | `None` | Style elements referenced by features. |
| `collapsed` | `bool` | `True` | `True` shows the root document collapsed in the TOC. |
| `cam` | `Element` | `None` | A `look_at` element for a default view. |

!!! success "Returns"
    `str`: the KML document as an XML string.

**Examples**

Assemble features into a KML string

```python
pt = kmlb.point([-71.0589, 42.3601], "Boston")
kmlb.kml("My Places", [pt])
```

Add styles and write it to a file

```python
city = kmlb.point_style("city", color="red", icon="triangle")
pt = kmlb.point([-71.0589, 42.3601], "Boston", style_to_use="city")
kmlb.kml("My Places", [pt], styles=[city], path="my_places.kml")
```

---

## look_at

Builds a `LookAt` element that defines a default camera angle. The result can be
passed as the `cam` argument to `point`, `line`, `polygon`, `folder`, or `kml`.

```python
look_at(coords, distance, azimuth, tilt, *, z_mode="ABS") -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `coords` | `list[float]` | required | `[longitude, latitude, elevation]` the camera looks at. |
| `distance` | `float` | required | Camera range from the target, in meters. |
| `azimuth` | `float` | required | Compass direction the camera faces, `0`–`360` degrees. |
| `tilt` | `float` | required | Camera tilt, `0` (straight down) to `90` (horizon). |
| `z_mode` | `str` | `'ABS'` | Altitude mode: CTG (clampToGround), RTG (relativeToGround), ABS (absolute, the default here), CSF (clampToSeaFloor), or RSF (relativeToSeaFloor). See [Altitude modes](getting_started.md#altitude-modes). |

!!! success "Returns"
    `Element`: a KML `LookAt` element.

**Examples**

A camera aimed at a coordinate

```python
kmlb.look_at([-71.0589, 42.3601, 0], distance=600, azimuth=210, tilt=55)
```

Attach it to a feature as its default view

```python
view = kmlb.look_at([-71.0589, 42.3601, 0], distance=600, azimuth=210, tilt=55)
kmlb.point([-71.0589, 42.3601], "Boston", cam=view)
```

---

## networklink_kml

Builds a network-link KML that points Google Earth at a hosted KML and refreshes
it on an interval. Returns the string and optionally writes it to disk.

```python
networklink_kml(name, link_path, *, write_path=None, desc="",
                refresh_interval=300, view_refresh=0, collapsed=True) -> str
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Document name. |
| `link_path` | `str` | required | URL of the hosted KML to link to. |
| `write_path` | `str` | `None` | Output file path ending in `.kml`. When omitted, only the string is returned. |
| `desc` | `str` | `''` | Descriptive text. |
| `refresh_interval` | `int` | `300` | Seconds between refreshes; `-1` disables interval refresh. |
| `view_refresh` | `int` | `0` | Seconds after camera movement stops before refreshing; `-1` disables. |
| `collapsed` | `bool` | `True` | `True` shows the link collapsed in the TOC. |

!!! success "Returns"
    `str`: the network-link KML as an XML string.

**Examples**

Link to a hosted KML

```python
kmlb.networklink_kml("Live vehicles", "https://example.com/flood.kml")
```

Refresh faster and write it to a file

```python
kmlb.networklink_kml("Live vehicles", "https://example.com/flood.kml",
                     refresh_interval=60, write_path="link.kml")
```

<br><br><br><br><br>
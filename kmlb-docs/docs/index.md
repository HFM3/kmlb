---
hide:
  - toc
---

<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Build KML files in plain Python</div>
<h2 class="kmlb-hero__title">KMLB Docs</h2>
<p class="kmlb-hero__sub">KMLB is a dependency-free Python KML builder for Google Earth. Write points, lines, polygons, styles, and folders in plain Python, then assemble them into a complete <b><code>.kml</code></b></p><br>
<p class="kmlb-hero__sub">New to KMLB? Check out our <a href="reference/getting_started/">Quick Start Guide</a> and a <a href="tutorial/">tutorial</a> that builds a KML of Boston waterfront attractions step by step.</p>
</div>

---

## Example KML Script

Every feature is one Python call that hands back an XML element. Define a
feature, style it, then bundle it all into a document. That's the whole library.

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
kmlb.kml( "My Places", [boston, block], [city, fill], path="folder/my_places.kml")
```
<br>

[![Building footprints extruded into 3D and viewed in Google Earth, built with kmlb polygons](assets/img/3d-buildings.jpg)](assets/img/3d-buildings.jpg){ .glightbox }

<p class="kmlb-caption">Building footprints extruded into 3D and viewed in Google&nbsp;Earth, built with kmlb polygons.</p>


---


<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Function references</h2>
<p class="kmlb-hero__sub">Every function in kmlb, grouped by what it does. Open any group for full signatures, parameters, and worked examples.</p>
</div>

## Features

Build placemarks from coordinates or a search, ready to drop into a folder or document.

| Function | Description                                                                  |
|---|------------------------------------------------------------------------------|
| [`point`](reference/features.md#point) | Point placemark from a `[lon, lat]` (or `[lon, lat, elev]`) coordinate sets. |
| [`search_poi`](reference/features.md#search_poi) | Placemark located by an address or search string, geocoded by Google Earth.  |
| [`line`](reference/features.md#line) | Line or polyline from an ordered list of coordinates.                        |
| [`polygon`](reference/features.md#polygon) | Polygon from one or more rings (first ring outer, the rest holes).           |

## Styles

Define a reusable style once, name it, and reference it from a feature's `style_to_use`.

| Function | Description |
|---|---|
| [`point_style`](reference/styles.md#point_style) | Reusable point style: icon, color, scale, and label. |
| [`line_style`](reference/styles.md#line_style) | Reusable line style: color and width. |
| [`polygon_style`](reference/styles.md#polygon_style) | Reusable polygon style: fill and outline. |

## Views & Export

Group features, set the camera, and write the document.

| Function | Description |
|---|---|
| [`folder`](reference/views_export.md#folder) | Group features and other folders together. |
| [`kml`](reference/views_export.md#kml) | Assemble features and styles into a KML document and write it to disk. |
| [`look_at`](reference/views_export.md#look_at) | Camera angle and view for a feature or document. |
| [`networklink_kml`](reference/views_export.md#networklink_kml) | Network-link KML that refreshes from a hosted URL. |

## Geodesy

Measure and project on the WGS-84 ellipsoid.

| Function | Description |
|---|---|
| [`distance`](reference/geodesy.md#distance) | Distance in meters between two coordinates. |
| [`bearing`](reference/geodesy.md#bearing) | Initial bearing in degrees between two coordinates. |
| [`destination`](reference/geodesy.md#destination) | Coordinate reached from an origin along a bearing and distance. |

## Shapes

Higher-level geometry built on the core builders.

| Function | Description |
|---|---|
| [`wedge`](reference/shapes.md#wedge) | Pie-wedge (circular sector) polygon, a natural fit for cellular coverage. |

## Colors & Icons

Name colors and markers instead of hunting down hex tuples and icon URLs.

| Function | Description |
|---|---|
| [`colors`](reference/colors_icons.md) | Named color palette (`colors.RED`, or `color="red"`). |
| [`icons`](reference/colors_icons.md) | Built-in marker shorthands (`icon="triangle"`, `"red-paddle"`). |

<br><br><br><br><br>
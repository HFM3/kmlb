# kmlb roadmap

Ideas for future releases. kmlb's scope is **making features on a map easy**: the
public API stays focused on building and styling features. The geodesic
measurements (`distance`, `bearing`, `destination`) are public building blocks,
while the underlying solvers (Vincenty, `_determinant`) stay private (`_`-prefixed)
infrastructure.

Nothing here is committed; these are candidates, roughly ordered by value vs.
effort. Open an issue or ask to pull any of them forward.

## Geometry & shapes (`kmlb.shapes`)
- **`circle(center, radius, steps=...)`**: an n-vertex ring around a center point.
  The natural companion to `wedge`; reuses `destination` and the internal geodesy.
- **`radial_line(origin, bearing, distance, name, ...)`**: one call for the common
  `line([origin, destination(origin, bearing, distance)], ...)` pattern.
- **`contains(polygon, point)` / point-in-polygon**: a true/false test built on
  the kept-private `_determinant` (the reason it was retained).

## Output formats
- **`kmz(...)`**: write a zipped `.kmz` document, optionally bundling custom icon
  images so a map is a single portable file.

## Richer KML features
- **Image overlays**: `ground_overlay` (an image draped on the map) and
  `screen_overlay` (a logo/legend pinned to the screen).
- **Time support**: `TimeStamp` / `TimeSpan` on features so Google Earth's time
  slider can animate them.
- **`StyleMap`**: paired normal/highlight styles for hover behavior.

## Convenience
- **`points_from_table(headers, rows)`**: build a folder of points in one call
  from tabular data (CSV-like rows).
- **Reading KML**: parse an existing `.kml` back into features, giving kmlb
  write↔read symmetry.

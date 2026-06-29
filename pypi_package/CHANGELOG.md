# Changelog

All notable changes to KMLB are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
from 1.0.0 onward.

> **Reconstructed history.** Releases `0.0.5`-`0.0.94` predate version control on
> this project; their entries are reconstructed from the published distributions
> on PyPI and the README history rather than from a commit log. Only milestone
> releases are listed below; the intervening patch releases up to `0.0.94` (the
> last version published before `0.1.0`) were maintenance and documentation
> updates. Exact per-release contents before `0.1.0` are approximate.

## [0.1.0]

A packaging and tooling modernization, with new geometry, color, and styling
helpers. The breaking changes are limited to the items called out under
**Changed**/**Fixed** below.

### Added
- Modern packaging: a `pyproject.toml` built with `hatchling`, a `src/` layout,
  and an explicit source-distribution allowlist so only the package, tests, and
  metadata are ever bundled.
- Type annotations across the public API, including `Literal` types for the
  closed `z_mode` set (`'CTG'`, `'RTG'`, `'ABS'`, `'CSF'`, `'RSF'`), and a
  `py.typed` marker so type checkers honor them for downstream users.
- Geodesy on the WGS-84 ellipsoid, public at the top level: `distance` and
  `bearing` between two coordinates, and `destination` to project from an origin
  along a bearing, the building block for radial lines and shapes.
- `desc` and `snip` on every placemark builder: free text/HTML for the
  description balloon (rendered above the `headers`/`attrs` table) and a short
  places-list summary.
- Optional elevation (z) in coordinates: `point`, `line`, and `polygon` now accept
  2-element `[lon, lat]` coordinates in addition to `[lon, lat, elev]`. When the
  elevation is omitted it defaults to `0`, which sits on the ground under the
  default `z_mode="CTG"`. An explicitly supplied `z_mode` is left
  unchanged. (`look_at` still requires a 3-element coordinate.)
- Sea-floor altitude modes for ocean and bathymetry work: `z_mode="CSF"`
  (`clampToSeaFloor`) and `"RSF"` (`relativeToSeaFloor`) on `point`, `line`,
  `polygon`, and `look_at`. These are Google `gx:` extensions, so they are
  written as `<gx:altitudeMode>` and the KML root now declares the `xmlns:gx`
  namespace.
- `kmlb.colors`: a curated palette of named colors, so any style color can be
  given by name (`color="red"`) or constant (`kmlb.colors.RED`).
- `kmlb.icons`: shorthand keys for Google Earth's built-in markers (shapes,
  colored pushpins, and colored paddles), so `point_style(icon="triangle")` or
  `icon="red-paddle"` instead of a full `mapfiles` URL.
- Flexible color input across every style builder: a bare hex string
  (`"#ff0000"`), a palette name (`"red"`), or a `(name|hex, opacity)` pair
  (`("red", 50)`), in addition to the original `(hex, opacity)` tuple.
- Automatic default styling: a `point`, `line`, or `polygon` built without a
  `style_to_use` now gets a tidy inline style, so quick maps look intentional.
  This changes the look of previously unstyled features; pass `style_to_use` to
  override.
- Extruded points: `point` accepts `extrude` to draw a vertical tether
  from a raised point down to the ground, and `point_style` gains `line_color`
  and `line_width` to color and size that tether.
- Documentation site built with Material for MkDocs: a step-by-step Boston
  tutorial and a full API reference, published at https://kmlb.dev

### Changed
- **Breaking:** the public API is limited to the feature, style, and document
  builders. The Vincenty solvers, three-point determinant, and WGS-84 constants
  moved from a public `gis_basics` module into a private `_geo` module; geodesy
  stays available through the public `distance`, `bearing`, and `destination`.
- **Breaking:** the optional arguments on every public builder are now
  keyword-only. A `*` follows the required positional arguments (for example
  `point(coords, name, *, ...)`, `point_style(name, *, ...)`,
  `kml(name, features, *, path=None, ...)`), so options such as `style_to_use`,
  `z_mode`, `headers`, and `styles` must be passed by name. This prevents
  same-typed arguments from being silently mis-assigned by position. Calls that
  already used keywords for these arguments are unaffected.
- **Breaking:** several common parameters were shortened for terser call sites.
  Update any keyword arguments accordingly:
  `description` to `desc`, `attributes` to `attrs`, `camera` to `cam`,
  `snippet` to `snip`, `altitude_mode` to `z_mode`, `extrude_to_ground` to
  `extrude`, and `folder`'s `loose_items` to `items`. Names left unchanged
  include `headers`, `style_to_use`, and `refresh_interval`.
- Relicensed from GPL-3.0 to MIT. The `LICENSE` file, the `pyproject.toml`
  license field, and each module's source header (a single
  `SPDX-License-Identifier: MIT` line) were updated together.
- Minimum supported Python is now 3.9 (was 3.8; 3.8 is end-of-life).

### Fixed
- `destination` returns a 2-element `[lon, lat]` when its origin has no elevation;
  feeding that result straight into `line` or `polygon` previously raised
  `IndexError` because those builders required a z value. With optional elevation
  they now accept it directly.
- `point` and `search_poi` now prefix their `styleUrl` with `#` (e.g. `#myStyle`),
  matching `line` and `polygon`, so a referenced shared style actually resolves in
  Google Earth. Previously the `#` was omitted and point/POI styles did not apply.
- Fixed an operator-precedence error in the Vincenty direct solver (`s / b * A`
  should be `s / (b * A)`) that introduced a small distance error in `destination`.

## [0.0.83]

### Added / Changed
- Expanded `base` functionality, including `networklink_kml` for network-link
  KML documents with refresh intervals.

## [0.0.82]

- Maintenance release.

## [0.0.81]

### Added
- `shapes.wedge`: a pie-wedge polygon builder composed from `polygon` and the
  Vincenty direct solver.

## [0.0.8]

### Added
- Documentation and example expansions across the point, line, polygon, style,
  folder, and document builders.

## [0.0.7]

### Added
- Styling helpers (`point_style`, `line_style`, `polygon_style`) and camera
  angles via `look_at`.

## [0.0.6]

### Added
- `gis_basics`: Vincenty inverse/direct solvers and the three-point determinant.

## [0.0.5]

### Added
- First broadly published release: the core `base` builders for points, lines,
  polygons, folders, and KML documents.

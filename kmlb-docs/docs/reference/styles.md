<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Styles</h2>
<p class="kmlb-hero__sub">Define a reusable style once, give it a name, and reference it from a feature's <code>style_to_use</code>. Plus automatic default styles.</p>
</div>

## point_style

Defines a reusable point style _(icon, color, scale, and label)_.

```python
point_style(name, *, icon="circle", color=("#ffff00", 100), scale=1.2,
            label_color=("#ffffff", 100), label_size=1.0,
            line_color=("#ffff00", 100), line_width=2.0) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Unique style ID, referenced by `point`'s `style_to_use`. |
| `icon` | `str` | Google circle | URL of the marker icon. |
| `color` | `tuple[str, int]` | `('#ffff00', 100)` | Icon `(hex color, opacity)`. |
| `scale` | `float` | `1.2` | Icon size. |
| `label_color` | `tuple[str, int]` | `('#ffffff', 100)` | Label `(hex color, opacity)`. |
| `label_size` | `float` | `1.0` | Label text size. |
| `line_color` | `tuple[str, int]` | `('#ffff00', 100)` | Tether line `(color, opacity)` for an extruded point. |
| `line_width` | `float` | `2.0` | Tether line thickness for an extruded point. |

!!! success "Returns"
    `Element`: a KML `Style` element with the given `id`.

!!! tip
    A catalog of ready-made icon URLs is at [kml4earth.appspot.com/icons.html](http://kml4earth.appspot.com/icons.html).

**Examples**

The simplest style: just a name

```python
kmlb.point_style("city")
```

Custom icon, color, and size

```python
kmlb.point_style("city", icon="triangle", color="red", scale=1.4)
```

Style the label too

```python
kmlb.point_style("city", icon="triangle", color="red",
                 label_color=("white", 100), label_size=1.2)
```

Color the tether for extruded points

```python
kmlb.point_style("tower", icon="circle", color="red",
                 line_color=("orange", 100), line_width=3)
```

---

## line_style

Defines a reusable line style.

```python
line_style(name, *, color=("#ff0000", 100), width=3.0,
           extrude_color=("#34c9eb", 35)) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Unique style ID. |
| `color` | `tuple[str, int]` | `('#ff0000', 100)` | Line `(hex color, opacity)`. |
| `width` | `float` | `3.0` | Line thickness. |
| `extrude_color` | `tuple[str, int]` | `('#34c9eb', 35)` | Fill `(hex color, opacity)` for the area below an extruded line. |

!!! success "Returns"
    `Element`: a KML `Style` element with the given `id`.

**Examples**

The simplest style: just a name

```python
kmlb.line_style("trail")
```

Custom color and width

```python
kmlb.line_style("trail", color="gold", width=4)
```

Set the fill for an extruded line

```python
kmlb.line_style("fence", color="gold", width=3, extrude_color=("teal", 35))
```

---

## polygon_style

Defines a reusable polygon style.

```python
polygon_style(name, *, fill_color=("#03cafc", 40),
              outline_color=("#fcdf03", 100), outline_width=3.0) -> Element
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Unique style ID. |
| `fill_color` | `tuple[str, int]` | `('#03cafc', 40)` | Fill `(hex color, opacity)`. |
| `outline_color` | `tuple[str, int]` | `('#fcdf03', 100)` | Outline `(hex color, opacity)`. |
| `outline_width` | `float` | `3.0` | Outline thickness. |

!!! success "Returns"
    `Element`: a KML `Style` element with the given `id`.

**Examples**

The simplest style: just a name

```python
kmlb.polygon_style("plaza")
```

Custom fill and outline

```python
kmlb.polygon_style("plaza", fill_color=("purple", 40),
                   outline_color="purple", outline_width=2)
```

---

## Default styles

A feature created without a `style_to_use` is given a tidy inline style
automatically, so a quick map looks intentional. Pass a `style_to_use` (with one
of the style builders above) to override any of these.

| Feature | Stroke / outline | Fill | Notes |
|---|---|---|---|
| `point` | yellow icon `#ffff00` | none | White label. An `extrude` point also gets a yellow `#ffff00` 2&nbsp;px tether down to the ground. |
| `line` | red `#ff0000`, 3&nbsp;px | none | An `extrude` line fills its wall to match a 3D polygon (`#495a7f` at 45%). |
| `polygon` (flat) | yellow `#ffff00`, 2&nbsp;px | `#00aaff` at 30% | The default for a ground polygon. |
| `polygon` (3D) | orange `#ffaa00`, 2&nbsp;px | `#495a7f` at 45% | Used when the polygon is `extrude=True`. |

<br><br><br><br><br>
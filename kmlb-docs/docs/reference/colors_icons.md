<div class="kmlb-hero" markdown>
<div class="kmlb-hero__eyebrow">Reference</div>
<h2 class="kmlb-hero__title">Colors &amp; Icons</h2>
<p class="kmlb-hero__sub">Pick a color by name, hex, or <code>(color, opacity)</code> pair; pick a marker by shorthand, constant, or full URL. Skip the style entirely and a feature still looks good with default styling.</p>
</div>

Pick a color by name (`"red"`), a hex string (`"#ff0000"`), or a
`(color, opacity)` pair (`("red", 50)`); or use a `kmlb.colors` constant. Same
for markers: a shorthand (`"triangle"`, `"red-paddle"`), a `kmlb.icons` constant, or
a full URL. Skip the style entirely and a feature still looks good.

```python
kmlb.point_style("city", color="red", icon="triangle")
kmlb.line_style("route", color=("teal", 80))       # name + opacity

# A polygon given no style_to_use falls back to kmlb's built-in default styling,
# so it still looks good. 'ring' is one closed list of [lon, lat] coordinates
# (the first and last point match).
ring = [[-71.06, 42.36], [-71.05, 42.36], [-71.05, 42.35], [-71.06, 42.35], [-71.06, 42.36]]
kmlb.polygon([ring], "Parking Lot")                 # no style_to_use, default style applied
```

## Color palette

<ul class="swatch-grid">
<li style="--c:#000000">black</li>
<li style="--c:#0000ff">blue</li>
<li style="--c:#a52a2a">brown</li>
<li style="--c:#00ffff">cyan</li>
<li style="--c:#ffd700">gold</li>
<li style="--c:#808080">gray</li>
<li style="--c:#008000">green</li>
<li style="--c:#f2a81d">kmlb_amber</li>
<li style="--c:#36c23f">kmlb_green</li>
<li style="--c:#e8472a">kmlb_red</li>
<li style="--c:#1b8a9b">kmlb_teal</li>
<li style="--c:#00ff00">lime</li>
<li style="--c:#ff00ff">magenta</li>
<li style="--c:#800000">maroon</li>
<li style="--c:#000080">navy</li>
<li style="--c:#808000">olive</li>
<li style="--c:#ffa500">orange</li>
<li style="--c:#ffc0cb">pink</li>
<li style="--c:#800080">purple</li>
<li style="--c:#ff0000">red</li>
<li style="--c:#c0c0c0">silver</li>
<li style="--c:#008080">teal</li>
<li style="--c:#ffffff">white</li>
<li style="--c:#ffff00">yellow</li>
</ul>

## Marker shorthands

### Shapes & symbols

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/shapes/arrow.png" alt="" loading="lazy" class="off-glb" />arrow</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/caution.png" alt="" loading="lazy" class="off-glb" />caution</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/placemark_circle.png" alt="" loading="lazy" class="off-glb" />circle</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/open-diamond.png" alt="" loading="lazy" class="off-glb" />diamond</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/donut.png" alt="" loading="lazy" class="off-glb" />donut</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/flag.png" alt="" loading="lazy" class="off-glb" />flag</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/info.png" alt="" loading="lazy" class="off-glb" />info</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/info-i.png" alt="" loading="lazy" class="off-glb" />info-i</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/poi.png" alt="" loading="lazy" class="off-glb" />poi</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/shaded_dot.png" alt="" loading="lazy" class="off-glb" />shaded-dot</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/placemark_square.png" alt="" loading="lazy" class="off-glb" />square</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/star.png" alt="" loading="lazy" class="off-glb" />star</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/target.png" alt="" loading="lazy" class="off-glb" />target</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/triangle.png" alt="" loading="lazy" class="off-glb" />triangle</li>
</ul>

### Places & services

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/shapes/bars.png" alt="" loading="lazy" class="off-glb" />bar</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/camera.png" alt="" loading="lazy" class="off-glb" />camera</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/coffee.png" alt="" loading="lazy" class="off-glb" />coffee</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/dining.png" alt="" loading="lazy" class="off-glb" />dining</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/firedept.png" alt="" loading="lazy" class="off-glb" />fire</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/gas_stations.png" alt="" loading="lazy" class="off-glb" />fuel</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/grocery.png" alt="" loading="lazy" class="off-glb" />grocery</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/hospitals.png" alt="" loading="lazy" class="off-glb" />hospital</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/lodging.png" alt="" loading="lazy" class="off-glb" />lodging</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/parking_lot.png" alt="" loading="lazy" class="off-glb" />parking</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/phone.png" alt="" loading="lazy" class="off-glb" />phone</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/police.png" alt="" loading="lazy" class="off-glb" />police</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/ranger_station.png" alt="" loading="lazy" class="off-glb" />ranger</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/shopping.png" alt="" loading="lazy" class="off-glb" />shopping</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/toilets.png" alt="" loading="lazy" class="off-glb" />toilets</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/water.png" alt="" loading="lazy" class="off-glb" />water</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/webcam.png" alt="" loading="lazy" class="off-glb" />webcam</li>
</ul>

### Recreation & outdoors

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/shapes/campfire.png" alt="" loading="lazy" class="off-glb" />campfire</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/campground.png" alt="" loading="lazy" class="off-glb" />campground</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/cycling.png" alt="" loading="lazy" class="off-glb" />cycling</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/fishing.png" alt="" loading="lazy" class="off-glb" />fishing</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/golf.png" alt="" loading="lazy" class="off-glb" />golf</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/hiker.png" alt="" loading="lazy" class="off-glb" />hiker</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/picnic.png" alt="" loading="lazy" class="off-glb" />picnic</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/trail.png" alt="" loading="lazy" class="off-glb" />trail</li>
</ul>

### Transport

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/shapes/bus.png" alt="" loading="lazy" class="off-glb" />bus</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/ferry.png" alt="" loading="lazy" class="off-glb" />ferry</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/heliport.png" alt="" loading="lazy" class="off-glb" />heliport</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/marina.png" alt="" loading="lazy" class="off-glb" />marina</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/airports.png" alt="" loading="lazy" class="off-glb" />plane</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/rail.png" alt="" loading="lazy" class="off-glb" />rail</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/sailing.png" alt="" loading="lazy" class="off-glb" />sailing</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/cabs.png" alt="" loading="lazy" class="off-glb" />taxi</li>
<li><img src="https://maps.google.com/mapfiles/kml/shapes/truck.png" alt="" loading="lazy" class="off-glb" />truck</li>
</ul>

### Pushpins

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png" alt="" loading="lazy" class="off-glb" />blue-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png" alt="" loading="lazy" class="off-glb" />green-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/ltblu-pushpin.png" alt="" loading="lazy" class="off-glb" />ltblue-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/pink-pushpin.png" alt="" loading="lazy" class="off-glb" />pink-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/purple-pushpin.png" alt="" loading="lazy" class="off-glb" />purple-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png" alt="" loading="lazy" class="off-glb" />red-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png" alt="" loading="lazy" class="off-glb" />white-pin</li>
<li><img src="https://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png" alt="" loading="lazy" class="off-glb" />yellow-pin</li>
</ul>

### Paddles

<ul class="icon-grid">
<li><img src="https://maps.google.com/mapfiles/kml/paddle/blu-circle.png" alt="" loading="lazy" class="off-glb" />blue-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/grn-circle.png" alt="" loading="lazy" class="off-glb" />green-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png" alt="" loading="lazy" class="off-glb" />ltblue-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/pink-circle.png" alt="" loading="lazy" class="off-glb" />pink-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/purple-circle.png" alt="" loading="lazy" class="off-glb" />purple-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/red-circle.png" alt="" loading="lazy" class="off-glb" />red-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/wht-circle.png" alt="" loading="lazy" class="off-glb" />white-paddle</li>
<li><img src="https://maps.google.com/mapfiles/kml/paddle/ylw-circle.png" alt="" loading="lazy" class="off-glb" />yellow-paddle</li>
</ul>


<br><br><br><br><br>
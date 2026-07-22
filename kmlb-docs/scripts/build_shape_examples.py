"""Build the combined shape_examples.kml linked at the top of the shapes docs.

Gathers every builder example on the shapes reference page into one KML so the
geometry can be inspected in Google Earth from a single download:

  * the 2D scene, imported live from the package's shapes_2d_demo.py,
  * every 3D-solid / fresnel example, executed straight from the ```python blocks
    in docs/reference/shapes.md (so the file always matches the docs),
  * the "solids along a path" Logan scene, imported from shapes_3d_path_demo.py.

Each shape lands in its own collapsed folder. hex_grid is intentionally left out
of the combined file (its parking-lot example overlaps the fishnet in the same
lot); it still appears in the docs.

Lives in the tracked kmlb-docs tree because its output is a docs asset. It reaches
back into ../../pypi_package for the library source and the demo scenes. Run it
from anywhere:

    py scripts/build_shape_examples.py     # from the kmlb-docs root
"""

import ast
import importlib.util
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "pypi_package", "src")
EXAMPLES = os.path.join(HERE, "..", "..", "pypi_package", "examples")
MD = os.path.join(HERE, "..", "docs", "reference", "shapes.md")
OUT = os.path.join(HERE, "..", "docs", "assets", "shape_examples.kml")

sys.path.insert(0, SRC)

import kmlb
from kmlb import base, shapes as S

# Shapes that come from the 2D scene demo, so they are not also pulled from the
# doc code blocks (which would double them up).
DEMO_2D = {"circle", "ellipse", "rectangle", "ngon", "annulus", "arc", "wedge",
           "ribbon", "con_rings", "fishnet", "hex_field"}

# Left out of the combined file (still documented): its parking-lot example sits
# on top of the fishnet in the same lot.
SKIP = {"hex_grid"}


def _load(mod_name, filename):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(EXAMPLES, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 2D scene and the Logan path scene, imported live (unpatched) from their demos.
demo_2d = _load("shapes_2d_demo", "shapes_2d_demo.py")
logan_solids = _load("shapes_3d_path_demo", "shapes_3d_path_demo.py").solids

# Wrap every shapes.* builder so calls made while exec-ing the doc blocks are
# recorded, and stub kmlb.kml so those blocks do not each write a file.
recorded = []
for name in list(S.__all__):
    fn = getattr(S, name, None)
    if callable(fn):
        def make(fn, name):
            def w(*a, **k):
                el = fn(*a, **k)
                recorded.append((name, el))
                return el
            return w
        setattr(S, name, make(fn, name))
kmlb.kml = lambda *a, **k: None

for code in re.findall(r"```python\n(.*?)\n```", open(MD, encoding="utf-8").read(), re.S):
    # skip signature snippets, the demo scene blocks (imported above), and prose
    if ("-> Element" in code and "kmlb." not in code) or "features = [" in code \
            or "solids = [" in code or "kmlb." not in code:
        continue
    try:
        exec(compile(ast.parse(code), "<doc>", "exec"), {"kmlb": kmlb})
    except Exception as e:  # noqa: BLE001 - report and keep going
        print("  ! skipped a doc block:", e)

groups = defaultdict(list)
for name, el in recorded:
    if name not in DEMO_2D and name not in SKIP:
        groups[name].append(el)

folders = [base.folder("2D shapes (from shapes_2d_demo)", demo_2d.features,
                       collapsed=True, hidden=False)]
for name in [n for n in S.__all__ if n in groups]:
    items = groups[name]
    for i, el in enumerate(items, 1):
        nm = el.find("name")
        if nm is not None:
            nm.text = f"{name} #{i}" if len(items) > 1 else name
    folders.append(base.folder(f"{name} ({len(items)})", items, collapsed=True, hidden=False))

folders.append(base.folder("3D solids along a path (Logan, from shapes_3d_path_demo)",
                           logan_solids, collapsed=True, hidden=False))

base.kml("kmlb shape examples",
         [base.folder("kmlb shape examples", folders, collapsed=False, hidden=False)],
         path=OUT)
print(f"wrote {os.path.normpath(OUT)} ({len(folders)} folders)")

"""
Build the self-contained CAD viewer page from viewer_template.html and the
glTF exports in exports/ (embedded as data URIs, ~8 MB total).

    python build_viewer.py            # → out/pyfridge_cad_assembly.html

Open the result in any browser: it loads the actual exported assembly
(same geometry as the STEP), with a STEP part tree, closed/open states,
ghost shell, per-layer toggles and click-to-highlight.
"""
import base64
import os

HERE = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
for key, fn in (("__GLB_CLOSED__", "LFXS27566S_closed.glb"), ("__GLB_OPEN__", "LFXS27566S_open.glb")):
    with open(os.path.join(HERE, "exports", fn), "rb") as f:
        tpl = tpl.replace(key, base64.b64encode(f.read()).decode())
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
out = os.path.join(HERE, "out", "pyfridge_cad_assembly.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(tpl)
print("wrote", out, f"({len(tpl) / 1e6:.1f} MB)")

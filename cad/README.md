# CAD / 3D Reference Models

The physical baseline for pyfridge: a part-by-part model of the reference refrigerator,
built from LG's own documents before any coordinate data is locked into
`sql/schema.sql` / `sql/seed.sql` and before the gantry frame is designed around it.

Each `.html` is a self-contained Three.js scene — open it in a browser, no build step.

## Reference unit: LG LFXS27566S

27 cu ft-class (26.6 actual: 17.7 fridge / 8.9 freezer) French door, Door-in-Door,
in-door ice maker, linear compressor. Chosen as the closest published match to the
"LG French Door, 34"W × 42"H fridge opening" the README has always cited.

Sources (facts extracted; LG's PDFs are copyrighted and are **not** committed here):
- LG spec sheet — https://www.lg.com/us/support/products/documents/LFXS27566S%20Spec%20Sheet.pdf
- LG service manual MFL62188073 (LFXS27566*, 109 pp) — https://research.encompass.com/ZEN/sm/LFXS27566S.pdf
- LG owner's manual MFL70761734 (LFXS28566* sibling, same chassis) — https://pdf.lowes.com/productdocuments/fb36fc23-32f5-4159-b543-7ecfc1f73c12/61288328.pdf
- Exploded parts diagrams — https://www.appliancepartspros.com/parts-for-lg-lfxs27566s-00.html

## Files

| File | What it is |
|---|---|
| `reference_unit.html` | Full assembly, 218 registered parts. Closed / Open / Ghost views, door-angle slider, per-layer toggles (shell, doors, fresh-food, freezer, refrigeration & controls, hinges/base, LG dimension lines A–I). Every mesh carries its LG part number and a C/P confidence tag; hover for dimensions, click to pin, filterable parts list. Browser-verified. |
| `spec/dimensions.md` | Every dimension we have, each tagged **confirmed** (LG document) / **measured** (owner) / **placeholder** (no source yet). |
| `spec/parts.md` | Full parts inventory with LG part numbers, grouped by assembly. |

## Confidence, current state

**Confirmed from LG documents:** exterior envelope 35¾ × 69¾ (hinge top) × 32⅞ in;
depth without doors 29 in; with handles 35⅜ in; door-open depth 47⅝ in; width at 90°
open 39¼ in (44¼ with handle); bar handles (2½ in protrusion); hidden top hinges with
lever latch, door lifts off middle hinge pin; auto-closing hinge under 30°; dispenser
on the left door; Door-in-Door ("Home Bar") on the right door, button release on the
handle; foldable heated mullion on the left door; in-door Slim SpacePlus ice maker in
the left door; 4 cantilever glass shelves (1 folding), 2 humidity crispers, full-width
Glide N' Serve drawer, 9 door bins; freezer = one drawer front, Durabase basket with
divider + upper pull-out tray.

**Still placeholder (no LG document breaks it out):** per-door width split, dispenser
recess size and position, freezer-drawer front height, handle bar diameter, kick-grille
height and setback, wall/insulation thickness. The fridge-section opening is **derived**
(≈ 818 × 1066 × 575 mm) from LG's 17.7 cu ft capacity and exterior width — it appears in
no LG document and must be confirmed on a unit; see `spec/dimensions.md`.

## Roadmap for this directory

1. ~~Exterior shell~~ → verified against spec sheet + service manual
2. Interior, doors open: shelves, crispers, Glide N' Serve, door bins, Door-in-Door
   case, in-door ice bin, mullion, freezer basket + tray, hinges (in progress)
3. Measure the real fridge-section opening; reconcile with `sql/schema.sql` X/Y/Z
   limits (issue #12)
4. Only then: the gantry frame from the README hardware section

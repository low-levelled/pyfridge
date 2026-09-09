# CAD / 3D Reference Models

Working visualizations of the physical hardware, built before we lock in coordinate
data in `sql/schema.sql` / `sql/seed.sql`. Each file is a self-contained Three.js
scene — open it directly in a browser, no build step.

## `reference_unit.html` — exterior shell (v1)

A dimensioned model of the reference refrigerator: LG French-door class, ~28 cu ft,
recessed pocket handles, matching the `34"W × 42"H` fridge-section interior opening
already cited in the README and baked into `sql/schema.sql` (864mm × 1066mm).

**What's verified against real spec sheets:**
- Exterior envelope — 35.75"W × 70"H × 34.4"D
- Fridge-section interior opening — 34"W × 42"H (matches existing schema coordinates)
- Pocket-handle styling, PrintProof-stainless finish, no top branding strip

**What's a placeholder, not yet confirmed against an LG diagram or photo:**
- Door width split (52/48, dispenser side wider)
- Dispenser size/position on the left door
- Freezer-drawer-to-doors height ratio

Next step before trusting this for hardware fit-checks: verify against an actual
photo or spec sheet of our specific model, then move on to the interior — zones,
shelf/drawer coordinates (this is what issue #12 is asking for), and the gantry
frame described in the README's hardware integration section.

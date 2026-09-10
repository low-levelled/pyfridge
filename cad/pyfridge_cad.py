"""
pyfridge reference unit — parametric CAD of the LG LFXS27566S in CadQuery.

Exports a STEP assembly (part tree with LG part numbers), plus STL and glTF
meshes. Same dimensions and confidence tags as reference_unit.html and
cad/spec/dimensions.md: C = confirmed in an LG document, D = derived from LG
numbers, P = placeholder.

Usage:
    python pyfridge_cad.py                 # closed unit → out/LFXS27566S_closed.*
    python pyfridge_cad.py --open          # doors 105°, drawer out → out/LFXS27566S_open.*
    python pyfridge_cad.py --no-mech       # skip machine-room / control parts

Requires: pip install cadquery   (Python 3.9–3.13)

Frame: X right, Y back→front, Z up. Origin: floor level, cabinet centre, rear face.
"""
import argparse
import math
import os
import sys

import cadquery as cq

# ---------------------------------------------------------------------------
# Dimensions (mm)
# ---------------------------------------------------------------------------
MM = dict(
    EXT_W=908,        # C  35¾ in
    CASE_H=1737,      # C  68⅜ in to top of case
    HINGE_TOP=1772,   # C  69¾ in to top of hinge cover
    CAB_D=737,        # C  29 in without door
    DOOR_T=98,        # D  32⅞ − 29 in
    HANDLE_P=63.5,    # D  35⅜ − 32⅞ in
    HANDLE_DIA=28,    # P
    KICK_H=80,        # P
    FZ_H=530,         # P
    GAP_H=10,         # P
    TOP_REVEAL=15,    # P
    CENTER_GAP=6,     # P
    WALL_SIDE=45,     # P
    WALL_TOP=33,      # P
    WALL_BACK=162,    # D  737 − 575
    FF_W=818, FF_H=1066, FF_D=575,  # D  from 17.7 cu ft + 908 mm exterior
    FZ_FLOOR=100,     # P
    DIV_T=38,         # P
)
M = MM
M["DOOR_Y0"] = M["KICK_H"] + M["FZ_H"] + M["GAP_H"]            # 620
M["DOOR_H"] = M["CASE_H"] - M["TOP_REVEAL"] - M["DOOR_Y0"]     # 1102
M["DOOR_W"] = (M["EXT_W"] - M["CENTER_GAP"]) / 2               # 451
M["FF_Y0"] = M["DOOR_Y0"] + (M["DOOR_H"] - M["FF_H"]) / 2      # 638
M["FF_Y1"] = M["FF_Y0"] + M["FF_H"]
M["FF_Z0"] = M["CAB_D"] - M["FF_D"]                            # 162 (rear of cavity, from cabinet back)
M["FZ_Y1"] = M["FF_Y0"] - M["DIV_T"]                           # 600

W, H, D, T = M["EXT_W"], M["CASE_H"], M["CAB_D"], M["DOOR_T"]

# ---------------------------------------------------------------------------
# Colours per layer (RGBA 0–1)
# ---------------------------------------------------------------------------
COL = dict(
    steel=(0.80, 0.82, 0.83, 1.0),
    liner=(0.94, 0.95, 0.95, 1.0),
    clear=(0.75, 0.86, 0.88, 0.45),
    glass=(0.85, 0.93, 0.94, 0.30),
    dark=(0.11, 0.12, 0.13, 1.0),
    grey=(0.55, 0.58, 0.59, 1.0),
    alu=(0.79, 0.80, 0.82, 1.0),
    black=(0.13, 0.14, 0.15, 1.0),
    copper=(0.72, 0.45, 0.20, 1.0),
    pcb=(0.12, 0.36, 0.23, 1.0),
    foam=(0.91, 0.87, 0.72, 1.0),
    gasket=(0.05, 0.05, 0.05, 1.0),
    led=(0.92, 0.96, 1.0, 1.0),
)


# ---------------------------------------------------------------------------
# Geometry helpers. All take web-model style coordinates: x right, y UP, z
# back→front; they are mapped to CadQuery's X, Y(front), Z(up) frame.
# ---------------------------------------------------------------------------
def V(x, yup, zf):
    return cq.Vector(x, zf, yup)


def box(w, h, d, x, yup, zf):
    """Box of width w (X), height h (up), depth d (front), centred at (x, yup, zf)."""
    return cq.Workplane("XY").box(w, d, h).translate(V(x, yup, zf))


def cyl_v(r, length, x, yup, zf):
    """Vertical cylinder (axis up)."""
    return cq.Workplane("XY").cylinder(length, r).translate(V(x, yup, zf))


def cyl_x(r, length, x, yup, zf):
    """Cylinder along X."""
    return cq.Workplane("YZ").cylinder(length, r).translate(V(x, yup, zf))


def cyl_z(r, length, x, yup, zf):
    """Cylinder along depth (back→front)."""
    return cq.Workplane("XZ").cylinder(length, r).translate(V(x, yup, zf))


def rounded_slab(w, h, d, r, x, yup, zf):
    """Side-Rounded door slab: fillet the vertical edges and soften the face edges."""
    s = cq.Workplane("XY").box(w, d, h)
    s = s.edges("|Z").fillet(r)
    s = s.edges(">Y or <Y").fillet(min(6, d / 4))
    return s.translate(V(x, yup, zf))


def frame_bin(w, h, d, x, yup, zf, wall=4):
    """Open-top bin: floor, back, two sides, (front face is the door when door-mounted)."""
    b = (
        box(w, wall, d, x, yup + wall / 2, zf)
        .union(box(w, h, wall, x, yup + h / 2, zf - d / 2 + wall / 2))
        .union(box(wall, h, d, x - w / 2 + wall / 2, yup + h / 2, zf))
        .union(box(wall, h, d, x + w / 2 - wall / 2, yup + h / 2, zf))
    )
    return b


def drawer(w, h, d, x, yup, zf, wall=4, front=12):
    return (
        box(w, wall, d, x, yup + wall / 2, zf)
        .union(box(w, h, front, x, yup + h / 2, zf + d / 2 - front / 2))
        .union(box(w, h, wall, x, yup + h / 2, zf - d / 2 + wall / 2))
        .union(box(wall, h, d, x - w / 2 + wall / 2, yup + h / 2, zf))
        .union(box(wall, h, d, x + w / 2 - wall / 2, yup + h / 2, zf))
    )


class Builder:
    def __init__(self, name, with_mech=True):
        self.asm = cq.Assembly(name=name)
        self.with_mech = with_mech
        self.count = 0

    def add(self, shape, name, pn, layer, tag, color, parent=None):
        if layer == "mech" and not self.with_mech:
            return
        self.count += 1
        label = f"{layer}.{self.count:03d} {name} [{pn}] ({tag})"
        (parent or self.asm).add(shape, name=label, color=cq.Color(*COL[color]))


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(open_state=False, with_mech=True):
    b = Builder("LG_LFXS27566S", with_mech)
    add = b.add

    # ---- cabinet shell: five panels + divider + ABS liners --------------
    ws, wt, wb = M["WALL_SIDE"], M["WALL_TOP"], M["WALL_BACK"]
    kh, ff = M["KICK_H"], M["FZ_FLOOR"]
    add(box(ws, H - kh, D, -W / 2 + ws / 2, kh + (H - kh) / 2, D / 2), "Cabinet side panel L", "—", "shell", "C", "steel")
    add(box(ws, H - kh, D, W / 2 - ws / 2, kh + (H - kh) / 2, D / 2), "Cabinet side panel R", "—", "shell", "C", "steel")
    add(box(W, wt, D, 0, H - wt / 2, D / 2), "Cabinet top panel", "—", "shell", "C", "steel")
    add(box(W, H - kh, wb, 0, kh + (H - kh) / 2, wb / 2), "Cabinet back panel + rear insulation", "—", "shell", "D", "steel")
    add(box(W, ff - kh, D, 0, kh + (ff - kh) / 2, D / 2), "Cabinet floor", "—", "shell", "P", "steel")
    add(box(W - 2 * ws, M["DIV_T"], D - wb, 0, M["FZ_Y1"] + M["DIV_T"] / 2, wb + (D - wb) / 2), "Fridge/freezer divider (foam)", "—", "shell", "P", "foam")

    fw, fh, fd, z0 = M["FF_W"], M["FF_H"], M["FF_D"], M["FF_Z0"]
    zc = z0 + fd / 2
    lt = 3
    liner = (
        box(fw, lt, fd, 0, M["FF_Y1"] - lt / 2, zc)
        .union(box(fw, lt, fd, 0, M["FF_Y0"] + lt / 2, zc))
        .union(box(lt, fh, fd, -fw / 2 + lt / 2, M["FF_Y0"] + fh / 2, zc))
        .union(box(lt, fh, fd, fw / 2 - lt / 2, M["FF_Y0"] + fh / 2, zc))
        .union(box(fw, fh, lt, 0, M["FF_Y0"] + fh / 2, z0 + lt / 2))
    )
    add(liner, "Fresh-food inner liner (ABS) 818x1066x575", "—", "shell", "D", "liner")
    fzh = M["FZ_Y1"] - ff
    fzl = (
        box(fw, lt, fd, 0, ff + lt / 2, zc)
        .union(box(fw, lt, fd, 0, M["FZ_Y1"] - lt / 2, zc))
        .union(box(lt, fzh, fd, -fw / 2 + lt / 2, ff + fzh / 2, zc))
        .union(box(lt, fzh, fd, fw / 2 - lt / 2, ff + fzh / 2, zc))
        .union(box(fw, fzh, lt, 0, ff + fzh / 2, z0 + lt / 2))
    )
    add(fzl, "Freezer inner liner (ABS)", "—", "shell", "P", "liner")

    # ---- base, hinges, trim -------------------------------------------
    add(box(W - 40, kh - 12, 40, 0, kh / 2 + 2, D + T - 95), "Toe grille / lower cover", "ACQ85891302", "base", "P", "dark")
    for s, side in ((-1, "L"), (1, "R")):
        add(cyl_v(16, kh, s * (W / 2 - 70), kh / 2, D - 60), f"Leveling leg front {side}", "AFC73349801", "base", "C", "black")
        add(cyl_x(28, 24, s * (W / 2 - 90), 28, 120), f"Rear roller {side}", "MHA62513601", "base", "C", "dark")
        hinge = (
            box(120, 6, 110, s * (W / 2 - 70), H + 3, D + 20)
            .union(cyl_v(6, 30, s * (W / 2 - 24), H - 12, D + 22))
            .union(box(40, 8, 18, s * (W / 2 - 95), H + 10, D - 10))
        )
        add(hinge, f"Upper hinge {side} (plate, pin, lever latch)", "AEH74216501" if side == "L" else "AEH73816806", "base", "C", "alu")
        ch = M["HINGE_TOP"] - H - 6
        add(box(110, ch, 130, s * (W / 2 - 65), H + 6 + ch / 2, D - 30), f"Hinge cover {side}", "ACQ86274031" if side == "L" else "ACQ86664715", "base", "C", "dark")
        mid = (
            box(70, 8, 80, s * (W / 2 - 45), M["DOOR_Y0"] - 5, D + 15)
            .union(cyl_v(7, 40, s * (W / 2 - 24), M["DOOR_Y0"] + 15, D + 22))
        )
        add(mid, f"Middle hinge {side} (pin)", "AEH73816902" if side == "L" else "AEH73816904", "base", "C", "alu")
        add(cyl_v(9, 14, s * (W / 2 - 24), M["DOOR_Y0"] + 2, D + 22), f"Shaft support bushing {side}", "MBF62704701", "base", "C", "grey")
        add(box(26, 10, 26, s * (W / 2 - 110), M["DOOR_Y0"] - 5, D + 60), f"Door stopper {side}", "MJB62830601" if side == "L" else "MJB63449803", "base", "C", "grey")
        add(box(70, 6, 60, s * (W / 2 - 60), M["DOOR_Y0"] + 4, D + 30), f"Door support bracket {side}", "MJH63894301", "base", "C", "alu")
        add(box(6, H - kh - 40, 40, s * (W / 2 + 3), kh + (H - kh) / 2, D - 20), f"Decor panel {side}", "ACW73717312" if side == "L" else "ACW73717317", "base", "C", "alu")
    add(box(30, 10, 30, 0, M["DOOR_Y0"] - 5, D + 40), "Door stopper, centre", "AJC73112301", "base", "C", "grey")
    for s, side in ((-1, "L"), (1, "R")):
        add(box(24, 8, 24, s * (W / 2 - 24), H + 7, D + 70), f"Door stopper {side}, upper hinge", "MJB63649801", "base", "C", "grey")
        add(cyl_v(10, 6, s * (W / 2 - 24), H + 14, D + 22), f"Hinge cap {side}", "MBL65077501", "base", "C", "grey")
        ring = cq.Workplane("XY").circle(10.6).circle(7.4).extrude(3).translate(V(s * (W / 2 - 24), M["DOOR_Y0"] + 42, D + 22))
        add(ring, f"Snap ring {side} (hinge pin)", "MGZ62766901", "base", "C", "alu")
        add(box(60, 6, 50, s * (W / 2 - 60), kh + M["FZ_H"] + 4, D + 30), f"Door bracket {side} (freezer)", "MEG61899901", "base", "C", "alu")
        add(box(W / 2 - 140, 10, 30, s * (W / 4 + 10), H - M["TOP_REVEAL"] / 2, D + T - 15), f"Decor cover {side} (top reveal)", "MCR64758001" if side == "L" else "MCR64776601", "base", "C", "dark")
        add(box(40, 40, 20, s * (W / 2 - 80), H - 8, D + T - 10), f"Decor cover corner {side}", "MCR64788601", "base", "C", "dark")
        add(cyl_x(20, 16, s * (W / 2 - 140), 20, 90), f"Rear roller {side}, inner", "MHA62652801" if side == "L" else "4580JQ3001B", "base", "C", "dark")
    add(box(W - 60, 6, 30, 0, 4, D - 20), "Lower cover assembly, rear", "ACQ85891306", "base", "C", "dark")

    # ---- doors (sub-assemblies, hinge axis at origin) -------------------
    Wd, Hd = M["DOOR_W"], M["DOOR_H"]
    hp, hr = M["HANDLE_P"], M["HANDLE_DIA"] / 2
    hinge_z = 20

    def door(side):
        sub = cq.Assembly(name=f"door_{side}")
        s = 1 if side == "L" else -1
        # door-local: x from hinge (0) toward centre; mirrored later for the right door via s
        def X(x):
            return s * x
        slab = rounded_slab(Wd, Hd, T - 12, 14, X(Wd / 2), Hd / 2, 12 + (T - 12) / 2 - hinge_z)
        add(slab, f"{'Left' if side == 'L' else 'Right'} refrigerator door slab (PCM stainless, foam)", "ADD74296905" if side == "L" else "ADC74665810", "doors", "D", "steel", sub)
        add(box(Wd - 16, Hd - 16, 12, X(Wd / 2), Hd / 2, 6 - hinge_z), f"Door liner {side}", "—", "doors", "P", "liner", sub)
        gw = 14
        gasket = (
            box(Wd - 20, gw, 10, X(Wd / 2), Hd - 14, -5 - hinge_z)
            .union(box(Wd - 20, gw, 10, X(Wd / 2), 14, -5 - hinge_z))
            .union(box(gw, Hd - 20, 10, X(14), Hd / 2, -5 - hinge_z))
            .union(box(gw, Hd - 20, 10, X(Wd - 14), Hd / 2, -5 - hinge_z))
        )
        add(gasket, f"Door gasket {side}", "ADX73550627", "doors", "C", "gasket", sub)
        ln = Hd * 0.78
        bar = cyl_v(hr, ln, X(Wd - 58), Hd / 2, T + hp - hr - hinge_z)
        for k in (-1, 1):
            bar = bar.union(cyl_z(9, hp - hr, X(Wd - 58), Hd / 2 + k * (ln / 2 - 60), T + (hp - hr) / 2 - hinge_z))
        add(bar, f"Bar handle {side} + studs (2.5 in protrusion)", "AED73593202", "doors", "C", "alu", sub)
        # handle hardware
        for k, nm in ((-1, "lower"), (1, "upper")):
            add(cyl_z(hr + 0.5, 6, X(Wd - 58), Hd / 2 + k * (ln / 2 + 3), T + hp - hr - hinge_z), f"Handle end cap {side} {nm}", "MBL65278201", "doors", "C", "dark", sub)
            add(box(24, 24, 6, X(Wd - 58), Hd / 2 + k * (ln / 2 - 60), T + 3 - hinge_z), f"Handle mounting bracket {side} {nm}", "AEJ73440302", "doors", "C", "alu", sub)
            add(cyl_z(5, 20, X(Wd - 58), Hd / 2 + k * (ln / 2 - 60), T - 8 - hinge_z), f"Handle mounting stud {side} {nm} (1/4 in Allen)", "MJB63190001", "doors", "C", "alu", sub)
        add(box(30, ln - 100, 4, X(Wd - 58), Hd / 2, T + 2 - hinge_z), f"Decor handle cover {side}", "MCR64995701" if side == "L" else "MCR64995702", "doors", "C", "dark", sub)
        add(box(Wd - 40, 6, 4, X(Wd / 2), 8, -2 - hinge_z), f"Gasket holder {side}", "MEG64120401", "doors", "C", "grey", sub)
        add(box(12, 26, 10, X(30), Hd - 30, -5 - hinge_z), f"Door position magnet {side}", "EBF62234513", "doors", "C", "dark", sub)
        if side == "L":
            dW, dH, cx, cy = 241, 356, Wd * 0.5, Hd * 0.55
            add(box(dW, dH, 20, X(cx), cy, T - 10 - hinge_z), "Dispenser recess + panel", "ACQ86599630", "doors", "P", "dark", sub)
            add(box(dW * 0.55, 14, 10, X(cx), cy - dH * 0.28, T + 2 - hinge_z), "Dispenser lever (paddle)", "MFC62709701", "doors", "C", "dark", sub)
            add(box(60, 200, 3, X(cx - dW / 2 - 45), cy + 40, T + 1 - hinge_z), "Display cover (membrane, LED)", "ACQ86599630", "doors", "C", "dark", sub)
            add(box(320, 430, 130, X(210), Hd - 260, -65 - hinge_z), "In-door ice maker housing (Slim SpacePlus)", "AEQ73110210", "doors", "P", "liner", sub)
            add(box(300, 190, 120, X(210), Hd - 470, -65 - hinge_z), "Ice bucket", "AKC73249303", "doors", "P", "clear", sub)
            add(cyl_v(20, 260, X(210), Hd - 360, -70 - hinge_z), "Auger", "EAU61083522", "doors", "C", "grey", sub)
            add(frame_bin(200, 120, 110, X(130), Hd - 560, -55 - hinge_z), "Dairy Corner bin", "MAN63049001", "doors", "P", "clear", sub)
            add(frame_bin(419, 184, 130, X(Wd / 2), 320, -65 - hinge_z), "Gallon door bin (L)", "MAN63048701", "doors", "P", "clear", sub)
            add(frame_bin(419, 120, 110, X(Wd / 2), 120, -55 - hinge_z), "Modular door bin (L)", "AAP73631702", "doors", "P", "clear", sub)
            add(box(24, Hd - 40, 56, X(Wd - 12), Hd / 2, -28 - hinge_z), "Centre mullion (flipper), heated", "AGU75188619", "doors", "C", "dark", sub)
            add(cyl_v(6, 120, X(Wd - 12), Hd - 140, -28 - hinge_z), "Mullion door spring", "MHY62044106", "doors", "C", "alu", sub)
            # dispenser internals
            add(box(dW + 16, dH + 16, 6, X(cx), cy, T - 1 - hinge_z), "Dispenser cover frame", "MCK62965301", "doors", "C", "dark", sub)
            add(box(dW - 10, 60, 4, X(cx), cy + dH / 2 - 40, T - 18 - hinge_z), "Dispenser front cover, upper", "MCK69570701", "doors", "C", "dark", sub)
            add(box(dW - 10, 60, 4, X(cx), cy - dH / 2 + 40, T - 18 - hinge_z), "Dispenser front cover, lower", "MCK71555401", "doors", "C", "dark", sub)
            add(box(70, 30, 14, X(cx), cy - dH * 0.28 + 22, T - 6 - hinge_z), "Dispenser lever holder", "MEG63262301", "doors", "C", "dark", sub)
            add(box(26, 14, 6, X(cx - 60), cy - dH * 0.28, T - 2 - hinge_z), "Lever button, water", "MBG64843402", "doors", "C", "grey", sub)
            add(box(26, 14, 6, X(cx + 60), cy - dH * 0.28, T - 2 - hinge_z), "Lever button, ice", "MBG64707201", "doors", "C", "grey", sub)
            add(box(dW * 0.55 + 8, 20, 4, X(cx), cy - dH * 0.28, T - 6 - hinge_z), "Dispenser lever cover", "MCK67046601", "doors", "C", "dark", sub)
            add(box(10, 10, 12, X(cx + dW * 0.3), cy - dH * 0.28, T - 14 - hinge_z), "Dispenser micro switch", "6600JB3001C", "doors", "C", "dark", sub)
            add(box(8, 8, 8, X(cx - dW * 0.3), cy - dH * 0.28, T - 14 - hinge_z), "Push button switch", "6600JR1002L", "doors", "C", "dark", sub)
            add(cq.Workplane("XZ").circle(16).workplane(offset=-40).circle(4).loft().translate(V(X(cx), cy + 40, T - 30 - hinge_z)), "Water funnel (nozzle)", "MDR62242301", "doors", "C", "grey", sub)
            add(box(dW - 20, 12, 60, X(cx), cy - dH / 2 + 8, T - 30 - hinge_z), "Dispenser drain tray", "AJP73574401", "doors", "C", "grey", sub)
            add(box(dW - 40, 8, 40, X(cx), cy - dH / 2 + 2, T - 26 - hinge_z), "Drain tray, lower", "MJS62812601", "doors", "C", "grey", sub)
            add(box(80, 90, 12, X(cx), cy + 90, T - 40 - hinge_z), "Ice dispenser duct door", "ABN73678303", "doors", "C", "dark", sub)
            add(cyl_x(16, 30, X(cx + 70), cy + 90, T - 48 - hinge_z), "Ice door motor (AC geared)", "EAU59551204", "doors", "C", "black", sub)
            add(box(40, 40, 10, X(cx + 70), cy + 90, T - 28 - hinge_z), "Ice door motor cover", "3550JA2273A", "doors", "C", "dark", sub)
            add(box(6, 60, 6, X(cx - 50), cy + 90, T - 44 - hinge_z), "Dispenser door link", "MFF62463201", "doors", "C", "alu", sub)
            add(cyl_v(4, 40, X(cx - 60), cy + 120, T - 44 - hinge_z), "Ice door lever spring", "4970JA3011K", "doors", "C", "alu", sub)
            add(box(50, 160, 3, X(cx - dW / 2 - 45), cy + 40, T - 10 - hinge_z), "Display PCB", "EBR78631903", "doors", "C", "pcb", sub)
            # ice maker sub-parts
            add(cyl_x(5, 40, X(210), Hd - 570, -134 - hinge_z), "Ice bank door hinge, lower", "AEH74156201", "doors", "C", "alu", sub)
            ibg = (
                box(310, 6, 4, X(210), Hd - 262, -136 - hinge_z).union(box(310, 6, 4, X(210), Hd - 458, -136 - hinge_z))
                .union(box(6, 200, 4, X(58), Hd - 360, -136 - hinge_z)).union(box(6, 200, 4, X(362), Hd - 360, -136 - hinge_z))
            )
            add(ibg, "Ice bin door gasket", "MDS64239202", "doors", "C", "gasket", sub)
            add(box(300, 200, 6, X(210), Hd - 360, -134 - hinge_z), "Ice bin door", "—", "doors", "P", "clear", sub)
            add(cyl_v(22, 60, X(210), Hd - 620, -70 - hinge_z), "Ice maker & auger motor assembly", "EAU60783850", "doors", "C", "black", sub)
            add(box(320, 6, 130, X(210), Hd - 46, -65 - hinge_z), "Ice room cover, top", "MCK67979601", "doors", "C", "liner", sub)
        else:
            dw, dh, dx, dy = Wd - 80, Hd * 0.62, Wd / 2, Hd * 0.5 + 40
            hb = (
                box(dw, 6, 150, X(dx), dy - dh / 2, -75 - hinge_z)
                .union(box(dw, 6, 150, X(dx), dy + dh / 2, -75 - hinge_z))
                .union(box(6, dh, 150, X(dx - dw / 2), dy, -75 - hinge_z))
                .union(box(6, dh, 150, X(dx + dw / 2), dy, -75 - hinge_z))
            )
            add(hb, "Door-in-Door 'Home Bar' case", "MBN63442501", "doors", "P", "liner", sub)
            add(box(dw - 20, dh - 20, 4, X(dx), dy, 14 - hinge_z), "ColdSaver panel", "—", "doors", "C", "foam", sub)
            add(frame_bin(dw - 30, 110, 120, X(dx), dy + dh / 2 - 150, -60 - hinge_z), "Cheese & butter bin (DiD)", "MAN63048801", "doors", "P", "clear", sub)
            add(frame_bin(dw - 30, 110, 120, X(dx), dy - 40, -60 - hinge_z), "Condiment bin (DiD)", "MAN63048901", "doors", "P", "clear", sub)
            add(frame_bin(419, 184, 130, X(Wd / 2), 120, -65 - hinge_z), "Gallon door bin (R)", "MAN63048701", "doors", "P", "clear", sub)
            add(frame_bin(dw - 30, 100, 110, X(dx), Hd - 170, -55 - hinge_z), "Fixed door bin, upper (R)", "AAP73631802", "doors", "P", "clear", sub)
            add(cyl_z(11, 6, X(Wd - 58), Hd / 2 + ln / 2 - 120, T + hp - hr + 12 - hinge_z), "Door-in-Door release button", "MEB62915403", "doors", "C", "dark", sub)
            add(box(dw, 8, 150, X(dx), dy + dh / 2 + 8, -75 - hinge_z), "Home Bar cover, upper", "MCK67480101", "doors", "C", "liner", sub)
            add(box(dw, 8, 150, X(dx), dy - dh / 2 - 8, -75 - hinge_z), "Home Bar cover, lower", "MCK67979701", "doors", "C", "liner", sub)
            add(cyl_v(6, 24, X(dx - dw / 2 - 6), dy + dh / 2 - 20, T / 2 - hinge_z), "Home Bar cap hinge (upper)", "—", "doors", "C", "alu", sub)
            add(box(120, 30, 1, X(Wd / 2), 70, T + 0.5 - hinge_z), "Name plate / emblem", "MFT62346511", "doors", "C", "alu", sub)
        return sub

    ang = 105 if open_state else 0
    ld, rd = door("L"), door("R")
    b.asm.add(ld, name="Left door assembly", loc=cq.Location(V(-W / 2, M["DOOR_Y0"], D + hinge_z), cq.Vector(0, 0, 1), -ang))
    b.asm.add(rd, name="Right door assembly", loc=cq.Location(V(W / 2, M["DOOR_Y0"], D + hinge_z), cq.Vector(0, 0, 1), ang))
    add(box(M["CENTER_GAP"] + 2, Hd, T, 0, M["DOOR_Y0"] + Hd / 2, D + T / 2), "Centre door seam", "—", "doors", "P", "gasket")
    add(box(W, M["GAP_H"], T, 0, kh + M["FZ_H"] + M["GAP_H"] / 2, D + T / 2), "Reveal, freezer/doors", "—", "doors", "P", "gasket")

    # ---- freezer drawer (sub-assembly, slides in +front) ----------------
    fz = cq.Assembly(name="freezer_drawer")
    fzy = kh + M["FZ_H"] / 2
    add(rounded_slab(W, M["FZ_H"], T - 12, 14, 0, fzy, D + 12 + (T - 12) / 2), "Freezer drawer front (foam, stainless)", "ADC73928108", "doors", "P", "steel", fz)
    add(box(W - 16, M["FZ_H"] - 16, 12, 0, fzy, D + 6), "Freezer drawer liner", "ADD73719008", "doors", "C", "liner", fz)
    ln = W * 0.6
    fbar = cyl_x(hr, ln, 0, kh + M["FZ_H"] - 70, D + T + hp - hr)
    for k in (-1, 1):
        fbar = fbar.union(cyl_z(9, hp - hr, k * (ln / 2 - 60), kh + M["FZ_H"] - 70, D + T + (hp - hr) / 2))
    add(fbar, "Freezer SmartPull bar handle + studs", "AED73593102", "doors", "C", "alu", fz)
    bw, bh, bd = W - 2 * ws - 60, 220, 520
    bz = D - 40 - bd / 2
    basket = frame_bin(bw, bh, bd, 0, ff + 20, bz).union(box(bw, bh, 4, 0, ff + 20 + bh / 2, bz + bd / 2 - 2)).union(box(4, bh - 20, bd - 20, 0, ff + 20 + bh / 2, bz))
    add(basket, "Durabase lower basket + divider", "AJP73594404", "freezer", "P", "clear", fz)
    for s in (-1, 1):
        add(cyl_x(22, 18, s * (W / 2 - ws - 60), ff + 22, D - 60), f"Drawer roller {'L' if s < 0 else 'R'}", "AHJ72909001", "freezer", "C", "grey", fz)
    b.asm.add(fz, name="Freezer drawer assembly", loc=cq.Location(V(0, 0, 430 if open_state else 0)))
    tw, th, td = W - 2 * ws - 120, 100, 420
    tz = D - 60 - td / 2 + (236 if open_state else 0)
    add(frame_bin(tw, th, td, 0, ff + 300, tz).union(box(tw, th, 4, 0, ff + 300 + th / 2, tz + td / 2 - 2)), "Upper pull-out tray", "AJP73574504", "freezer", "P", "clear")
    for s in (-1, 1):
        add(box(12, 30, 560, s * (W / 2 - ws - 8), ff + 290, D - 60 - 280), f"Drawer slide rail {'L' if s < 0 else 'R'}", "MGT61844004" if s < 0 else "MGT61844003", "freezer", "C", "alu")
        add(box(16, 40, 300, s * (W / 2 - ws - 10), ff + 120, D - 200), f"Rail guide {'L' if s < 0 else 'R'}", "AEC73637401", "freezer", "C", "grey")
    add(cyl_x(6, W - 2 * ws - 40, 0, ff + 60, D - 80), "Drawer sync bar", "ACJ73430105", "freezer", "C", "alu")
    add(box(fw - 40, fzh - 60, 30, 0, ff + fzh / 2, z0 + 50), "Freezer rear shroud / evaporator grille", "MHN62442001", "freezer", "C", "liner")

    # ---- fresh-food interior -------------------------------------------
    for i, x in enumerate((-380, 0, 380)):
        add(box(22, 800, 12, x, M["FF_Y0"] + 500, z0 + 8), f"Shelf ladder rail {i + 1}", "MEG63342502", "fresh", "C", "grey")
    shW, shD = 787 / 2, 406
    for y, row in ((M["FF_Y0"] + 590, "B"), (M["FF_Y0"] + 840, "A")):
        for s in (-1, 1):
            folding = row == "A" and s == 1
            depth = shD * 0.55 if folding else shD
            glass = box(shW - 8, 5, depth, s * (shW / 2 + 6), y + 8, z0 + 30 + depth / 2)
            frame = box(shW - 4, 14, 20, s * (shW / 2 + 6), y + 7, z0 + 40).union(box(shW - 4, 6, shD, s * (shW / 2 + 6), y + 3, z0 + 30 + shD / 2))
            add(glass, f"{'Folding' if folding else 'Fixed'} split shelf glass row {row} {'L' if s < 0 else 'R'}", "MHL62691504", "fresh", "P", "glass")
            add(frame, f"Shelf frame row {row} {'L' if s < 0 else 'R'} (cantilever)", "AHT73454104" if folding else "AHT73554101", "fresh", "C", "grey")
    gw, gh, gd, gy, gz = fw - 60, 120, 470, M["FF_Y0"] + 272, zc + 40
    add(drawer(gw, gh, gd, 0, gy, gz), "Glide N' Serve drawer", "AJP73574805", "fresh", "P", "clear")
    add(box(gw, 6, gd, 0, gy + gh + 30, gz), "Glide N' Serve glass cover", "ACQ85891502", "fresh", "P", "glass")
    for s in (-1, 1):
        add(box(10, 20, gd, s * (gw / 2 + 8), gy + 10, gz), f"Glide N' Serve rail {'L' if s < 0 else 'R'}", "AEC73597502", "fresh", "C", "alu")
    cw, chh, cd, cy0, cz = (fw - 60) / 2 - 10, 240, 500, M["FF_Y0"] + 10, zc + 30
    for s in (-1, 1):
        x = s * (cw / 2 + 10)
        add(drawer(cw, chh, cd, x, cy0, cz), f"Humidity crisper {'L' if s < 0 else 'R'}", "AJP73694502" if s < 0 else "AJP73694501", "fresh", "P", "clear")
    add(box(fw - 40, 10, cd + 20, 0, cy0 + chh + 8, cz), "Crisper cover frame", "ACQ85891603", "fresh", "C", "grey")
    add(box(fw - 60, 5, cd, 0, cy0 + chh + 14, cz), "Crisper cover glass", "ACQ85891603", "fresh", "P", "glass")
    add(cyl_z(38, 150, -fw / 2 + 90, M["FF_Y1"] - 70, z0 + fd - 160), "Water filter LT700P + head", "AGF80300702", "fresh", "C", "liner")
    add(box(220, 720, 34, 0, M["FF_Y0"] + 640, z0 + 20), "Multi-Air Flow duct + damper", "ADJ74132109", "fresh", "C", "liner")
    add(box(90, 90, 20, 0, M["FF_Y0"] + 930, z0 + 40), "Fresh air filter LT120F", "ADQ73214408", "fresh", "C", "grey")
    for s, side in ((-1, "L"), (1, "R")):
        add(box(6, 560, 14, s * (fw / 2 - 6), M["FF_Y0"] + 640, z0 + fd - 120), f"LED strip {side}", "EAV61873612", "fresh", "C", "led")
    tank = None
    for i in range(6):
        c = cyl_x(7, 360, 0, M["FF_Y0"] + 18 + i * 16, z0 + 80 + i * 18)
        tank = c if tank is None else tank.union(c)
    add(tank, "Water tank (coiled reservoir)", "AJL72911502", "fresh", "C", "clear")
    # filter, lamp covers, ducts, holders
    add(box(90, 70, 130, -fw / 2 + 90, M["FF_Y1"] - 50, z0 + fd - 160), "Filter cover", "MCK67447801", "fresh", "C", "liner")
    add(cyl_z(32, 30, -fw / 2 + 90, M["FF_Y1"] - 70, z0 + fd - 250), "Filter bypass cap", "ABN73019101", "fresh", "C", "grey")
    add(cyl_z(42, 30, -fw / 2 + 90, M["FF_Y1"] - 70, z0 + fd - 70), "Filter head (LT700P socket)", "ADQ36011715", "fresh", "C", "liner")
    for s, side, pn in ((-1, "L", "MCK66592001"), (1, "R", "MCK67153601")):
        add(box(6, 580, 30, s * (fw / 2 - 8), M["FF_Y0"] + 640, z0 + fd - 120), f"LED lamp cover {side}", pn, "fresh", "C", "clear")
    add(box(300, 4, 20, 60, M["FF_Y1"] - 4, z0 + fd - 150), "Ceiling LED module", "EAV61873612", "fresh", "C", "led")
    add(box(320, 6, 34, 60, M["FF_Y1"] - 8, z0 + fd - 150), "Ceiling lamp cover", "MCK68069401", "fresh", "C", "clear")
    add(box(240, 6, 30, 0, M["FF_Y0"] + 1000, z0 + 40), "Lamp cover, rear duct", "ACQ86133501", "fresh", "C", "clear")
    add(box(220, 40, 30, 0, M["FF_Y0"] + 280, z0 + 20), "Duct connector", "MCZ62872001", "fresh", "C", "liner")
    add(box(220, 700, 10, 0, M["FF_Y0"] + 640, z0 + 5), "Duct insulation", "MCZ63192901", "fresh", "C", "foam")
    for x, pn in ((-90, "MBL61865301"), (90, "MBL61865401")):
        add(cyl_z(14, 8, x, M["FF_Y1"] - 30, z0 + 42), "Duct cap", pn, "fresh", "C", "grey")
    add(box(24, 900, 16, -fw / 2 + 14, M["FF_Y0"] + 540, z0 + 30), "Tube cover (water line, left wall)", "MCK67502201", "fresh", "C", "grey")
    add(box(90, 90, 12, 0, M["FF_Y0"] + 930, z0 + 52), "Air cleaner filter element", "ADQ73214408", "fresh", "C", "foam")
    add(box(400, 6, 130, 0, M["FF_Y0"] + 112, z0 + 130), "Reservoir cover", "EBS61443328", "fresh", "C", "liner")
    for y, row in ((M["FF_Y0"] + 590, "B"), (M["FF_Y0"] + 840, "A")):
        for i, x in enumerate((-380, 0, 380)):
            add(box(26, 30, 16, x, y + 8, z0 + 18), f"Shelf holder row {row} rail {i + 1}", "MEG63060501" if i == 1 else "MEG64000201", "fresh", "C", "grey")
    for s in (-1, 1):
        sd = "L" if s < 0 else "R"
        add(box(14, 40, 40, s * (fw / 2 - 14), M["FF_Y0"] + 280, zc), f"Drawer rail holder {sd}", "MEG63342501", "fresh", "C", "grey")
        add(box(20, 20, 40, s * (fw / 2 - 30), M["FF_Y0"] + 272, zc + 260), f"Rail connector {sd}", "MCD62287601" if s < 0 else "MCD62287602", "fresh", "C", "grey")
        add(box(12, 24, 500, s * (fw / 2 - 8), M["FF_Y0"] + 250, zc + 30), f"Crisper slide rail {sd}", "MGT61844004" if s < 0 else "MGT61844003", "fresh", "C", "alu")
        add(box(16, 30, 300, s * (fw / 2 - 12), M["FF_Y0"] + 120, zc), f"Crisper rail guide {sd}", "AEC73637501" if s < 0 else "AEC73637502", "fresh", "C", "grey")
        add(box(16, 30, 360, s * (W / 2 - ws - 12), ff + 330, D - 260), f"Freezer drawer guide {sd}", "MEA61842101", "freezer", "C", "grey")
    add(box(160, 4, 14, 0, M["FZ_Y1"] - 4, D - 300), "Freezer LED", "EAV61873613", "freezer", "C", "led")
    add(box(180, 6, 24, 0, M["FZ_Y1"] - 10, D - 300), "Freezer lamp cover", "ACQ87128801", "freezer", "C", "clear")
    add(box(W - 2 * ws - 100, 8, 30, 0, ff + 8, D - 120), "Freezer tray, lower (discontinued)", "MJS62591801", "freezer", "C", "grey")

    # ---- refrigeration & controls ---------------------------------------
    comp = cyl_x(90, 300, 150, kh + 110, 140).union(box(340, 12, 220, 150, kh + 10, 140))
    add(comp, "Linear inverter compressor + base", "TCA38151706", "mech", "C", "black")
    cond = box(420, 200, 18, -180, kh + 130, 40)
    for i in range(9):
        cond = cond.union(cyl_v(2.5, 200, -180 - 160 + i * 40, kh + 130, 52))
    add(cond, "Wire condenser", "ACG73749402", "mech", "C", "black")
    add(cyl_z(62, 30, -180, kh + 130, 150).union(cyl_z(28, 40, -180, kh + 130, 185)), "Condenser fan motor", "4681JB1029D", "mech", "C", "grey")
    add(cyl_v(12, 90, -20, kh + 200, 60), "Drier / filter", "ADH73150210", "mech", "C", "copper")
    evap = box(560, 260, 40, 0, ff + 330, z0 + 22)
    for i in range(7):
        evap = evap.union(cyl_x(4, 540, 0, ff + 220 + i * 36, z0 + 22))
    add(evap, "Fin-tube evaporator", "ADL73762004", "mech", "C", "alu")
    add(box(560, 8, 8, 0, ff + 190, z0 + 22), "Sheath defrost heater", "5300JK1005Z", "mech", "C", "black")
    add(cyl_z(60, 26, 0, M["FZ_Y1"] - 60, z0 + 30), "Evaporator fan motor", "EAU63103208", "mech", "C", "grey")
    add(box(520, 20, 200, 0, ff + 150, z0 + 70), "Drip tray", "AJP73914401", "mech", "C", "grey")
    add(box(250, 180, 6, 180, H - 260, 4).union(box(270, 200, 22, 180, H - 260, -10)), "Main PCB in case", "EBR74796443", "mech", "C", "pcb")
    add(box(70, 60, 60, -300, kh + 70, 30), "Water inlet valve", "AJU72992601", "mech", "C", "black")
    add(cyl_x(5, 400, -200, kh + 40, 8), "Power cord", "EAD62108309", "mech", "C", "black")
    add(box(120, 90, 20, -300, kh + 200, 30), "Power control board", "EBR60070733", "mech", "C", "pcb")
    add(box(W - 80, 250, 4, 0, kh + 130, 2), "Machine room cover", "ACQ85930901", "mech", "C", "dark")
    for s, side in ((-1, "L"), (1, "R")):
        add(box(18, 26, 12, s * (W / 2 - ws - 20), M["FF_Y1"] - 30, D - 20), f"Door switch {side}", "EBF62234504", "mech", "C", "dark")
    # machine-room mounts, electrics, routing, sensors
    for i, (ax, bz_) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        add(cyl_v(14, 22, 150 + ax * 130, kh + 22, 140 + bz_ * 80), f"Compressor damper (rubber mount) {i + 1}", "MCQ67247501", "mech", "C", "gasket")
        add(box(20, 6, 20, 150 + ax * 130, kh + 36, 140 + bz_ * 80), f"Compressor mount clip {i + 1}", "4620JA3015A", "mech", "C", "alu")
    add(cyl_x(5, 90, 20, kh + 90, 140), "Sealing / process pipe", "MGE62010606", "mech", "C", "copper")
    add(cyl_v(20, 50, 300, kh + 140, 60), "Run capacitor", "EAE58905704", "mech", "C", "black")
    add(box(40, 30, 20, 320, kh + 110, 200), "Overload protector", "6750CL0001C", "mech", "C", "black")
    add(box(30, 20, 14, 320, kh + 140, 200), "PTC thermistor / start relay", "EBG61486613", "mech", "C", "black")
    add(box(36, 26, 18, 290, kh + 160, 230), "Compressor start device (PTC)", "EBG61486614", "mech", "C", "black")
    add(box(150, 150, 6, -180, kh + 130, 200), "Condenser fan grill", "AEB73764503", "mech", "C", "dark")
    add(box(150, 150, 6, 0, M["FZ_Y1"] - 60, z0 + 50), "Evaporator fan grill", "AEB73764506", "mech", "C", "dark")
    for s, pn in ((-1, "5040JQ2002B"), (1, "5040JQ2003A")):
        add(box(30, 40, 20, s * 60, M["FF_Y0"] + 300, z0 + 30), f"Damper motor support {'L' if s < 0 else 'R'}", pn, "mech", "C", "grey")
    add(box(60, 40, 30, 0, M["FF_Y0"] + 300, z0 + 40), "Air damper (stepper)", "—", "mech", "C", "grey")
    add(cyl_x(45, 20, -fw / 2 + 30, M["FF_Y1"] - 200, z0 + fd - 300), "Ice room fan + DC motor", "ADP73713301", "mech", "C", "grey")
    add(box(80, 60, 6, 180, H - 420, 6), "Sensor control board", "EBR71326804", "mech", "C", "pcb")
    add(box(300, 220, 30, 180, H - 260, -6), "PCB cover / case (outer)", "MCK67464101", "mech", "C", "dark")
    add(cyl_v(6, H - 400, -W / 2 + 40, H / 2, 8), "Main wire harness", "EAD62160110", "mech", "C", "black")
    add(box(40, 40, 40, -240, kh + 70, 30), "Secondary water valve", "5221JB2010G", "mech", "C", "black")
    add(cyl_v(4, 1500, -W / 2 + ws / 2 + 4, kh + 900, D - 30).union(cyl_x(4, 300, -W / 2 + 160, H - 20, D - 30)), "Water line tube (valve → tank → left door)", "AJR73964201", "mech", "C", "clear")
    add(box(20, 20, 20, -W / 2 + ws / 2 + 4, kh + 150, D - 30), "Tube connector", "MCD63827601", "mech", "C", "grey")
    add(cyl_v(6, 200, 0, ff + 60, z0 + 60), "Drain tube to machine room", "AJR74125001", "mech", "C", "grey")
    for x, y, z, nm in ((0, M["FF_Y0"] + 880, z0 + 40, "refrigerator"), (0, ff + 400, z0 + 60, "freezer"), (0, ff + 330, z0 + 48, "defrost"),
                        (-fw / 2 + 40, M["FF_Y1"] - 120, z0 + fd - 100, "humidity"), (W / 2 - 40, H - 80, D - 60, "ambient")):
        add(box(14, 14, 8, x, y, z), f"Temperature sensor, {nm}", "6500JB2002X", "mech", "C", "dark")

    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="doors at 105°, freezer drawer out")
    ap.add_argument("--no-mech", action="store_true", help="skip machine-room / control parts")
    ap.add_argument("--out", default="out")
    ap.add_argument("--formats", default="step,stl,glb")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    b = build(open_state=a.open, with_mech=not a.no_mech)
    base = os.path.join(a.out, f"LFXS27566S_{'open' if a.open else 'closed'}")
    fmts = [f.strip().lower() for f in a.formats.split(",")]
    if "step" in fmts:
        b.asm.save(base + ".step")
        print("wrote", base + ".step")
    if "stl" in fmts:
        b.asm.save(base + ".stl", exportType="STL")
        print("wrote", base + ".stl")
    if "glb" in fmts:
        b.asm.save(base + ".glb", exportType="GLTF")
        print("wrote", base + ".glb")
    print(f"{b.count} parts")


if __name__ == "__main__":
    main()

"""Procedural Blender model of the Case 05 viewer plant (run with the bpy module or Blender --background).

    python build.py [--out ../web/assets/hvac.glb] [--render preview.png]

Layout (metres, Blender Z up): office floor 18 m (x, west->east) x 12 m (y, south->north),
west perimeter zone x 0-4, interior 4-14, east perimeter 14-18; ceiling 2.8 m, slab above 3.8 m.
Plant deck north of the floor (y 12.6-17): AHU, air-cooled chiller, chilled water pump.
Part names follow <group>_<part>; moving parts have their origin on the pivot.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (loft, rect_ring, round_ring, box, cyl, empty, grid_image, linked, mat, mesh_from, poly_tube, reset,  # noqa: E402
                 smooth_tube, tube, uv_box_project)

reset()
# ----------------------------------------------------------------------------- materials
M = dict(
    galv=mat("galvanised", (0.72, 0.74, 0.76), 0.6, 0.42),
    flange=mat("flange", (0.62, 0.64, 0.66), 0.5, 0.5),
    panel=mat("ahu_panel", (0.80, 0.81, 0.79), 0.15, 0.45),
    alu=mat("aluminium", (0.66, 0.68, 0.70), 0.6, 0.4),
    dark=mat("dark_steel", (0.07, 0.08, 0.09), 0.5, 0.55),
    black=mat("black_plastic", (0.03, 0.03, 0.035), 0.0, 0.6),
    copper=mat("copper", (0.80, 0.45, 0.28), 1.0, 0.28),
    armaflex=mat("armaflex", (0.04, 0.04, 0.045), 0.0, 0.85),
    foil=mat("foil_insulation", (0.86, 0.86, 0.84), 0.6, 0.45),
    glass=mat("glass", (0.62, 0.76, 0.86), 0.0, 0.05, alpha=0.22),
    mullion=mat("mullion", (0.18, 0.19, 0.21), 0.6, 0.35),
    concrete=mat("concrete", (0.46, 0.46, 0.45), 0.0, 0.92),
    carpet=mat("carpet", (0.22, 0.24, 0.27), 0.0, 1.0),
    wall=mat("wall_paint", (0.86, 0.86, 0.84), 0.0, 0.9),
    wood=mat("desk_top", (0.62, 0.50, 0.38), 0.0, 0.55),
    white=mat("white_powder", (0.92, 0.92, 0.92), 0.1, 0.5),
    fanblade=mat("fan_blade", (0.12, 0.13, 0.14), 0.6, 0.4),
    impeller=mat("impeller", (0.30, 0.55, 0.72), 0.6, 0.35),
    motor=mat("motor_paint", (0.14, 0.32, 0.55), 0.3, 0.45),
    filter=mat("filter_media", (0.88, 0.85, 0.66), 0.0, 0.95),
    fins=mat("coil_fins", (0.78, 0.79, 0.80), 0.7, 0.3),
    pan=mat("stainless", (0.70, 0.71, 0.72), 1.0, 0.18),
    heater=mat("heater_element", (0.35, 0.22, 0.18), 0.6, 0.5, emit=(1.0, 0.35, 0.08), emit_strength=0.0),
    canvas=mat("flex_connector", (0.20, 0.20, 0.22), 0.0, 0.8),
    flex=mat("flex_duct", (0.80, 0.80, 0.78), 0.5, 0.55),
    person=mat("mannequin", (0.58, 0.62, 0.68), 0.0, 0.7),
    chair=mat("chair", (0.10, 0.10, 0.11), 0.0, 0.6),
    screen=mat("screen", (0.02, 0.02, 0.03), 0.3, 0.2),
    light=mat("light_panel", (0.95, 0.95, 0.92), 0.0, 0.4, emit=(1.0, 0.98, 0.92), emit_strength=2.0),
    chiller=mat("chiller_casing", (0.88, 0.89, 0.88), 0.2, 0.4),
    grating=mat("grating", (0.35, 0.36, 0.37), 0.8, 0.5),
    red=mat("tag_red", (0.75, 0.10, 0.08), 0.0, 0.5),
    blue=mat("tag_blue", (0.08, 0.28, 0.70), 0.0, 0.5),
    yellow=mat("tag_yellow", (0.95, 0.75, 0.10), 0.0, 0.5),
    green=mat("led_green", (0.1, 0.9, 0.3), 0.0, 0.3, emit=(0.1, 1.0, 0.3), emit_strength=3.0),
    rubber=mat("rubber", (0.05, 0.05, 0.05), 0.0, 0.9),
)
tile_img = grid_image("ceiling_tile")
M["ceiling"] = mat("ceiling_tile", (1, 1, 1), 0.0, 0.9, image=tile_img)

CEIL, SLAB2, DY = 2.8, 3.8, 3.3          # ceiling, slab above, duct centre height
ZX = {"Wes": (0.0, 4.0), "Int": (4.0, 14.0), "Eas": (14.0, 18.0)}
W, D = 18.0, 12.0

# ============================================================================= building
bld = empty("building")
box("building_slab", (W + 0.6, D + 0.6, 0.25), (W / 2, D / 2, -0.125), M["concrete"], bld)
for z, (x0, x1) in ZX.items():
    fl = box(f"building_floor_{z}", (x1 - x0, D, 0.02), ((x0 + x1) / 2, D / 2, 0.01), M["carpet"], bld)
# solid north (core side) and south walls
box("building_wall_north", (W, 0.2, SLAB2), (W / 2, D + 0.1, SLAB2 / 2), M["wall"], bld)
box("building_wall_south", (W, 0.2, SLAB2), (W / 2, -0.1, SLAB2 / 2), M["wall"], bld)
# curtain wall facades east and west: spandrel, glazing band 0.9-2.4 m, mullions every 1.5 m
for side, x in (("west", -0.05), ("east", W + 0.05)):
    box(f"building_spandrel_low_{side}", (0.1, D, 0.9), (x, D / 2, 0.45), M["mullion"], bld)
    box(f"building_spandrel_high_{side}", (0.1, D, SLAB2 - 2.4), (x, D / 2, (2.4 + SLAB2) / 2), M["mullion"], bld)
    box(f"building_glazing_{side}", (0.03, D, 1.5), (x, D / 2, 1.65), M["glass"], bld)
    mu = box(f"building_mullion_{side}_0", (0.12, 0.06, 1.5), (x, 0.0, 1.65), M["mullion"], bld)
    for k in range(1, 9):
        linked(mu, f"building_mullion_{side}_{k}", (x, 1.5 * k, 1.65), bld)
    box(f"building_transom_{side}", (0.12, D, 0.05), (x, D / 2, 2.4), M["mullion"], bld)
# glass partitions between perimeter and interior zones (to ceiling), with mullions
for name, x in (("west", 4.0), ("east", 14.0)):
    box(f"building_partition_{name}", (0.02, D, CEIL), (x, D / 2, CEIL / 2), M["glass"], bld)
    pm = box(f"building_partition_mullion_{name}_0", (0.05, 0.05, CEIL), (x, 0.6, CEIL / 2), M["mullion"], bld)
    for k in range(1, 9):
        linked(pm, f"building_partition_mullion_{name}_{k}", (x, 0.6 + 1.35 * k, CEIL / 2), bld)
# suspended ceiling (tiles 0.6 m) per zone, separate so it can be hidden
ceil = empty("ceiling")
for z, (x0, x1) in ZX.items():
    c = box(f"ceiling_tiles_{z}", (x1 - x0, D, 0.02), ((x0 + x1) / 2, D / 2, CEIL + 0.01), M["ceiling"], ceil)
    uv_box_project(c, 0.6)
# light troffers 0.6 x 1.2
lt = box("ceiling_light_0", (0.6, 1.2, 0.04), (2.0, 3.0, CEIL - 0.005), M["light"], ceil)
k = 1
for x in (2.0, 6.5, 9.0, 11.5, 16.0):
    for y in (3.0, 6.0, 9.0):
        if (x, y) != (2.0, 3.0):
            linked(lt, f"ceiling_light_{k}", (x, y, CEIL - 0.005), ceil)
            k += 1
# slab above (hidden by default in the viewer)
box("building_slab_above", (W + 0.6, D + 0.6, 0.25), (W / 2, D / 2, SLAB2 + 0.125), M["concrete"], bld)

# ============================================================================= furniture and people
furn = empty("furniture")
from lib import join, limb, sphere  # noqa: E402
M["skin"] = mat("skin", (0.80, 0.62, 0.50), 0.0, 0.55)
M["hair"] = mat("hair", (0.12, 0.08, 0.06), 0.0, 0.7)
M["trousers"] = mat("trousers", (0.13, 0.15, 0.20), 0.0, 0.8)
M["shoes"] = mat("shoes", (0.06, 0.05, 0.05), 0.2, 0.5)
SHIRTS = [mat("shirt_blue", (0.30, 0.45, 0.70), 0.0, 0.8), mat("shirt_white", (0.85, 0.86, 0.88), 0.0, 0.8),
          mat("shirt_red", (0.62, 0.22, 0.20), 0.0, 0.8)]
M["cushion"] = mat("chair_fabric", (0.16, 0.18, 0.22), 0.0, 0.9)
M["bezel"] = mat("monitor_bezel", (0.05, 0.05, 0.06), 0.3, 0.4)
M["display"] = mat("monitor_display", (0.10, 0.18, 0.28), 0.2, 0.15, emit=(0.35, 0.55, 0.8), emit_strength=0.6)
M["paper"] = mat("paper", (0.95, 0.95, 0.93), 0.0, 0.9)

# desk (origin at the desk centre on the floor; the user sits on the -y side, the monitor is on the +y side)
d = [
    box("dk_top", (1.4, 0.7, 0.025), (0, 0, 0.735), M["wood"], bevel=0.004),
    box("dk_side_l", (0.035, 0.66, 0.72), (-0.665, 0, 0.36), M["white"]),
    box("dk_side_r", (0.035, 0.66, 0.72), (0.665, 0, 0.36), M["white"]),
    box("dk_modesty", (1.28, 0.018, 0.38), (0, 0.29, 0.5), M["white"]),
    box("dk_cable_tray", (0.9, 0.12, 0.06), (0, 0.22, 0.66), M["dark"]),
    box("dk_screen_divider", (1.4, 0.03, 0.4), (0, 0.365, 0.95), M["cushion"], bevel=0.01),
    box("dk_mon_bezel", (0.58, 0.03, 0.35), (0, 0.18, 1.06), M["bezel"], bevel=0.006),
    box("dk_mon_display", (0.55, 0.004, 0.32), (0, 0.164, 1.065), M["display"]),
    box("dk_mon_back", (0.3, 0.04, 0.2), (0, 0.205, 1.05), M["bezel"], bevel=0.01),
    box("dk_mon_neck", (0.05, 0.03, 0.2), (0, 0.22, 0.85), M["alu"]),
    box("dk_mon_foot", (0.24, 0.17, 0.012), (0, 0.2, 0.754), M["alu"], bevel=0.004),
    box("dk_keyboard", (0.44, 0.14, 0.018), (0, -0.12, 0.757), M["bezel"], bevel=0.004),
    box("dk_mouse", (0.06, 0.1, 0.03), (0.32, -0.12, 0.762), M["bezel"], bevel=0.012),
    box("dk_papers", (0.21, 0.297, 0.01), (-0.48, -0.05, 0.752), M["paper"]),
    cyl("dk_mug", 0.04, 0.1, (0.55, 0.1, 0.8), M["white"], verts=14),
    box("dk_pedestal", (0.4, 0.55, 0.6), (0.42, 0.02, 0.3), M["white"], bevel=0.005),
]
desk = join("furn_desk_proto", d, origin=(0, 0, 0))
# task chair: cushion seat and back, armrests, gas column, 5-star base with castors
CY = -0.6
c = [
    box("ch_seat", (0.5, 0.48, 0.08), (0, CY, 0.47), M["cushion"], bevel=0.03),
    box("ch_back", (0.46, 0.06, 0.52), (0, CY - 0.27, 0.86), M["cushion"], bevel=0.03),
    box("ch_back_spine", (0.06, 0.03, 0.4), (0, CY - 0.3, 0.6), M["chair"]),
    box("ch_arm_l", (0.05, 0.26, 0.03), (-0.27, CY + 0.02, 0.68), M["chair"], bevel=0.01),
    box("ch_arm_r", (0.05, 0.26, 0.03), (0.27, CY + 0.02, 0.68), M["chair"], bevel=0.01),
    box("ch_armpost_l", (0.03, 0.03, 0.22), (-0.27, CY, 0.56), M["chair"]),
    box("ch_armpost_r", (0.03, 0.03, 0.22), (0.27, CY, 0.56), M["chair"]),
    box("ch_mech", (0.2, 0.2, 0.05), (0, CY, 0.41), M["chair"]),
    cyl("ch_column", 0.025, 0.3, (0, CY, 0.25), M["alu"], verts=12),
    cyl("ch_hub", 0.045, 0.05, (0, CY, 0.09), M["chair"], verts=12),
]
for k in range(5):
    a = 2 * math.pi * k / 5
    tip = Vector((0.3 * math.cos(a), CY + 0.3 * math.sin(a), 0.07))
    c.append(limb(f"ch_leg{k}", (0, CY, 0.09), tip, 0.022, 0.016, M["chair"], verts=6))
    c.append(sphere(f"ch_castor{k}", 0.028, (tip.x, tip.y, 0.03), M["black"], segs=8, rings=6))
chair = join("furn_chair_proto", c, origin=(0, 0, 0))


def mannequin(name, shirt):
    """Seated person facing +y, hands on the keyboard (origin on the floor under the desk centre)."""
    Y = -0.6
    p = []
    for s in (-1, 1):
        hip = Vector((0.1 * s, Y + 0.02, 0.56))
        knee = Vector((0.11 * s, Y + 0.44, 0.57))
        ankle = Vector((0.11 * s, Y + 0.48, 0.1))
        p += [limb(f"{name}_thigh{s}", hip, knee, 0.075, 0.06, M["trousers"]),
              sphere(f"{name}_knee{s}", 0.06, knee, M["trousers"]),
              limb(f"{name}_shin{s}", knee, ankle, 0.055, 0.042, M["trousers"]),
              box(f"{name}_shoe{s}", (0.1, 0.26, 0.08), (0.11 * s, Y + 0.55, 0.04), M["shoes"], bevel=0.03)]
        sh = Vector((0.19 * s, Y - 0.02, 1.0))
        el = Vector((0.23 * s, Y + 0.12, 0.8))
        wr = Vector((0.15 * s, Y + 0.44, 0.79))
        p += [sphere(f"{name}_shoulder{s}", 0.065, sh, shirt),
              limb(f"{name}_uarm{s}", sh, el, 0.05, 0.042, shirt),
              sphere(f"{name}_elbow{s}", 0.042, el, shirt),
              limb(f"{name}_farm{s}", el, wr, 0.04, 0.03, shirt),
              sphere(f"{name}_hand{s}", 0.04, wr + Vector((0, 0.04, -0.01)), M["skin"], scale=(0.8, 1.3, 0.5))]
    p += [sphere(f"{name}_pelvis", 0.17, (0, Y, 0.57), M["trousers"], scale=(1.0, 0.85, 0.55)),
          limb(f"{name}_torso", (0, Y - 0.01, 0.6), (0, Y - 0.03, 1.0), 0.15, 0.17, shirt, verts=16),
          sphere(f"{name}_chest", 0.17, (0, Y - 0.03, 0.97), shirt, scale=(1.15, 0.7, 0.5)),
          limb(f"{name}_neck", (0, Y - 0.02, 1.02), (0, Y - 0.01, 1.12), 0.045, 0.045, M["skin"]),
          sphere(f"{name}_head", 0.1, (0, Y + 0.01, 1.21), M["skin"], scale=(0.85, 1.0, 1.15), segs=16, rings=10),
          sphere(f"{name}_hair", 0.104, (0, Y - 0.005, 1.24), M["hair"], scale=(0.87, 1.0, 1.0), segs=16, rings=10)]
    return join(name, p, origin=(0, 0, 0))


persons = [mannequin(f"person_proto_{k}", s) for k, s in enumerate(SHIRTS)]
for proto in (desk, chair, *persons):
    proto.hide_render = True
    proto.location = (0, 0, -50)          # prototypes are parked below the floor and removed at export
people = {"Wes": [], "Int": [], "Eas": []}
layout = {
    "Wes": [(2.0, y, math.pi / 2) for y in (2.0, 4.0, 6.0, 8.0, 10.0)],
    "Eas": [(16.0, y, -math.pi / 2) for y in (2.0, 4.0, 6.0, 8.0, 10.0)],
    "Int": [(x, y, r) for x in (6.0, 8.0, 10.0, 12.0) for y, r in ((3.2, 0.0), (5.0, math.pi), (8.0, 0.0))],
}
for z, spots in layout.items():
    for i, (x, y, r) in enumerate(spots):
        linked(desk, f"furn_desk_{z}_{i}", (x, y, 0.02), furn, (0, 0, r))
        linked(chair, f"furn_chair_{z}_{i}", (x, y, 0.02), furn, (0, 0, r))
        linked(persons[(i + len(z)) % 3], f"person_{z}_{i}", (x, y, 0.02), furn, (0, 0, r))

# ============================================================================= rectangular duct helper
def rect_duct(name, p0, p1, w, h, parent, insulated=True, flange_every=1.2, hangers=True):
    """Straight rectangular duct between two points along x or y, with TDC flanges, hangers and insulation."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    ax = "x" if abs(d.x) > 1e-6 else ("y" if abs(d.y) > 1e-6 else "z")
    c = (p0 + p1) / 2
    size = {"x": (L, w, h), "y": (w, L, h), "z": (w, h, L)}[ax]
    g = empty(name, parent)
    box(f"{name}_sheet", size, c, M["galv"], g)
    n = max(1, int(L / flange_every))
    fsize = {"x": (0.04, w + 0.06, h + 0.06), "y": (w + 0.06, 0.04, h + 0.06), "z": (w + 0.06, h + 0.06, 0.04)}[ax]
    f0 = None
    for k in range(n + 1):
        p = p0 + d * (k / n)
        if f0 is None:
            f0 = box(f"{name}_flange_0", fsize, p, M["flange"], g)
        else:
            linked(f0, f"{name}_flange_{k}", p, g)
    if insulated:
        isize = {"x": (L, w + 0.06, h + 0.06), "y": (w + 0.06, L, h + 0.06), "z": (w + 0.06, h + 0.06, L)}[ax]
        box(f"{name}_insulation", isize, c, M["foil"], g)
    if hangers and ax != "z":
        nh = max(2, int(L / 1.8) + 1)
        for k in range(nh):
            p = p0 + d * ((k + 0.5) / nh)
            off = Vector((0, w / 2 + 0.08, 0)) if ax == "x" else Vector((w / 2 + 0.08, 0, 0))
            for s, sgn in (("a", 1), ("b", -1)):
                q = p + off * sgn
                cyl(f"{name}_rod_{k}{s}", 0.006, SLAB2 - (p.z - h / 2 - 0.05), (q.x, q.y, (SLAB2 + p.z - h / 2 - 0.05) / 2), M["alu"], g, verts=6)
            strut = (w + 0.3, 0.04, 0.04) if ax == "y" else (0.04, w + 0.3, 0.04)
            strut = (0.04, w + 0.3, 0.04) if ax == "x" else (w + 0.3, 0.04, 0.04)
            box(f"{name}_strut_{k}", strut, (p.x, p.y, p.z - h / 2 - 0.05), M["alu"], g)
    return g


def elbow_block(name, p, w, h, parent):
    g = empty(name, parent)
    box(f"{name}_sheet", (w, w, h), p, M["galv"], g)
    box(f"{name}_insulation", (w + 0.06, w + 0.06, h + 0.06), p, M["foil"], g)
    return g


def diffuser(name, x, y, parent, size=0.6):
    """Square 4-way ceiling diffuser: face frame, stepped cones, plenum box and round collar."""
    g = empty(name, parent, (x, y, CEIL))
    box(f"{name}_frame", (size, size, 0.02), (x, y, CEIL - 0.01), M["white"], g)
    for k, s in enumerate((0.48, 0.38, 0.28, 0.18)):
        tube_sq = box(f"{name}_cone_{k}", (s, s, 0.015), (x, y, CEIL - 0.02 - 0.012 * k), M["white"], g)
    box(f"{name}_core", (0.12, 0.12, 0.02), (x, y, CEIL - 0.07), M["white"], g)
    box(f"{name}_plenum", (0.5, 0.5, 0.3), (x, y, CEIL + 0.17), M["galv"], g)
    cyl(f"{name}_collar", 0.10, 0.1, (x, y, CEIL + 0.37), M["galv"], g, verts=16)
    return g


def return_grille(name, x, y, parent):
    g = empty(name, parent, (x, y, CEIL))
    box(f"{name}_frame", (0.6, 0.6, 0.02), (x, y, CEIL - 0.01), M["white"], g)
    bar = box(f"{name}_bar_x0", (0.56, 0.008, 0.02), (x, y - 0.26, CEIL - 0.02), M["white"], g)
    for k in range(1, 14):
        linked(bar, f"{name}_bar_x{k}", (x, y - 0.26 + 0.04 * k, CEIL - 0.02), g)
    barz = box(f"{name}_bar_y0", (0.008, 0.56, 0.02), (x - 0.26, y, CEIL - 0.02), M["white"], g)
    for k in range(1, 14):
        linked(barz, f"{name}_bar_y{k}", (x - 0.26 + 0.04 * k, y, CEIL - 0.02), g)
    return g


# ============================================================================= VAV boxes
def vav_box(z, inlet, direction, parent):
    """Pressure-independent VAV box with electric reheat; air flows along +x (direction=1) or -x/+y etc.
    inlet: world point of the inlet collar face; direction: unit vector (x or y)."""
    g = empty(f"vav_{z}", parent, inlet)
    d = Vector(direction)
    ax = "X" if abs(d.x) > 0 else "Y"
    side = Vector((0, 1, 0)) if ax == "X" else Vector((1, 0, 0))
    p = Vector(inlet)
    L_in, L_box, L_reh = 0.25, 0.55, 0.35
    # inlet collar (round 250 mm) with flow cross
    c_in = p + d * (L_in / 2)
    cyl(f"vav_{z}_inlet", 0.125, L_in, c_in, M["galv"], g, axis=ax, verts=20)
    bar1 = box(f"vav_{z}_flowcross_a", (0.01, 0.24, 0.012) if ax == "X" else (0.24, 0.01, 0.012), c_in + d * 0.05, M["dark"], g)
    box(f"vav_{z}_flowcross_b", (0.01, 0.012, 0.24) if ax == "X" else (0.012, 0.01, 0.24), c_in + d * 0.05, M["dark"], g)
    # damper blade (butterfly) with pivot on the shaft (horizontal, perpendicular to flow)
    blade_c = p + d * (L_in * 0.62)
    if ax == "X":
        cyl(f"vav_{z}_damper_blade", 0.118, 0.006, blade_c, M["dark"], g, axis="X", verts=20, origin=blade_c)
    else:
        cyl(f"vav_{z}_damper_blade", 0.118, 0.006, blade_c, M["dark"], g, axis="Y", verts=20, origin=blade_c)
    shaft_len = 0.42
    cyl(f"vav_{z}_shaft", 0.008, shaft_len, blade_c + side * 0.05, M["alu"], g, axis="Y" if ax == "X" else "X", verts=8)
    # casing (insulated sheet-metal box)
    c_box = p + d * (L_in + L_box / 2)
    size = (L_box, 0.55, 0.32) if ax == "X" else (0.55, L_box, 0.32)
    box(f"vav_{z}_casing", size, c_box, M["galv"], g, bevel=0.005)
    # actuator + controller on the side
    act = blade_c + side * 0.25
    box(f"vav_{z}_actuator", (0.12, 0.09, 0.1) if ax == "X" else (0.09, 0.12, 0.1), act, M["black"], g, bevel=0.01)
    box(f"vav_{z}_controller", (0.22, 0.05, 0.16) if ax == "X" else (0.05, 0.22, 0.16), c_box + side * 0.31, M["white"], g, bevel=0.005)
    box(f"vav_{z}_led", (0.02, 0.005, 0.01) if ax == "X" else (0.005, 0.02, 0.01), c_box + side * 0.336 + Vector((0, 0, 0.05)), M["green"], g)
    poly_tube(f"vav_{z}_sensor_tube", [tuple(c_in + side * 0.12), tuple(c_in + side * 0.2 + Vector((0, 0, 0.12))), tuple(c_box + side * 0.3 + Vector((0, 0, 0.1)))], 0.004, M["yellow"], g)
    # backdraft damper (gravity flap) at the casing outlet
    c_bdd = p + d * (L_in + L_box - 0.03)
    piv = c_bdd + Vector((0, 0, 0.14))
    box(f"vav_{z}_backdraft_flap", (0.006, 0.5, 0.28) if ax == "X" else (0.5, 0.006, 0.28), c_bdd, M["alu"], g, origin=piv)
    # electric reheat section: frame, three serpentine elements, terminal box
    c_reh = p + d * (L_in + L_box + L_reh / 2)
    size_r = (L_reh, 0.55, 0.32) if ax == "X" else (0.55, L_reh, 0.32)
    box(f"vav_{z}_reheat_casing", size_r, c_reh, M["galv"], g, bevel=0.005)
    for k, off in enumerate((-0.18, 0.0, 0.18)):
        pts = []
        for j in range(9):
            zz = -0.11 + 0.0275 * j
            a = -0.2 if j % 2 == 0 else 0.2
            q = c_reh + side * off + d * 0.0 + Vector((0, 0, zz))
            pts.append(tuple(q + (side * 0 + Vector((0, 0, 0)))))
        # zig-zag across the duct width
        pts = [tuple(c_reh + d * (0.04 * ((j % 2) * 2 - 1)) + side * off + Vector((0, 0, -0.11 + 0.0275 * j))) for j in range(9)]
        poly_tube(f"vav_{z}_heater_element_{k}", pts, 0.006, M["heater"], g, verts=8)
    box(f"vav_{z}_heater_box", (0.2, 0.08, 0.2) if ax == "X" else (0.08, 0.2, 0.2), c_reh + side * 0.32, M["white"], g, bevel=0.005)
    box(f"vav_{z}_heater_label", (0.08, 0.003, 0.04) if ax == "X" else (0.003, 0.08, 0.04), c_reh + side * 0.362, M["red"], g)
    # standing seams, bottom access panel, nameplate, hanger rods with angle brackets
    for k, t in enumerate((L_in + 0.01, L_in + L_box - 0.01, L_in + L_box + L_reh - 0.01)):
        q = p + d * t
        box(f"vav_{z}_seam_{k}", (0.02, 0.58, 0.35) if ax == "X" else (0.58, 0.02, 0.35), q, M["flange"], g)
    box(f"vav_{z}_access_panel", (0.3, 0.3, 0.012) if ax == "X" else (0.3, 0.3, 0.012), c_box - Vector((0, 0, 0.166)), M["panel"], g)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = c_box - Vector((0, 0, 0.173)) + (d * 0.12 * sx) + side * 0.12 * sy
            cyl(f"vav_{z}_screw_{sx}{sy}", 0.008, 0.004, q, M["alu"], g, verts=8)
    box(f"vav_{z}_nameplate", (0.14, 0.003, 0.07) if ax == "X" else (0.003, 0.14, 0.07), c_box - side * 0.277 + Vector((0, 0, 0.05)), M["blue"], g)
    for k, t in enumerate((L_in + 0.08, L_in + L_box + L_reh - 0.08)):
        q = p + d * t
        for sgn in (1, -1):
            r = q + side * (0.3 * sgn)
            cyl(f"vav_{z}_rod_{k}{'ab'[sgn > 0]}", 0.006, SLAB2 - (DY - 0.2), (r.x, r.y, (SLAB2 + DY - 0.2) / 2), M["alu"], g, verts=6)
        box(f"vav_{z}_bracket_{k}", (0.04, 0.68, 0.04) if ax == "X" else (0.68, 0.04, 0.04), q - Vector((0, 0, 0.19)), M["alu"], g)
    # outlet flange
    out = p + d * (L_in + L_box + L_reh)
    box(f"vav_{z}_outlet_flange", (0.03, 0.6, 0.37) if ax == "X" else (0.6, 0.03, 0.37), out, M["flange"], g)
    return g, out


# ============================================================================= ductwork in the ceiling plenum
duc = empty("ducts")
MAIN_X = 8.3
# supply main: from the north wall to the tee at y = 6.0 (500 x 300)
rect_duct("duct_supply_main", (MAIN_X, 12.0, DY), (MAIN_X, 6.25, DY), 0.5, 0.3, duc)
elbow_block("duct_supply_tee", (MAIN_X, 6.0, DY), 0.5, 0.3, duc)
# branches east and west (300 x 250) to the VAV inlets
rect_duct("duct_supply_east", (MAIN_X + 0.25, 6.0, DY), (13.0, 6.0, DY), 0.3, 0.25, duc)
rect_duct("duct_supply_west", (MAIN_X - 0.25, 6.0, DY), (4.9, 6.0, DY), 0.3, 0.25, duc)
vav = empty("vav")
vE, oE = vav_box("Eas", (14.15, 6.0, DY), (1, 0, 0), vav)
loft("duct_reducer_Eas", rect_ring((13.0, 6.0, DY), 0.3, 0.25, "X", 24), round_ring((13.45, 6.0, DY), 0.125, "X", 24), M["galv"], vav)
cyl("duct_round_Eas", 0.125, 0.7, (13.8, 6.0, DY), M["galv"], vav, axis="X", verts=24)
tube("duct_round_Eas_band", 0.133, 0.12, 0.03, (13.45, 6.0, DY), M["flange"], vav, axis="X")
vW, oW = vav_box("Wes", (3.85, 6.0, DY), (-1, 0, 0), vav)
loft("duct_reducer_Wes", rect_ring((4.9, 6.0, DY), 0.3, 0.25, "X", 24), round_ring((4.5, 6.0, DY), 0.125, "X", 24), M["galv"], vav)
cyl("duct_round_Wes", 0.125, 0.65, (4.175, 6.0, DY), M["galv"], vav, axis="X", verts=24)
tube("duct_round_Wes_band", 0.133, 0.12, 0.03, (4.5, 6.0, DY), M["flange"], vav, axis="X")
rect_duct("duct_supply_interior", (MAIN_X, 5.75, DY), (MAIN_X, 4.75, DY), 0.3, 0.25, duc)
loft("duct_reducer_Int", rect_ring((MAIN_X, 4.75, DY), 0.3, 0.25, "Y", 24), round_ring((MAIN_X, 4.4, DY), 0.125, "Y", 24), M["galv"], vav)
cyl("duct_round_Int", 0.125, 0.2, (MAIN_X, 4.3, DY), M["galv"], vav, axis="Y", verts=24)
vI, oI = vav_box("Int", (MAIN_X, 4.2, DY), (0, -1, 0), vav)
# diffusers and round ducts / flex from the VAV outlets
dif = empty("diffusers")
DIFF = {"Eas": [(16.2, 3.0), (16.2, 9.0)], "Wes": [(1.8, 3.0), (1.8, 9.0)],
        "Int": [(6.0, 3.0), (10.6, 3.0), (6.0, 9.0), (10.6, 9.0)]}
outs = {"Eas": oE, "Wes": oW, "Int": oI}
for z, pts in DIFF.items():
    o = outs[z]
    box(f"duct_plenum_{z}", (0.4, 0.6, 0.35) if z != "Int" else (0.6, 0.4, 0.35), o + (Vector((0.2, 0, 0)) if z == "Eas" else Vector((-0.2, 0, 0)) if z == "Wes" else Vector((0, -0.2, 0))), M["galv"], duc)
    for i, (x, y) in enumerate(pts):
        diffuser(f"diffuser_{z}_{i}", x, y, dif)
        start = o + (Vector((0.4, 0, 0)) if z == "Eas" else Vector((-0.4, 0, 0)) if z == "Wes" else Vector((0, -0.4, 0)))
        start.z = DY
        mid = Vector((x, start.y, DY)) if z != "Int" else Vector((start.x, y, DY))
        path = [tuple(start), tuple((start + mid) / 2), tuple(mid), (x, y, DY), (x, y, CEIL + 0.42)]
        if z == "Int":
            path = [tuple(start), (start.x, start.y - 0.3, DY), (x, start.y - 0.3, DY), (x, y, DY), (x, y, CEIL + 0.42)]
        smooth_tube(f"flexduct_{z}_{i}", path, 0.1, M["flex"], duc, verts=12, bend=0.35)
# return: grilles in the ceiling (plenum return) and a return duct from the plenum to the AHU
GRILLE = {"Eas": [(16.2, 6.0)], "Wes": [(1.8, 6.0)], "Int": [(6.0, 6.0), (10.6, 6.0)]}
for z, pts in GRILLE.items():
    for i, (x, y) in enumerate(pts):
        return_grille(f"return_grille_{z}_{i}", x, y, dif)
RET_X = 5.4
box("duct_return_inlet", (0.6, 0.5, 0.45), (RET_X, 11.3, DY), M["galv"], duc)
rect_duct("duct_return_main", (RET_X, 11.55, DY), (RET_X, 13.6, DY), 0.45, 0.35, duc, insulated=False)

# ============================================================================= plant deck
plant = empty("plant")
box("plant_deck", (12.0, 4.6, 0.12), (9.0, 15.0, -0.06), M["grating"], plant)
box("plant_parapet", (12.0, 0.15, 1.1), (9.0, 17.3, 0.55), M["concrete"], plant)

# ----------------------------------------------------------------------------- AHU (along +x, blow-through)
AY, AZ0 = 14.6, 0.20         # centre line y, top of base frame
AW, AH = 1.10, 1.15          # casing width (y) and height (z)
ZC = AZ0 + AH / 2
sec = {"mix": (4.40, 5.40), "filter": (5.40, 5.90), "fan": (5.90, 7.20), "coil": (7.20, 7.85), "dis": (7.85, 8.75)}
ahu = empty("ahu")
# base frame
for s, yy in (("s", AY - AW / 2 + 0.05), ("n", AY + AW / 2 - 0.05)):
    box(f"ahu_base_rail_{s}", (4.45, 0.1, 0.16), (6.575, yy, 0.08), M["dark"], ahu)
for k, x in enumerate((4.45, 5.65, 7.2, 8.7)):
    box(f"ahu_base_cross_{k}", (0.08, AW, 0.12), (x, AY, 0.08), M["dark"], ahu)
# section casings: frame profiles + side panels (south panels are removable doors)
for nm, (x0, x1) in sec.items():
    g = empty(f"ahu_{nm}", ahu)
    L = x1 - x0
    cx = (x0 + x1) / 2
    box(f"ahu_{nm}_roof", (L, AW, 0.05), (cx, AY, AZ0 + AH - 0.025), M["panel"], g)
    box(f"ahu_{nm}_floor", (L, AW, 0.05), (cx, AY, AZ0 + 0.025), M["panel"], g)
    box(f"ahu_{nm}_back", (L, 0.05, AH), (cx, AY + AW / 2 - 0.025, ZC), M["panel"], g)
    # south access door, hinged at its west edge
    door = box(f"ahu_{nm}_door", (L - 0.04, 0.05, AH - 0.1), (cx, AY - AW / 2 + 0.025, ZC), M["panel"], g,
               origin=(x0 + 0.02, AY - AW / 2 + 0.025, ZC))
    for hz in (ZC - 0.35, ZC + 0.35):
        cyl(f"ahu_{nm}_hinge_{int(hz * 100)}", 0.012, 0.08, (x0 + 0.02, AY - AW / 2 - 0.005, hz), M["alu"], g, verts=8)
    box(f"ahu_{nm}_handle", (0.03, 0.04, 0.18), (x1 - 0.1, AY - AW / 2 - 0.02, ZC), M["black"], g)
    for zz in (AZ0, AZ0 + AH):
        for yy in (AY - AW / 2, AY + AW / 2):
            box(f"ahu_{nm}_profile_{int(zz*100)}_{int(yy*100)}", (L, 0.04, 0.04), (cx, yy, zz), M["alu"], g)
    for xx in (x0, x1):
        for yy in (AY - AW / 2, AY + AW / 2):
            box(f"ahu_{nm}_post_{int(xx*100)}_{int(yy*100)}", (0.04, 0.04, AH), (xx, yy, ZC), M["alu"], g)
# end panels
box("ahu_dis_end", (0.05, AW, AH), (sec["dis"][1] - 0.025, AY, ZC), M["panel"], ahu)
# --- mixing box: outdoor air hood + damper (west end), return damper (top), relief damper + hood (north side)
gm = bpy.data.objects["ahu_mix"]
x0 = sec["mix"][0]
box("ahu_mix_oa_hood_top", (0.45, AW + 0.1, 0.03), (x0 - 0.22, AY, AZ0 + AH + 0.02), M["panel"], gm)
for s, yy in (("s", AY - AW / 2 - 0.03), ("n", AY + AW / 2 + 0.03)):
    mesh_from(f"ahu_mix_oa_hood_cheek_{s}", [(x0, yy, AZ0 + AH + 0.03), (x0 - 0.45, yy, AZ0 + AH + 0.03), (x0, yy, AZ0 + 0.2)],
              [(0, 1, 2)], M["panel"], gm)
bl = box("ahu_mix_oa_louvre_0", (0.03, AW, 0.06), (x0 - 0.22, AY, AZ0 + 0.35), M["alu"], gm)
bl.rotation_euler = (0, 0.6, 0)
for k in range(1, 9):
    o = linked(bl, f"ahu_mix_oa_louvre_{k}", (x0 - 0.22 + 0.0 * k, AY, AZ0 + 0.35 + 0.09 * k), gm, (0, 0.6, 0))
box("ahu_mix_oa_birdmesh", (0.005, AW - 0.05, AH - 0.2), (x0 - 0.02, AY, ZC + 0.05), M["dark"], gm)


def damper(prefix, centre, span, n, axis_dir, normal, parent, blade_w=None):
    """Opposed-blade damper: frame + n blades; each blade origin on its shaft."""
    c = Vector(centre)
    nrm = Vector(normal)
    along = Vector(axis_dir)                    # shaft direction
    stack = nrm.cross(along).normalized()       # direction in which blades are stacked
    pitch = span / n
    fr_size = tuple(abs(along[i]) * span + abs(stack[i]) * span + abs(nrm[i]) * 0.06 for i in range(3))
    box(f"{prefix}_frame", fr_size, c, M["alu"], parent)
    for k in range(n):
        bc = c + stack * (-span / 2 + pitch * (k + 0.5))
        size = tuple(abs(along[i]) * (span - 0.04) + abs(stack[i]) * (pitch * 0.95) + abs(nrm[i]) * 0.008 for i in range(3))
        box(f"{prefix}_blade_{k}", size, bc, M["alu"], parent, origin=bc)
    act_pos = c + along * (span / 2 + 0.08)
    box(f"{prefix}_actuator", (0.1, 0.1, 0.12), act_pos, M["black"], parent, bevel=0.01)


damper("ahu_damper_oa", (x0 + 0.04, AY, ZC + 0.05), 0.9, 6, (0, 1, 0), (1, 0, 0), gm)
damper("ahu_damper_ret", ((sec["mix"][0] + sec["mix"][1]) / 2 + 0.15, AY, AZ0 + AH + 0.03), 0.6, 4, (0, 1, 0), (0, 0, 1), gm)
damper("ahu_damper_rel", ((sec["mix"][0] + sec["mix"][1]) / 2, AY + AW / 2 + 0.03, ZC), 0.7, 5, (1, 0, 0), (0, 1, 0), gm)
box("ahu_mix_relief_hood", (0.8, 0.35, 0.05), ((sec["mix"][0] + sec["mix"][1]) / 2, AY + AW / 2 + 0.18, ZC + 0.42), M["panel"], gm)
# --- filter bank: 2 x 2 pleated panels
gf = bpy.data.objects["ahu_filter"]
fx = (sec["filter"][0] + sec["filter"][1]) / 2
verts, faces = [], []
npl = 24
for iy, y0 in enumerate((-0.5, 0.0)):
    for iz, z0 in enumerate((-0.5, 0.0)):
        base_i = len(verts)
        for j in range(npl + 1):
            xx = fx + (0.06 if j % 2 else -0.06)
            yy = AY + y0 + 0.02 + 0.46 * j / npl
            verts += [(xx, yy, ZC + z0 + 0.02), (xx, yy, ZC + z0 + 0.48)]
        for j in range(npl):
            a = base_i + 2 * j
            faces.append((a, a + 2, a + 3, a + 1))
mesh_from("ahu_filter_media", verts, faces, M["filter"], gf)
for yy in (AY - 0.5, AY, AY + 0.5):
    box(f"ahu_filter_frame_v{int(yy*100)}", (0.15, 0.03, 1.0), (fx, yy, ZC), M["alu"], gf)
for zz in (ZC - 0.5, ZC, ZC + 0.5):
    box(f"ahu_filter_frame_h{int(zz*100)}", (0.15, 1.0, 0.03), (fx, AY, zz), M["alu"], gf)
box("ahu_filter_dp_gauge", (0.03, 0.1, 0.1), (fx, AY - AW / 2 - 0.05, ZC + 0.35), M["white"], gf)
# --- plug fan: inlet cone, impeller (pivot on axis), motor, frame, isolators
gfan = bpy.data.objects["ahu_fan"]
fx0 = sec["fan"][0]
FX = fx0 + 0.55
tube("ahu_fan_inlet_cone", 0.36, 0.30, 0.12, (fx0 + 0.18, AY, ZC), M["galv"], gfan, axis="X")
box("ahu_fan_inlet_panel", (0.03, AW - 0.1, AH - 0.1), (fx0 + 0.12, AY, ZC), M["galv"], gfan)
imp = empty("ahu_fan_impeller", gfan, (FX, AY, ZC))
cyl("ahu_fan_impeller_backplate", 0.40, 0.012, (FX + 0.12, AY, ZC), M["impeller"], imp, axis="X", verts=32, origin=(FX, AY, ZC))
tube("ahu_fan_impeller_shroud", 0.40, 0.30, 0.03, (FX - 0.12, AY, ZC), M["impeller"], imp, axis="X", verts=32)
bp = None
for k in range(9):
    a = 2 * math.pi * k / 9
    # backward-curved blade as a thin curved strip between r=0.18 and r=0.40
    vs, fs = [], []
    for j in range(5):
        r = 0.18 + 0.055 * j
        th = a + 0.45 * (j / 4)
        for xx in (FX - 0.11, FX + 0.11):
            vs.append((xx, AY + r * math.cos(th), ZC + r * math.sin(th)))
    for j in range(4):
        fs.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
    b = mesh_from(f"ahu_fan_impeller_blade_{k}", [(v[0] - FX, v[1] - AY, v[2] - ZC) for v in vs], fs, M["impeller"], imp, loc=(FX, AY, ZC))
cyl("ahu_fan_hub", 0.07, 0.2, (FX, AY, ZC), M["dark"], imp, axis="X", verts=16, origin=(FX, AY, ZC))
cyl("ahu_fan_motor", 0.15, 0.42, (FX + 0.42, AY, ZC), M["motor"], gfan, axis="X", verts=24)
cyl("ahu_fan_shaft", 0.022, 0.42, (FX + 0.1, AY, ZC), M["pan"], gfan, axis="X", verts=12)
cyl("ahu_fan_motor_flange", 0.19, 0.03, (FX + 0.2, AY, ZC), M["motor"], gfan, axis="X", verts=24)
cyl("ahu_fan_bearing_housing", 0.06, 0.06, (FX + 0.16, AY, ZC), M["dark"], gfan, axis="X", verts=16)
cyl("ahu_fan_motor_endcover", 0.15, 0.08, (FX + 0.67, AY, ZC), M["dark"], gfan, axis="X", verts=24, r2=0.13)
cyl("ahu_fan_motor_eyebolt", 0.012, 0.06, (FX + 0.42, AY, ZC + 0.18), M["alu"], gfan, verts=8)
tube("ahu_fan_inlet_ring", 0.33, 0.29, 0.04, (fx0 + 0.25, AY, ZC), M["impeller"], gfan, axis="X", verts=32)
for k in range(10):
    a = 2 * math.pi * k / 10
    box(f"ahu_fan_motor_fin_{k}", (0.36, 0.012, 0.03), (FX + 0.42, AY + 0.155 * math.cos(a), ZC + 0.155 * math.sin(a)), M["motor"], gfan)
box("ahu_fan_terminal_box", (0.12, 0.1, 0.1), (FX + 0.42, AY, ZC + 0.2), M["motor"], gfan)
box("ahu_fan_motor_frame", (0.5, 0.5, 0.06), (FX + 0.42, AY, AZ0 + 0.2), M["dark"], gfan)
for s, yy in (("a", AY - 0.2), ("b", AY + 0.2)):
    box(f"ahu_fan_motor_leg_{s}", (0.06, 0.06, ZC - 0.15 - AZ0 - 0.2), (FX + 0.42, yy, (ZC - 0.15 + AZ0 + 0.2) / 2), M["dark"], gfan)
for k, (xx, yy) in enumerate(((fx0 + 0.25, AY - 0.4), (fx0 + 0.25, AY + 0.4), (sec["fan"][1] - 0.15, AY - 0.4), (sec["fan"][1] - 0.15, AY + 0.4))):
    cyl(f"ahu_fan_isolator_{k}", 0.04, 0.1, (xx, yy, AZ0 + 0.1), M["yellow"], gfan, verts=10)
box("ahu_fan_pedestal", (0.5, 0.4, ZC - 0.4 - AZ0 - 0.2), (FX + 0.25, AY, (ZC - 0.4 + AZ0 + 0.2) / 2), M["dark"], gfan)
box("ahu_fan_skid", (1.1, 0.95, 0.05), ((fx0 + sec["fan"][1]) / 2, AY, AZ0 + 0.17), M["dark"], gfan)
box("ahu_fan_vfd", (0.25, 0.15, 0.4), (sec["fan"][1] - 0.2, AY - AW / 2 - 0.1, ZC + 0.25), M["white"], gfan, bevel=0.01)
box("ahu_fan_vfd_display", (0.08, 0.005, 0.05), (sec["fan"][1] - 0.2, AY - AW / 2 - 0.18, ZC + 0.33), M["screen"], gfan)
# --- cooling coil: fin pack, tube bends, headers, drain pan, eliminator
gc = bpy.data.objects["ahu_coil"]
cx0, cx1 = sec["coil"]
ccx = (cx0 + cx1) / 2
fin = box("ahu_coil_fin_0", (0.32, 0.0015, AH - 0.2), (ccx, AY - 0.45, ZC + 0.03), M["fins"], gc)
for k in range(1, 46):
    linked(fin, f"ahu_coil_fin_{k}", (ccx, AY - 0.45 + 0.02 * k, ZC + 0.03), gc)
for s, yy in (("s", AY - 0.47), ("n", AY + 0.47)):
    box(f"ahu_coil_tubesheet_{s}", (0.34, 0.02, AH - 0.18), (ccx, yy, ZC + 0.03), M["galv"], gc)
for row in range(8):
    zz = AZ0 + 0.2 + 0.1 * row
    for col in (-0.08, 0.08):
        cyl(f"ahu_coil_bend_{row}_{int(col*100)}", 0.012, 0.06, (ccx + col, AY + 0.5, zz), M["copper"], gc, axis="Y", verts=8)
cyl("ahu_coil_header_sup", 0.03, AH - 0.25, (ccx - 0.12, AY + 0.55, ZC), M["copper"], gc, verts=12)
cyl("ahu_coil_header_ret", 0.03, AH - 0.25, (ccx + 0.12, AY + 0.55, ZC), M["copper"], gc, verts=12)
box("ahu_coil_drain_pan", (0.55, AW - 0.08, 0.06), (ccx, AY, AZ0 + 0.09), M["pan"], gc)
cyl("ahu_coil_drain", 0.02, 0.4, (ccx, AY - AW / 2 - 0.1, AZ0 + 0.06), M["dark"], gc, axis="Y", verts=10)
box("ahu_coil_eliminator", (0.05, AW - 0.1, AH - 0.2), (cx1 - 0.06, AY, ZC + 0.03), M["alu"], gc)
# --- discharge plenum with top outlet, flexible connector and sound attenuator
gd = bpy.data.objects["ahu_dis"]
dx = (sec["dis"][0] + sec["dis"][1]) / 2
box("ahu_dis_outlet_collar", (0.55, 0.55, 0.08), (dx + 0.1, AY, AZ0 + AH + 0.04), M["galv"], gd)
box("ahu_dis_flex_connector", (0.52, 0.52, 0.12), (dx + 0.1, AY, AZ0 + AH + 0.14), M["canvas"], gd)
for k in range(3):
    box(f"ahu_dis_splitter_{k}", (0.6, 0.06, AH - 0.3), (dx, AY - 0.3 + 0.3 * k, ZC - 0.05), M["foil"], gd)
box("ahu_control_panel", (0.5, 0.18, 0.6), (sec["dis"][1] - 0.3, AY - AW / 2 - 0.12, ZC + 0.05), M["white"], ahu, bevel=0.01)
box("ahu_control_panel_screen", (0.18, 0.005, 0.12), (sec["dis"][1] - 0.3, AY - AW / 2 - 0.215, ZC + 0.18), M["screen"], ahu)
box("ahu_control_panel_led", (0.02, 0.005, 0.02), (sec["dis"][1] - 0.18, AY - AW / 2 - 0.215, ZC + 0.18), M["green"], ahu)

# AHU <-> building ducts: supply riser from the discharge top up to plenum level, then south through the wall
SUP_X = dx + 0.1
rect_duct("duct_supply_riser", (SUP_X, AY, AZ0 + AH + 0.2), (SUP_X, AY, DY - 0.15), 0.5, 0.5, duc, hangers=False)
elbow_block("duct_supply_elbow", (SUP_X, AY, DY), 0.5, 0.3, duc)
rect_duct("duct_supply_link", (SUP_X, AY - 0.25, DY), (SUP_X, 12.3, DY), 0.5, 0.3, duc)
box("duct_supply_offset", (abs(SUP_X - MAIN_X) + 0.5, 0.5, 0.3), ((SUP_X + MAIN_X) / 2, 12.15, DY), M["galv"], duc)
# return: from the plenum, through the wall, down onto the return damper on the mixing box roof
RX = (sec["mix"][0] + sec["mix"][1]) / 2 + 0.15
rect_duct("duct_return_link", (RET_X, 13.6, DY), (RX, 13.6, DY), 0.45, 0.35, duc, insulated=False) if abs(RET_X - RX) > 0.3 else None
elbow_block("duct_return_elbow", (RX, AY, DY), 0.45, 0.35, duc)
rect_duct("duct_return_lateral", (RX, 13.6, DY), (RX, AY - 0.22, DY), 0.45, 0.35, duc, insulated=False)
rect_duct("duct_return_drop", (RX, AY, DY - 0.18), (RX, AY, AZ0 + AH + 0.1), 0.45, 0.45, duc, insulated=False, hangers=False)
# outdoor air: short weather hood is part of the AHU; relief discharges through the hood on the north side

# ----------------------------------------------------------------------------- air-cooled chiller
ch = empty("chiller")
CX0, CX1, CY0, CY1, CH = 11.2, 13.6, 13.55, 14.95, 1.75
ccx, ccy = (CX0 + CX1) / 2, (CY0 + CY1) / 2
HY = (CY1 - CY0) / 2
ZL = 0.78                                     # top of the compressor enclosure, bottom of the V coils
box("chiller_base", (CX1 - CX0 + 0.1, CY1 - CY0 + 0.1, 0.12), (ccx, ccy, 0.06), M["dark"], ch)
for k, xx in enumerate((CX0 + 0.15, CX1 - 0.15)):
    for j, yy in enumerate((CY0 + 0.15, CY1 - 0.15)):
        cyl(f"chiller_isolator_{k}{j}", 0.05, 0.06, (xx, yy, 0.15), M["rubber"], ch, verts=10)
# compressor enclosure: corner posts, louvred long sides, solid ends (south side is a removable panel)
for k, xx in enumerate((CX0, CX1)):
    for j, yy in enumerate((CY0, CY1)):
        box(f"chiller_post_{k}{j}", (0.06, 0.06, CH - 0.12), (xx, yy, (CH + 0.12) / 2), M["chiller"], ch)
for s, yy in (("s", CY0), ("n", CY1)):
    g = empty(f"chiller_lower_panel_{s}", ch)
    box(f"chiller_lower_panel_{s}_frame", (CX1 - CX0, 0.03, ZL - 0.18), (ccx, yy, (ZL + 0.18) / 2), M["chiller"], g)
    sl = box(f"chiller_lower_panel_{s}_louvre_0", (CX1 - CX0 - 0.2, 0.05, 0.025), (ccx, yy + (0.02 if s == "n" else -0.02), 0.26), M["chiller"], g)
    for k in range(1, 10):
        linked(sl, f"chiller_lower_panel_{s}_louvre_{k}", (ccx, yy + (0.02 if s == "n" else -0.02), 0.26 + 0.05 * k), g)
for s, xx in (("w", CX0), ("e", CX1)):
    box(f"chiller_end_lower_{s}", (0.03, CY1 - CY0, ZL - 0.12), (xx, ccy, (ZL + 0.12) / 2), M["chiller"], ch)
    # trapezoid end panel closing the V coil section
    mesh_from(f"chiller_end_upper_{s}", [(xx, ccy - 0.15, ZL), (xx, ccy + 0.15, ZL), (xx, CY1, CH), (xx, CY0, CH)], [(0, 1, 2, 3)], M["chiller"], ch)
box("chiller_floor_plate", (CX1 - CX0, CY1 - CY0, 0.03), (ccx, ccy, ZL), M["chiller"], ch)
# V-shaped condenser coils: aluminium fin pack, copper hairpins at both ends, coil frames
for s, sgn in (("s", -1), ("n", 1)):
    g = empty(f"chiller_condenser_{s}", ch)
    y0, y1 = ccy + sgn * 0.15, ccy + sgn * (HY - 0.03)
    q = [(CX0 + 0.08, y0, ZL), (CX1 - 0.08, y0, ZL), (CX1 - 0.08, y1, CH - 0.03), (CX0 + 0.08, y1, CH - 0.03)]
    mesh_from(f"chiller_condenser_{s}_finpack", q, [(0, 1, 2, 3)], M["fins"], g)
    # fin lines (thin ribs) to read as a coil face
    rib = None
    for k in range(48):
        xx = CX0 + 0.1 + k * (CX1 - CX0 - 0.2) / 47
        if rib is None:
            rib = poly_tube(f"chiller_condenser_{s}_rib_0", [(xx, y0 + sgn * 0.01, ZL), (xx, y1 + sgn * 0.01, CH - 0.03)], 0.003, M["alu"], g, verts=4)
        else:
            poly_tube(f"chiller_condenser_{s}_rib_{k}", [(xx, y0 + sgn * 0.01, ZL), (xx, y1 + sgn * 0.01, CH - 0.03)], 0.003, M["alu"], g, verts=4)
    for e, xx in (("w", CX0 + 0.06), ("e", CX1 - 0.06)):
        box(f"chiller_condenser_{s}_tubesheet_{e}", (0.03, 0.06, 0.06), (xx, y0, ZL), M["galv"], g)
        poly_tube(f"chiller_condenser_{s}_tubesheet_edge_{e}", [(xx, y0, ZL), (xx, y1, CH - 0.03)], 0.025, M["galv"], g, verts=4)
        for k in range(10):
            t = (k + 0.5) / 10
            yy, zz = y0 + (y1 - y0) * t, ZL + (CH - 0.03 - ZL) * t
            cyl(f"chiller_condenser_{s}_hairpin_{e}_{k}", 0.009, 0.05, (xx + (0.03 if e == "e" else -0.03), yy, zz), M["copper"], g, axis="X", verts=8)
    box(f"chiller_condenser_{s}_header", (CX1 - CX0 - 0.3, 0.04, 0.04), (ccx, y0 + sgn * 0.04, ZL + 0.05), M["copper"], g)
# top deck with fan rings, guards and rotating fans
box("chiller_top_deck", (CX1 - CX0, CY1 - CY0, 0.04), (ccx, ccy, CH), M["chiller"], ch)
for k, fxp in enumerate((CX0 + 0.6, CX1 - 0.6)):
    fz = CH + 0.1
    fg = empty(f"chiller_fan_{k}", ch, (fxp, ccy, fz))
    tube(f"chiller_fan_{k}_shroud", 0.52, 0.49, 0.2, (fxp, ccy, CH + 0.1), M["chiller"], ch, verts=40)
    cyl(f"chiller_fan_{k}_hub", 0.08, 0.1, (fxp, ccy, fz), M["fanblade"], fg, origin=(fxp, ccy, fz))
    for j in range(5):
        a = 2 * math.pi * j / 5
        vs = []
        for r, wdt, tw in ((0.08, 0.12, 0.05), (0.47, 0.20, 0.015)):
            for t in (-1, 1):
                th = a + t * wdt / (2 * r)
                vs.append((r * math.cos(th), r * math.sin(th), tw * t))
        mesh_from(f"chiller_fan_{k}_blade_{j}", vs, [(0, 1, 3, 2)], M["fanblade"], fg, loc=(fxp, ccy, fz))
    cyl(f"chiller_fan_{k}_motor", 0.09, 0.18, (fxp, ccy, fz - 0.14), M["dark"], ch, verts=16)
    for j in range(3):
        a = 2 * math.pi * j / 3 + 0.3
        box(f"chiller_fan_{k}_bracket_{j}", (0.44, 0.03, 0.02), (fxp + 0.27 * math.cos(a), ccy + 0.27 * math.sin(a), fz - 0.2), M["dark"], ch).rotation_euler = (0, 0, a)
    for j, rr in enumerate((0.5, 0.36, 0.22)):
        tube(f"chiller_fan_{k}_guard_ring_{j}", rr + 0.005, rr - 0.005, 0.008, (fxp, ccy, CH + 0.21), M["dark"], ch, verts=40)
    for j in range(8):
        box(f"chiller_fan_{k}_guard_wire_{j}", (1.0, 0.008, 0.008), (fxp, ccy, CH + 0.21), M["dark"], ch).rotation_euler = (0, 0, math.pi * j / 8)
# compressors (scroll, tandem), suction/discharge lines, plate evaporator, liquid line with sight glass
for k, xx in enumerate((CX0 + 0.45, CX0 + 0.85)):
    cyl(f"chiller_compressor_{k}", 0.13, 0.42, (xx, ccy - 0.2, 0.39), M["dark"], ch, verts=24)
    cyl(f"chiller_compressor_{k}_dome", 0.13, 0.07, (xx, ccy - 0.2, 0.635), M["dark"], ch, verts=24, r2=0.07)
    box(f"chiller_compressor_{k}_terminal", (0.1, 0.06, 0.08), (xx, ccy - 0.34, 0.45), M["dark"], ch)
    smooth_tube(f"chiller_suction_{k}", [(xx, ccy - 0.2, 0.67), (xx, ccy + 0.05, 0.7), (CX1 - 0.65, ccy + 0.05, 0.62), (CX1 - 0.65, ccy + 0.18, 0.55)], 0.016, M["copper"], ch, bend=0.1)
    smooth_tube(f"chiller_discharge_{k}", [(xx + 0.1, ccy - 0.2, 0.55), (xx + 0.1, ccy - 0.4, 0.7), (xx + 0.1, ccy - 0.4, ZL + 0.06)], 0.012, M["copper"], ch, bend=0.08)
box("chiller_evaporator", (0.42, 0.26, 0.5), (CX1 - 0.6, ccy + 0.3, 0.45), M["pan"], ch)
for k in range(14):
    box(f"chiller_evaporator_plate_{k}", (0.008, 0.27, 0.51), (CX1 - 0.79 + 0.029 * k, ccy + 0.3, 0.45), M["alu"], ch)
for k, zz in enumerate((0.3, 0.62)):
    cyl(f"chiller_evaporator_nozzle_{k}", 0.035, 0.16, (CX1 - 0.32, ccy + 0.3, zz), M["dark"], ch, axis="X", verts=12)
smooth_tube("chiller_liquid_line", [(CX0 + 1.2, ccy - 0.4, ZL + 0.06), (CX0 + 1.2, ccy + 0.1, 0.3), (CX1 - 0.8, ccy + 0.1, 0.3)], 0.009, M["copper"], ch, bend=0.08)
cyl("chiller_sight_glass", 0.02, 0.05, (CX0 + 1.2, ccy - 0.1, 0.45), M["green"], ch, verts=10)
cyl("chiller_filter_drier", 0.03, 0.18, (CX0 + 1.4, ccy + 0.1, 0.3), M["dark"], ch, axis="X", verts=12)
# electrical panel on the east end with display, isolator and LED
box("chiller_panel", (0.25, 0.9, 0.95), (CX1 + 0.16, ccy, 0.62), M["chiller"], ch, bevel=0.01)
box("chiller_panel_display", (0.005, 0.18, 0.11), (CX1 + 0.288, ccy - 0.15, 0.85), M["screen"], ch)
box("chiller_panel_led", (0.005, 0.025, 0.025), (CX1 + 0.288, ccy + 0.05, 0.85), M["green"], ch)
box("chiller_panel_isolator", (0.03, 0.12, 0.12), (CX1 + 0.295, ccy + 0.25, 0.85), M["yellow"], ch)
box("chiller_panel_isolator_handle", (0.02, 0.03, 0.1), (CX1 + 0.315, ccy + 0.25, 0.85), M["red"], ch)
box("chiller_nameplate", (0.4, 0.005, 0.1), (ccx, CY0 - 0.035, ZL - 0.12), M["blue"], ch)

# ----------------------------------------------------------------------------- chilled water loop
chw = empty("chw")
PY_SUP, PY_RET, PZ = 15.55, 15.85, 0.55
# chiller evaporator -> pump -> AHU coil supply header; coil return header -> chiller
ev = Vector((CX1 - 0.6, ccy + 0.3, 0.45))
coil_sup = Vector((sec["coil"][0] + 0.205, AY + 0.6, ZC - 0.35))
coil_ret = Vector((sec["coil"][0] + 0.445, AY + 0.6, ZC + 0.35))
pump_c = Vector((10.2, PY_SUP, PZ))
sup_pts = [tuple(ev + Vector((0, 0.15, 0.1))), (ev.x, PY_SUP, PZ), (pump_c.x + 0.3, PY_SUP, PZ)]
smooth_tube("chw_supply_pipe_a", sup_pts, 0.03, M["copper"], chw, bend=0.15)
smooth_tube("chw_supply_insul_a", sup_pts, 0.05, M["armaflex"], chw, bend=0.15)
sup_b = [(pump_c.x - 0.3, PY_SUP, PZ), (coil_sup.x, PY_SUP, PZ), (coil_sup.x, PY_SUP, coil_sup.z), tuple(coil_sup)]
smooth_tube("chw_supply_pipe_b", sup_b, 0.03, M["copper"], chw, bend=0.15)
smooth_tube("chw_supply_insul_b", sup_b, 0.05, M["armaflex"], chw, bend=0.15)
ret = [tuple(coil_ret), (coil_ret.x, PY_RET, coil_ret.z), (coil_ret.x, PY_RET, PZ + 0.45), (ev.x + 0.25, PY_RET, PZ + 0.45), (ev.x + 0.25, ev.y + 0.15, PZ + 0.45), tuple(ev + Vector((0.15, 0.15, 0.25)))]
smooth_tube("chw_return_pipe", ret, 0.03, M["copper"], chw, bend=0.15)
smooth_tube("chw_return_insul", ret, 0.05, M["armaflex"], chw, bend=0.15)
for k, (p, mm) in enumerate(((Vector((pump_c.x + 0.7, PY_SUP, PZ)), M["blue"]), (Vector((coil_ret.x, PY_RET, PZ + 0.6)), M["red"]))):
    box(f"chw_pipe_tag_{k}", (0.12, 0.11, 0.11), p, mm, chw)
# in-line pump (volute + motor), isolation valves, strainer, control valve with actuator (stem pivot)
pg = empty("chw_pump", chw, tuple(pump_c))
cyl("chw_pump_volute", 0.16, 0.14, tuple(pump_c), M["blue"], pg, axis="X", verts=24)
cyl("chw_pump_motor", 0.11, 0.32, tuple(pump_c + Vector((0, 0, 0.3))), M["motor"], pg, verts=20)
box("chw_pump_terminal", (0.1, 0.08, 0.08), tuple(pump_c + Vector((0, -0.12, 0.35))), M["motor"], pg)
cyl("chw_pump_fan_cover", 0.1, 0.05, tuple(pump_c + Vector((0, 0, 0.48))), M["dark"], pg, verts=20)
cyl("chw_pump_shaft_coupling", 0.04, 0.08, tuple(pump_c + Vector((0, 0, 0.12))), M["alu"], pg, verts=12, origin=tuple(pump_c))
for k, xx in enumerate((pump_c.x + 0.45, pump_c.x - 0.45)):
    cyl(f"chw_valve_{k}_body", 0.05, 0.12, (xx, PY_SUP, PZ), M["dark"], chw, axis="X", verts=16)
    box(f"chw_valve_{k}_handle", (0.02, 0.2, 0.02), (xx, PY_SUP - 0.05, PZ + 0.09), M["red"], chw)
cyl("chw_strainer", 0.045, 0.18, (pump_c.x + 0.9, PY_SUP, PZ - 0.06), M["dark"], chw, axis="X", verts=14)
cv = Vector((coil_ret.x, PY_RET, PZ + 0.45))
cyl("chw_control_valve_body", 0.055, 0.14, tuple(cv + Vector((0.4, 0, 0))), M["pan"], chw, axis="X", verts=16)
box("chw_control_valve_actuator", (0.12, 0.12, 0.14), tuple(cv + Vector((0.4, 0, 0.16))), M["black"], chw, bevel=0.01)
cyl("chw_control_valve_stem", 0.008, 0.08, tuple(cv + Vector((0.4, 0, 0.06))), M["alu"], chw, verts=8, origin=tuple(cv + Vector((0.4, 0, 0.02))))
for k, p in enumerate((Vector((coil_sup.x, PY_SUP, PZ + 0.2)), cv + Vector((0.15, 0, 0)))):
    cyl(f"chw_thermometer_{k}", 0.025, 0.02, tuple(p + Vector((0, -0.07, 0.04))), M["white"], chw, axis="Y", verts=12)
# pipe supports
for k, xx in enumerate((8.6, 9.4, 11.0)):
    box(f"chw_support_{k}", (0.05, 0.6, 0.05), (xx, (PY_SUP + PY_RET) / 2, 0.3), M["dark"], chw)
    box(f"chw_support_leg_{k}", (0.05, 0.05, 0.3), (xx, (PY_SUP + PY_RET) / 2, 0.15), M["dark"], chw)

# ============================================================================= export / render
prototypes = [bpy.data.objects[n] for n in ("furn_desk_proto", "furn_chair_proto", "person_proto_0", "person_proto_1", "person_proto_2")]


def export(path):
    for p in prototypes:
        p.hide_set(True)
        p.hide_render = True
    bpy.ops.object.select_all(action="SELECT")
    for p in prototypes:
        p.select_set(False)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_extras=False, export_lights=False, export_cameras=False)


def render(path, cam_loc, target, engine="CYCLES", res=(1600, 900), samples=16, hide=()):
    sc = bpy.context.scene
    for n in hide:
        for o in bpy.data.objects:
            if o.name.startswith(n):
                o.hide_render = True
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.location = cam_loc
    d = Vector(target) - Vector(cam_loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 28
    sc.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (0.8, 0.2, 0.6)
    sc.collection.objects.link(sun)
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.68, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = world
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    bpy.data.objects.remove(sun)
    for o in bpy.data.objects:
        o.hide_render = o in prototypes


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = Path(args[args.index("--out") + 1]) if "--out" in args else Path(__file__).resolve().parents[1] / "web" / "assets" / "hvac.glb"
    if "--render" in args:
        r = Path(args[args.index("--render") + 1])
        render(r.with_name(r.stem + "_overview.png"), (-6, -9, 13), (9, 8, 1.5), hide=("building_slab_above", "ceiling_tiles", "building_wall_south"))
        render(r.with_name(r.stem + "_plant.png"), (4.5, 10.8, 2.6), (8.6, 14.8, 0.8), hide=("building_slab_above", "building_wall_north", "ahu_mix_door", "ahu_filter_door", "ahu_fan_door", "ahu_coil_door", "ahu_dis_door"))
        render(r.with_name(r.stem + "_chiller.png"), (10.0, 11.6, 2.6), (12.4, 14.2, 0.9), hide=("building_slab_above", "building_wall_north"))
        render(r.with_name(r.stem + "_vav.png"), (13.0, 4.5, 2.55), (14.6, 6.0, 3.3), hide=("building_slab_above", "ceiling_tiles"))
    export(out)
    print("exported", out, "objects:", len(bpy.data.objects))

"""Small procedural-modelling helpers for bpy (Blender 5). Units: metres, Z up.

Every visible piece is a mesh object with a clear name; groups are empties. Objects that
should move in the viewer (fan impellers, damper blades, doors, valve stems) get their
origin at the pivot so the viewer only has to rotate them.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

# ----------------------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for x in list(c):
            c.remove(x)


_MATS = {}


def mat(name, color, metal=0.0, rough=0.5, alpha=1.0, emit=None, emit_strength=0.0, image=None):
    """Principled material (exported as glTF PBR)."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = emit_strength
    if image is not None:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = image
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    _MATS[name] = m
    return m


def grid_image(name, n=64, line=2, bg=(0.93, 0.93, 0.92), fg=(0.72, 0.73, 0.74)):
    """Square texture with a border line (one ceiling tile, repeated by UVs)."""
    img = bpy.data.images.new(name, n, n, alpha=False)
    px = []
    for y in range(n):
        for x in range(n):
            c = fg if (x < line or y < line) else bg
            px += [*c, 1.0]
    img.pixels = px
    img.pack()
    return img


# ----------------------------------------------------------------------------- objects
def _world_loc(o):
    p = Vector((0, 0, 0))
    while o is not None:
        p += Vector(o.location)
        o = o.parent
    return p


def attach(o, parent):
    """Parent o to parent while keeping o's current location as a world position (empties carry no rotation)."""
    if parent is None:
        return o
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Translation(-_world_loc(parent))
    return o


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    return attach(e, parent)


def _obj(name, me, m, parent, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m is not None:
        if isinstance(m, (list, tuple)):
            for mm in m:
                o.data.materials.append(mm)
        else:
            o.data.materials.append(m)
    o.location = loc
    return attach(o, parent)


def _mesh_from_bm(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def box(name, size, loc, m, parent=None, bevel=0.0, origin=None):
    """Axis-aligned box. size=(sx,sy,sz) centred on loc (or with origin at 'origin', a world point)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=bevel, segments=1, affect="EDGES")
    piv = Vector(origin) if origin is not None else Vector(loc)
    bmesh.ops.translate(bm, vec=Vector(loc) - piv, verts=bm.verts)
    return _obj(name, _mesh_from_bm(name, bm), m, parent, piv)


def cyl(name, r, depth, loc, m, parent=None, axis="Z", verts=16, r2=None, origin=None, cap=True):
    """Cylinder (or cone with r2) along an axis, centred on loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    rot = {"Z": Matrix(), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    piv = Vector(origin) if origin is not None else Vector(loc)
    bmesh.ops.translate(bm, vec=Vector(loc) - piv, verts=bm.verts)
    return _obj(name, _mesh_from_bm(name, bm), m, parent, piv)


def tube(name, r_out, r_in, depth, loc, m, parent=None, axis="Z", verts=24):
    """Hollow ring / pipe stub."""
    bm = bmesh.new()
    for r, flip in ((r_out, False), (r_in, True)):
        pass
    # outer and inner walls with end rings
    seg = verts
    rings = []
    for z in (-depth / 2, depth / 2):
        ro = [bm.verts.new((r_out * math.cos(2 * math.pi * i / seg), r_out * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)]
        ri = [bm.verts.new((r_in * math.cos(2 * math.pi * i / seg), r_in * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)]
        rings.append((ro, ri))
    (o0, i0), (o1, i1) = rings
    for k in range(seg):
        n = (k + 1) % seg
        bm.faces.new((o0[k], o0[n], o1[n], o1[k]))
        bm.faces.new((i0[n], i0[k], i1[k], i1[n]))
        bm.faces.new((o0[n], o0[k], i0[k], i0[n]))
        bm.faces.new((o1[k], o1[n], i1[n], i1[k]))
    rot = {"Z": Matrix(), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    return _obj(name, _mesh_from_bm(name, bm), m, parent, loc)


def poly_tube(name, points, r, m, parent=None, verts=12):
    """Round pipe or flexible duct along a polyline (curve with bevel, converted to mesh)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = max(1, verts // 4 - 1)
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (*q, 1)
    o = bpy.data.objects.new(name + "_c", cu)
    bpy.context.scene.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(cu)
    return _obj(name, me, m, parent)


def smooth_tube(name, points, r, m, parent=None, verts=12, bend=0.25):
    """Pipe along a polyline with rounded bends (bend radius ~ bend)."""
    pts = [Vector(p) for p in points]
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        d1, d2 = (b - a).normalized(), (c - b).normalized()
        rr = min(bend, (b - a).length / 2, (c - b).length / 2)
        p0, p2 = b - d1 * rr, b + d2 * rr
        for t in [i / 6 for i in range(7)]:
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2)
    out.append(pts[-1])
    return poly_tube(name, [tuple(p) for p in out], r, m, parent, verts)


def mesh_from(name, verts, faces, m, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return _obj(name, me, m, parent, loc)


def linked(src, name, loc, parent=None, rot=(0, 0, 0)):
    """Instance sharing the mesh of src (exported once in glTF)."""
    o = bpy.data.objects.new(name, src.data)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return attach(o, parent)


def join(name, objs, origin=None):
    """Join meshes into one object (fewer draw calls); origin: world point for the new pivot (default: first object's)."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    if origin is not None:
        off = Vector(o.location) - Vector(origin)
        o.data.transform(Matrix.Translation(off))
        o.location = origin
    return o


def loft(name, ring0, ring1, m, parent=None, cap=False):
    """Skin between two rings of equal vertex count (e.g. rectangle-to-round transition)."""
    n = len(ring0)
    verts = list(ring0) + list(ring1)
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    # make the winding face outward (away from the ring axis)
    c0 = sum((Vector(v) for v in ring0), Vector()) / n
    c1 = sum((Vector(v) for v in ring1), Vector()) / n
    a, b_, c = Vector(verts[0]), Vector(verts[1]), Vector(verts[n + 1])
    nrm = (b_ - a).cross(c - a)
    if nrm.dot(a - c0) < 0:
        faces = [tuple(reversed(f)) for f in faces]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    return _obj(name, me, m, parent, (0, 0, 0))


def rect_ring(c, w, h, axis, n=16):
    """n points around a w x h rectangle perpendicular to axis ('X' or 'Y'), starting at angle 0."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        u, v = math.cos(a), math.sin(a)
        s = max(abs(u) / (w / 2), abs(v) / (h / 2))
        u, v = u / s, v / s
        pts.append(Vector(c) + (Vector((0, u, v)) if axis == "X" else Vector((u, 0, v))))
    return pts


def round_ring(c, r, axis, n=16):
    return [Vector(c) + (Vector((0, r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n))) if axis == "X"
                         else Vector((r * math.cos(2 * math.pi * k / n), 0, r * math.sin(2 * math.pi * k / n)))) for k in range(n)]


def set_parent_keep(child, parent):
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw


def uv_box_project(o, scale=1.0):
    """World-space planar UVs (for tiled textures)."""
    me = o.data
    uv = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        n = poly.normal
        for li in poly.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) >= max(abs(n.x), abs(n.y)):
                uv.data[li].uv = (v.x / scale, v.y / scale)
            elif abs(n.x) >= abs(n.y):
                uv.data[li].uv = (v.y / scale, v.z / scale)
            else:
                uv.data[li].uv = (v.x / scale, v.z / scale)

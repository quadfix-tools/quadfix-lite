"""Mesh generators shared by the test runners. Import with `from meshes import *`."""
import bpy, bmesh, math, random
from math import radians
from mathutils import Vector, Matrix



def stats(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    t = sum(1 for f in bm.faces if len(f.verts) == 3)
    q = sum(1 for f in bm.faces if len(f.verts) == 4)
    n = len(bm.faces) - t - q
    b = sum(1 for e in bm.edges if e.is_boundary)
    nm = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    bm.free()
    return dict(verts=len(obj.data.vertices), tris=t, quads=q, ngons=n, boundary=b, nonmanifold=nm)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def edit(obj, select_all=True):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT" if select_all else "DESELECT")


def done():
    bpy.ops.object.mode_set(mode="OBJECT")


def make_suzanne_with_holes():
    bpy.ops.mesh.primitive_monkey_add(size=2)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    # delete a few face patches -> holes
    for i in (10, 11, 12, 13, 200, 201, 300):
        pass
    from mathutils import Vector
    def patch(center, r):
        return [f for f in bm.faces if (f.calc_center_median() - Vector(center)).length < r]
    kill = patch((0.0, -0.9, 0.55), 0.22) + patch((0.9, 0.4, -0.2), 0.25) + patch((-0.55, -0.75, -0.25), 0.2)
    kill = list(dict.fromkeys(kill))
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_stock_suzanne():
    bpy.ops.mesh.primitive_monkey_add(size=2)
    return bpy.context.object


def make_boolean_junk():
    bpy.ops.mesh.primitive_cube_add(size=2)
    a = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.1, location=(0.7, 0.4, 0.3), segments=24, ring_count=12)
    b = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=4, location=(-0.5, -0.5, 0), vertices=16)
    c = bpy.context.object
    for cutter in (b, c):
        m = a.modifiers.new("bool", "BOOLEAN"); m.object = cutter; m.operation = "DIFFERENCE"
    bpy.context.view_layer.objects.active = a
    for m in list(a.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(b); bpy.data.objects.remove(c)
    return a


def make_ring_gap():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if 0.35 < f.calc_center_median().z < 0.62]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_tilted_band():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if 0.25 < (f.calc_center_median().z + 0.5 * f.calc_center_median().x) < 0.55]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_equator_band():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if -0.12 < (f.calc_center_median().z + 0.3 * f.calc_center_median().x) < 0.2]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_horseshoe():
    import math
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if -0.05 < f.calc_center_median().z < 0.36
            and math.atan2(f.calc_center_median().y, f.calc_center_median().x) > -2.2]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_jagged_band():
    import math
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median(); ang = math.atan2(c.y, c.x)
        if 0.0 < c.z < 0.2 and ang > -2.2: kill.append(f)
        if 0.2 < c.z < 0.4 and ang > -1.8: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_jagged_both():
    import math
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = []
    for f in bm.faces:
        c = f.calc_center_median(); ang = math.atan2(c.y, c.x)
        if 0.0 < c.z < 0.2 and -2.2 < ang < 2.6: kill.append(f)
        if 0.2 < c.z < 0.4 and -1.8 < ang < 2.9: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_triangulated_scan():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    # noise + duplicate verts + loose verts
    import random; random.seed(1)
    for v in bm.verts:
        v.co += v.normal * random.uniform(-0.01, 0.01)
    for i in range(20):
        bm.verts.new((random.uniform(-2, 2),) * 3)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in range(0, 40)], context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_holed_sphere():
    """UV sphere with three round holes (marketing hero case: lattice must be rebuilt without slivers)."""
    from mathutils import Vector
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = []
    for c, r in (((0.55, -0.75, 0.4), 0.42), ((-0.6, -0.6, -0.45), 0.3), ((0.95, -0.2, -0.15), 0.28)):
        kill += [f for f in bm.faces if (f.calc_center_median() - Vector(c)).length < r]
    bmesh.ops.delete(bm, geom=list(dict.fromkeys(kill)), context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_pole_block():
    """7x7 block of faces removed two rings below the pole (Pavel's GUI test, v1.1.4 left 2 tris + open edges)."""
    import math
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1)
    obj = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = []
    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        c = f.calc_center_median()
        ring = int((90 - math.degrees(math.asin(max(-1, min(1, c.z))))) / (180 / 16))
        seg = int((math.degrees(math.atan2(c.y, c.x)) % 360) / (360 / 32))
        if 2 <= ring < 9 and 8 <= seg < 15:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj




# ------------------------------------------------------------- edge cases

def _sphere(segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1)
    return bpy.context.object


def _kill(obj, pred):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [f for f in bm.faces if pred(f)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_pole_touching_hole():
    """Hole that includes the pole cap triangles (loop goes around the pole)."""
    return _kill(_sphere(), lambda f: f.calc_center_median().z > 0.86)


def make_two_holes_shared_vertex():
    """Two 2x2 holes touching diagonally at one vertex (non-manifold-ish loop walk)."""
    obj = _sphere()
    def pred(f):
        c = f.calc_center_median(); a = math.degrees(math.atan2(c.y, c.x)) % 360
        ring = int((90 - math.degrees(math.asin(max(-1, min(1, c.z))))) / (180 / 16))
        seg = int(a / (360 / 32))
        return (ring in (6, 7) and seg in (8, 9)) or (ring in (8, 9) and seg in (10, 11))
    return _kill(obj, pred)


def make_tiny_holes():
    """Single-face holes (4-vert loops) and a 3-vert hole at the pole ring, chosen geometrically."""
    obj = _sphere()
    targets = [Vector((0.6, 0.6, 0.5)), Vector((-0.7, 0.2, -0.6)), Vector((0.1, -0.9, 0.3)), Vector((0.05, 0.02, 0.99))]
    bm = bmesh.new(); bm.from_mesh(obj.data)
    kill = [min(bm.faces, key=lambda f: (f.calc_center_median() - t).length) for t in targets]
    bmesh.ops.delete(bm, geom=list(dict.fromkeys(kill)), context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_quad_tri_hole():
    """A pole triangle plus its neighbouring quad removed: a 5-vertex loop."""
    obj = _sphere()
    bm = bmesh.new(); bm.from_mesh(obj.data)
    tri = min((f for f in bm.faces if len(f.verts) == 3 and f.calc_center_median().z > 0),
              key=lambda f: (f.calc_center_median() - Vector((0.1, 0.0, 0.99))).length)
    quad = next(f for e in tri.edges for f in e.link_faces if len(f.verts) == 4)
    bmesh.ops.delete(bm, geom=[tri, quad], context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_open_plane():
    """Subdivided plane: its outer border is a closed boundary loop (must not crash, must stay manifold)."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=8, size=2)
    return bpy.context.object


def make_plane_with_hole():
    """Flat grid with a 3x3 hole: zero-curvature lattice reconstruction."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=2)
    obj = bpy.context.object
    return _kill(obj, lambda f: abs(f.calc_center_median().x) < 0.3 and abs(f.calc_center_median().y) < 0.3)


def make_single_quad():
    bpy.ops.mesh.primitive_plane_add(size=1)
    return bpy.context.object


def make_transformed_holed_sphere():
    """Holed sphere with non-uniform scale + rotation: ops must work in local space."""
    obj = make_holed_sphere()
    obj.scale = (0.3, 2.0, 1.2); obj.rotation_euler = (0.7, 0.2, 1.1); obj.location = (5, -3, 2)
    return obj


def make_attributed_holed_sphere():
    """Holed sphere carrying UVs, a color attribute, a vertex group and custom normals: nothing may be lost."""
    obj = make_holed_sphere()
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    vg = obj.vertex_groups.new(name="Group")
    vg.add(list(range(len(me.vertices))), 0.5, "REPLACE")
    me.shade_smooth()
    return obj


def make_ai_like_mesh():
    """Decimated Suzanne: dense triangle soup with a few holes (stand-in for Tripo/Meshy output)."""
    bpy.ops.mesh.primitive_monkey_add(size=2)
    obj = bpy.context.object
    m = obj.modifiers.new("sub", "SUBSURF"); m.levels = 2
    bpy.ops.object.modifier_apply(modifier="sub")
    m = obj.modifiers.new("tri", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier="tri")
    m = obj.modifiers.new("dec", "DECIMATE"); m.ratio = 0.6
    bpy.ops.object.modifier_apply(modifier="dec")
    random.seed(3)
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    idx = random.sample(range(len(bm.faces)), 12)
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in idx], context="FACES")
    bm.to_mesh(obj.data); bm.free()
    return obj


def make_big_mesh():
    """~200k faces with holes: performance guard."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=512, ring_count=400, radius=1)
    obj = bpy.context.object
    return _kill(obj, lambda f: (f.calc_center_median() - Vector((0.6, -0.7, 0.3))).length < 0.15)


def make_two_objects():
    """Two holed spheres, both entered into multi-object edit mode."""
    a = make_holed_sphere(); a.location = (-2, 0, 0)
    b = make_holed_sphere(); b.location = (2, 0, 0)
    return a, b

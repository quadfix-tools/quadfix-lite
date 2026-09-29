# QuadFix Lite - N-gons to quads and mesh cleanup for Blender.
# Copyright (C) 2026 QuadFix Tools
# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
import bmesh
from math import radians
from bpy.props import FloatProperty, BoolProperty, PointerProperty
from bpy.types import Operator, PropertyGroup


# ---------------------------------------------------------------- helpers

def _bm_from_edit(obj):
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def _update(obj, bm):
    bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)


def _stats(bm):
    tris = sum(1 for f in bm.faces if len(f.verts) == 3)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    ngons = len(bm.faces) - tris - quads
    return tris, quads, ngons


def _is_planar(f, tol):
    """True if all verts lie within tol*face_size of the face plane."""
    if len(f.verts) <= 4:
        return True
    n = f.normal
    if n.length == 0:
        return False
    c = f.calc_center_median()
    size = max((v.co - c).length for v in f.verts) or 1.0
    return all(abs((v.co - c).dot(n)) <= tol * size for v in f.verts)


def _tris_to_quads(bm, faces, angle_face, angle_shape, aggressive=False):
    if aggressive:
        angle_face = angle_shape = radians(180)
    res = bmesh.ops.join_triangles(
        bm, faces=[f for f in faces if len(f.verts) == 3],
        angle_face_threshold=angle_face, angle_shape_threshold=angle_shape,
        cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False, cmp_materials=False)
    return res.get("faces", [])


# ---------------------------------------------------------------- properties

class QuadFixLiteProps(PropertyGroup):
    merge_dist: FloatProperty(name="Merge Distance", default=0.0001, min=0.0, precision=5,
                              description="Merge vertices closer than this")
    angle_face: FloatProperty(name="Face Angle", default=radians(90), min=0, max=radians(180), subtype="ANGLE",
                              description="Max angle between triangle normals to join into a quad")
    angle_shape: FloatProperty(name="Shape Angle", default=radians(90), min=0, max=radians(180), subtype="ANGLE",
                               description="Max deviation from a rectangle to accept a quad")
    keep_sharp: BoolProperty(name="Keep Sharp Edges", default=True,
                             description="Do not dissolve edges marked sharp")
    dissolve_angle: FloatProperty(name="Dissolve Angle", default=radians(5), min=0, max=radians(90), subtype="ANGLE",
                                  description="Limited dissolve angle for boolean cleanup")
    only_selected: BoolProperty(name="Only Selected", default=True,
                                description="Restrict to selected geometry (Edit Mode); off = whole mesh")
    keep_planar: BoolProperty(name="Keep Planar N-gons", default=True,
                              description="Leave flat n-gons untouched (clean on flat surfaces); only convert curved n-gons and triangles")
    aggressive: BoolProperty(name="Aggressive Quads", default=False,
                             description="Join any two triangles into a quad regardless of angle (fewest triangles, less regular shapes)")
    report: bpy.props.StringProperty(name="Report", default="")


def register_props():
    bpy.types.Scene.quadfix_lite = PointerProperty(type=QuadFixLiteProps)


def unregister_props():
    del bpy.types.Scene.quadfix_lite


# ---------------------------------------------------------------- operators

class QUADFIXLITE_OT_ngons_to_quads(Operator):
    """Convert selected n-gons and triangles into quads"""
    bl_idname = "quadfix_lite.ngons_to_quads"
    bl_label = "N-gons to Quads"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.edit_object

    def execute(self, context):
        p = context.scene.quadfix_lite
        obj = context.edit_object
        bm = _bm_from_edit(obj)
        bm.normal_update()
        faces = [f for f in bm.faces if (f.select or not p.only_selected) and len(f.verts) != 4
                 and not (p.keep_planar and len(f.verts) > 4 and _is_planar(f, 0.01))]
        if not faces:
            self.report({"INFO"}, "Nothing to convert (all quads or flat n-gons)")
            return {"CANCELLED"}
        before = _stats(bm)
        tri = bmesh.ops.triangulate(bm, faces=faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        _tris_to_quads(bm, tri["faces"], p.angle_face, p.angle_shape, p.aggressive)
        _update(obj, bm)
        after = _stats(bm)
        p.report = f"n-gons {before[2]}→{after[2]}, tris {before[0]}→{after[0]}, quads {before[1]}→{after[1]}"
        self.report({"INFO"}, p.report)
        return {"FINISHED"}


class QUADFIXLITE_OT_clean(Operator):
    """Clean boolean/imported mesh: merge doubles, remove degenerate & loose geometry, limited dissolve, quads, normals"""
    bl_idname = "quadfix_lite.clean"
    bl_label = "Clean & Quad"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.edit_object

    def execute(self, context):
        p = context.scene.quadfix_lite
        obj = context.edit_object
        bm = _bm_from_edit(obj)
        sel = lambda g: (g.select or not p.only_selected)
        verts = [v for v in bm.verts if sel(v)]
        before = _stats(bm)
        nv0 = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=verts, dist=p.merge_dist)
        bm.verts.ensure_lookup_table()
        verts = [v for v in bm.verts if sel(v)]
        edges = [e for e in bm.edges if sel(e)]
        bmesh.ops.dissolve_degenerate(bm, dist=p.merge_dist, edges=edges)
        loose_v = [v for v in bm.verts if sel(v) and not v.link_edges]
        loose_e = [e for e in bm.edges if sel(e) and not e.link_faces]
        bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
        bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
        verts = [v for v in bm.verts if sel(v)]
        edges = [e for e in bm.edges if sel(e)]
        if p.keep_sharp:
            edges = [e for e in edges if e.smooth]
        # remember original planar n-gons (the ones Keep Planar protects)
        protected = set()
        if p.keep_planar:
            bm.normal_update()  # normals are stale after remove_doubles / dissolve_degenerate
            protected = {f for f in bm.faces if sel(f) and len(f.verts) > 4 and _is_planar(f, 0.01)}
        bmesh.ops.dissolve_limit(bm, angle_limit=p.dissolve_angle, use_dissolve_boundaries=False,
                                 verts=verts, edges=edges, delimit={"SHARP", "SEAM"} if p.keep_sharp else set())
        protected = {f for f in protected if f.is_valid}
        # faces created by the dissolve are unselected in face select mode: select them
        # when all their vertices are selected, so "Only Selected" keeps working
        for f in bm.faces:
            if not f.select and all(v.select for v in f.verts):
                f.select = True
        # n-gons created by the dissolve itself are always converted; original flat n-gons stay
        faces = [f for f in bm.faces if sel(f) and len(f.verts) != 4 and f not in protected]
        if faces:
            tri = bmesh.ops.triangulate(bm, faces=faces, quad_method="BEAUTY", ngon_method="BEAUTY")
            _tris_to_quads(bm, tri["faces"], p.angle_face, p.angle_shape, p.aggressive)
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if sel(f)])
        _update(obj, bm)
        after = _stats(bm)
        p.report = (f"verts {nv0}→{len(bm.verts)}, quads {before[1]}→{after[1]}, "
                    f"tris {before[0]}→{after[0]}, n-gons {before[2]}→{after[2]}")
        self.report({"INFO"}, p.report)
        return {"FINISHED"}


class QUADFIXLITE_OT_select_bad(Operator):
    """Select all non-quad faces and boundary (hole) edges"""
    bl_idname = "quadfix_lite.select_bad"
    bl_label = "Select Non-Quads & Holes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and context.edit_object

    def execute(self, context):
        obj = context.edit_object
        bm = _bm_from_edit(obj)
        for g in (bm.verts, bm.edges, bm.faces):
            for x in g:
                x.select = False
        nbad = 0
        for f in bm.faces:
            if len(f.verts) != 4:
                f.select = True
                nbad += 1
        nholes = 0
        for e in bm.edges:
            if e.is_boundary:
                e.select = True
                nholes += 1
        bm.select_flush_mode()
        _update(obj, bm)
        context.scene.quadfix_lite.report = f"{nbad} non-quad faces, {nholes} boundary edges"
        self.report({"INFO"}, context.scene.quadfix_lite.report)
        return {"FINISHED"}


classes = (QuadFixLiteProps, QUADFIXLITE_OT_ngons_to_quads, QUADFIXLITE_OT_clean, QUADFIXLITE_OT_select_bad)

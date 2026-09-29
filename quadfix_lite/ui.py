# SPDX-License-Identifier: GPL-3.0-or-later
import os
import tomllib
from bpy.types import Panel


def _version():
    try:
        with open(os.path.join(os.path.dirname(__file__), "blender_manifest.toml"), "rb") as f:
            return tomllib.load(f).get("version", "?")
    except Exception:
        return "?"


VERSION = _version()


class QUADFIXLITE_PT_panel(Panel):
    bl_label = "QuadFix Lite"
    bl_idname = "QUADFIXLITE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "QuadFix Lite"
    bl_context = "mesh_edit"

    def draw(self, context):
        p = context.scene.quadfix_lite
        col = self.layout.column(align=True)
        col.prop(p, "only_selected")
        col.separator()
        col.operator("quadfix_lite.select_bad", icon="RESTRICT_SELECT_OFF")
        col.separator()
        box = col.box()
        box.label(text="Quads", icon="MOD_TRIANGULATE")
        box.operator("quadfix_lite.ngons_to_quads", icon="MESH_PLANE")
        box.prop(p, "angle_face")
        box.prop(p, "angle_shape")
        box.prop(p, "keep_planar")
        box.prop(p, "aggressive")
        box = col.box()
        box.label(text="Boolean / Import Cleanup", icon="MOD_BOOLEAN")
        box.operator("quadfix_lite.clean", icon="BRUSH_DATA")
        box.prop(p, "merge_dist")
        box.prop(p, "dissolve_angle")
        box.prop(p, "keep_sharp")
        if p.report:
            col.separator()
            col.label(text=p.report, icon="INFO")
        col.separator()
        col.label(text=f"QuadFix Lite v{VERSION}")


classes = (QUADFIXLITE_PT_panel,)

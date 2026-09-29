# SPDX-License-Identifier: GPL-3.0-or-later
import bpy
from . import ops, ui

_classes = ops.classes + ui.classes


def register():
    for c in _classes:
        bpy.utils.register_class(c)
    ops.register_props()


def unregister():
    ops.unregister_props()
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)

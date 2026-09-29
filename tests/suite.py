"""QuadFix Lite assertion suite. Run: blender -b --factory-startup --python tests/suite.py [-- --quick]
Exit code 1 on any failure. Every case runs under a matrix of select modes and
selection variants; every result is checked against mesh invariants."""
import bpy, bmesh, sys, os, time, math, traceback, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import quadfix_lite
quadfix_lite.register()
from meshes import *

QUICK = "--quick" in sys.argv
MODES = {"V": (True, False, False), "E": (False, True, False), "F": (False, False, True)}
FAILS, PASSES, SKIPS = [], 0, []


def face_hash(obj, pred=lambda f: True):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    h = hashlib.md5()
    for f in bm.faces:
        if pred(f):
            h.update(str([tuple(round(c, 5) for c in v.co) for v in f.verts]).encode())
    bm.free()
    return h.hexdigest()


def mesh_report(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.normal_update()
    r = dict(faces=len(bm.faces),
             tris=sum(1 for f in bm.faces if len(f.verts) == 3),
             quads=sum(1 for f in bm.faces if len(f.verts) == 4),
             ngons=sum(1 for f in bm.faces if len(f.verts) > 4),
             boundary=sum(1 for e in bm.edges if e.is_boundary),
             nonmanifold=sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
             loose_verts=sum(1 for v in bm.verts if not v.link_edges),
             degenerate=sum(1 for f in bm.faces if f.calc_area() < 1e-9),
             folds=0, worst_dihedral=0.0)
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) == 2 and lf[0].normal.length > 1e-9 and lf[1].normal.length > 1e-9:
            a = math.degrees(lf[0].normal.angle(lf[1].normal))
            r["worst_dihedral"] = max(r["worst_dihedral"], a)
            if a > 110: r["folds"] += 1
    r["radius"] = max((v.co.length for v in bm.verts), default=0)
    bm.free()
    return r


def attrs(obj):
    me = obj.data
    return dict(uv=len(me.uv_layers), col=len(me.color_attributes), vg=len(obj.vertex_groups))


def select_variant(obj, variant):
    """Set up the edit-mode selection for a variant. Returns pred of faces expected untouched."""
    if variant == "all":
        bpy.ops.mesh.select_all(action="SELECT")
        return None
    if variant == "half":
        # select faces with local x > 0 only (partial selection, Only Selected on)
        bm = bmesh.from_edit_mesh(obj.data)
        for f in bm.faces:
            f.select = f.calc_center_median().x > 0
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)
        return lambda f: f.calc_center_median().x < -0.05
    if variant == "none":
        bpy.ops.mesh.select_all(action="DESELECT")
        return lambda f: True


def run_case(name, maker, op, variants=("all", "half"), modes=("V", "F"), expect=None, timeout=60):
    """expect: dict of checks. Defaults: valid, no new non-manifold, no degenerate, no loose,
    attrs preserved, untouched faces unchanged. For fill: boundary==0, folds==0."""
    expect = expect or {}
    for mode in modes:
        for variant in variants:
            label = f"{name} [{mode}/{variant}]"
            try:
                reset()
                made = maker()
                objs = list(made) if isinstance(made, tuple) else [made]
                obj = objs[0]
                for o in objs: o.select_set(True)
                bpy.context.view_layer.objects.active = obj
                before = mesh_report(obj); a0 = attrs(obj)
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.context.tool_settings.mesh_select_mode = MODES[mode]
                untouched = select_variant(obj, variant)
                h_before = face_hash(obj, untouched) if untouched else None
                t = time.time()
                res = op()
                dt = time.time() - t
                bpy.ops.object.mode_set(mode="OBJECT")
                after = mesh_report(obj); a1 = attrs(obj)
                errs = []
                if obj.data.validate(verbose=False):
                    errs.append("mesh.validate() had to fix data")
                if "FINISHED" not in res and variant == "all" and "cancel_ok" not in expect:
                    errs.append(f"operator returned {res}")
                if after["nonmanifold"] > before["nonmanifold"]:
                    errs.append(f"non-manifold {before['nonmanifold']}→{after['nonmanifold']}")
                if after["degenerate"] > before["degenerate"]:
                    errs.append(f"degenerate faces {before['degenerate']}→{after['degenerate']}")
                if after["folds"] > before["folds"] and "folds_ok" not in expect:
                    errs.append(f"folds {before['folds']}→{after['folds']}")
                if after["loose_verts"] > before["loose_verts"] and "loose_ok" not in expect:
                    errs.append(f"loose verts {before['loose_verts']}→{after['loose_verts']}")
                if a1 != a0:
                    errs.append(f"attributes changed {a0}→{a1}")
                if untouched and face_hash(obj, untouched) != h_before:
                    errs.append("faces outside the selection were modified")
                if after["radius"] > before["radius"] * 1.15 + 1e-6:
                    errs.append(f"geometry exploded: radius {before['radius']:.3f}→{after['radius']:.3f}")
                if dt > timeout:
                    errs.append(f"took {dt:.1f}s > {timeout}s")
                if variant == "all":
                    for k, v in expect.items():
                        if k in ("loose_ok", "folds_ok", "cancel_ok"): continue
                        if callable(v):
                            if not v(before, after): errs.append(f"expect {k} failed: {after}")
                        elif after.get(k) != v:
                            errs.append(f"{k}={after.get(k)} expected {v}")
                if errs:
                    FAILS.append((label, errs, before, after))
                    print(f"FAIL  {label}: " + "; ".join(errs))
                else:
                    global PASSES; PASSES += 1
                    print(f"ok    {label}  {dt:.2f}s  q{after['quads']} t{after['tris']} n{after['ngons']} b{after['boundary']}")
            except Exception:
                FAILS.append((label, [traceback.format_exc().splitlines()[-1]], None, None))
                print(f"ERROR {label}:\n" + traceback.format_exc())


def undo_case(name, maker, op):
    """Operator must be undoable: after ed.undo the mesh equals the original."""
    label = f"{name} [undo]"
    try:
        reset(); obj = maker(); h0 = face_hash(obj)
        edit(obj)
        bpy.ops.ed.undo_push(message="before")
        op()
        bpy.ops.ed.undo_push(message="after")
        bpy.ops.ed.undo()
        bpy.ops.object.mode_set(mode="OBJECT")
        h1 = face_hash(obj)
        if h0 != h1:
            FAILS.append((label, ["mesh differs after undo"], None, None)); print(f"FAIL  {label}")
        else:
            global PASSES; PASSES += 1; print(f"ok    {label}")
    except Exception as e:
        SKIPS.append((label, str(e).splitlines()[-1])); print(f"SKIP  {label}: {str(e).splitlines()[-1]}")


CLEAN = bpy.ops.quadfix_lite.clean
NGONS = bpy.ops.quadfix_lite.ngons_to_quads
SELECT = bpy.ops.quadfix_lite.select_bad
assert "fill_quads" not in dir(bpy.ops.quadfix_lite), "Lite must not contain hole filling"

run_case("boolean clean", make_boolean_junk, CLEAN, expect=dict(quads=lambda b, a: a["quads"] >= 129, ngons=12))
run_case("boolean ngons", make_boolean_junk, NGONS, expect=dict(quads=lambda b, a: a["quads"] >= 129))
run_case("tri scan clean", make_triangulated_scan, CLEAN, expect=dict(quads=lambda b, a: a["quads"] > 380), variants=("all",))
run_case("tri scan ngons", make_triangulated_scan, NGONS, expect=dict(quads=lambda b, a: a["quads"] > 500), variants=("all",))
run_case("ai-like ngons", make_ai_like_mesh, NGONS, expect=dict(quads=lambda b, a: a["quads"] > b["faces"] * 0.3))
run_case("ai-like clean", make_ai_like_mesh, CLEAN)
run_case("attributed ngons", make_attributed_holed_sphere, NGONS)
run_case("attributed clean", make_attributed_holed_sphere, CLEAN)
run_case("single quad clean", make_single_quad, CLEAN, variants=("all",))
run_case("select bad", make_holed_sphere, SELECT, variants=("all", "none"))
# ---- nothing selected: must not crash, must not touch anything
run_case("nothing selected clean", make_boolean_junk, CLEAN, variants=("none",), modes=("F",))
for nm, mk, op in (("clean", make_boolean_junk, CLEAN), ("ngons", make_triangulated_scan, NGONS)):
    undo_case(nm, mk, op)
if not QUICK:
    run_case("big mesh clean", make_big_mesh, CLEAN, variants=("all",), modes=("F",), timeout=120)

print(f"\n{PASSES} passed, {len(FAILS)} failed, {len(SKIPS)} skipped  (Blender {bpy.app.version_string})")
for label, errs, b, a in FAILS:
    print(f"  FAIL {label}: {'; '.join(errs)}")
sys.exit(1 if FAILS else 0)

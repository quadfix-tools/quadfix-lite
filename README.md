# QuadFix Lite

Free Blender add-on (Blender 4.2 LTS and newer) that cleans up meshes and turns triangles and curved n-gons into quads.

## What it does

- **N-gons to Quads**: converts triangles and curved n-gons to quads. Flat n-gons (caps, CAD faces) stay untouched by default, so clean flat surfaces stay clean.
- **Clean & Quad**: after a Boolean cut or an import (STL, OBJ, FBX, CAD, scans, AI-generated meshes): merge doubles, remove degenerate and loose geometry, limited dissolve that keeps sharp edges, tris to quads, recalculate normals.
- **Select Non-Quads & Holes**: selects every face that is not a quad and every open boundary edge, and prints the counts in the panel.
- Works on the selection or on the whole mesh. One undo step per operation.

## Install

1. Download `quadfix_lite-1.0.0.zip` from the Releases page (do not unzip it).
2. In Blender: **Edit > Preferences > Get Extensions**, open the small arrow menu at the top right, choose **Install from Disk**, pick the zip.
3. In the 3D viewport press `Tab` (Edit Mode), press `N`, open the **QuadFix Lite** tab.

## What it does not do

- It does not fill holes. Closing a hole with a proper quad grid is a separate, harder problem: see the full [QuadFix](https://quadfix.gumroad.com/l/quadfix) add-on (paid).
- It is not a remesher. It repairs the mesh you have and does not rebuild edge flow. Dense scans keep some triangles.

## Tests

`tests/run_all_versions.sh` runs the assertion suite (38 checks) on every Blender found in `/Applications` and `~/Applications/blender-versions`. Last run: Blender 4.2.23, 4.5.14 and 5.2.2, all passing.

## License

GPL-3.0-or-later, see `LICENSE`. Blender add-ons that use the Blender Python API must be GPL-compatible, and the Blender Extensions platform requires `GPL-3.0-or-later` for add-ons.

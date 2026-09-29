#!/bin/sh
# Run the assertion suite on every Blender found. Usage: tests/run_all_versions.sh [--quick]
cd "$(dirname "$0")/.."
rc=0
for B in /Applications/Blender.app ~/Applications/blender-versions/Blender-*.app; do
  [ -x "$B/Contents/MacOS/Blender" ] || continue
  echo "=================== $B"
  "$B/Contents/MacOS/Blender" -b --factory-startup --python tests/suite.py -- "$@" 2>&1 | grep -E "^(ok|FAIL|ERROR|SKIP|  FAIL|[0-9]+ passed)|Traceback|Error:" || rc=1
  [ "${PIPESTATUS:-0}" = "0" ] || rc=1
done
exit $rc

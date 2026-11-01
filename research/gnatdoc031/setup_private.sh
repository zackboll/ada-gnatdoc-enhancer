#!/bin/sh
# Invoke with a NEW absolute workspace path. No global toolchain/package edits.
set -eu
script_directory=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
workspace=$1
case "$workspace" in /*) ;; *) echo 'workspace must be absolute' >&2; exit 2;; esac
test ! -e "$workspace"
mkdir -p "$workspace"
cd "$workspace"
python3 -m venv venv
alr -n get libadalang=26.0.0 > get.log 2>&1
cd libadalang_26.0.0_75276b8d
# Preserve the measured dependency solution against future index changes.
cp "$script_directory/alire.lock" alire/alire.lock
alr settings --set dependencies.shared false
alr -n toolchain --select --local gnat_native=15.3.1 gprbuild=26.0.1
alr -n build --stop-after=generation > ../generation.log 2>&1
# Global LIBRARY_TYPE must apply to the dependency closure, not only Libadalang.
alr -n build -- -j2 -XLIBRARY_TYPE=relocatable > ../shared-build.log 2>&1
alr -n printenv > ../private-build-environment.txt
alr -n exec -- gprinstall -p -r -P libadalang.gpr -XLIBRARY_TYPE=relocatable \
    --prefix="$workspace/install" > ../private-install.log 2>&1
# XMLAda is imported through an aggregate project; recursive installation of
# Libadalang alone does not install its component shared libraries.
alr -n exec -- gprinstall -p -r \
    -P alire/cache/dependencies/xmlada_26.0.0_b140ed4a/xmlada.gpr \
    -XLIBRARY_TYPE=relocatable --prefix="$workspace/install" > ../xmlada-install.log 2>&1
"$workspace/venv/bin/python" -m pip install ./python > ../python-install.log 2>&1
cd "$workspace"
# Runtime settings are explicit and process-local. Compiler used to analyze
# Core can differ from the compiler used to build the native shared library.
python3 - "$workspace" <<'PY'
from pathlib import Path
import shlex
import sys
root = Path(sys.argv[1])
dirs = sorted({str(p.parent) for p in (root / 'install').rglob('*.so*')})
# GNAT runtime is not installed by gprinstall. Read the actual resolved Alire
# environment rather than assuming the system compiler supplies its ABI.
import subprocess
crate = root / 'libadalang_26.0.0_75276b8d'
env = subprocess.check_output(['alr', '-n', 'exec', '--', 'printenv', 'LD_LIBRARY_PATH'],
                              cwd=crate, text=True).strip()
if env:
    dirs.append(env)
(root / 'runtime.env').write_text('export LD_LIBRARY_PATH=' + shlex.quote(':'.join(dirs)) + '\n')
PY
. ./runtime.env
"$workspace/venv/bin/python" - <<'PY'
import libadalang as lal
ctx = lal.AnalysisContext()
unit = ctx.get_from_buffer('smoke.adb', b'procedure Smoke is X : Integer := 1; begin null; end Smoke;')
assert not unit.diagnostics
value = unit.root.findall(lal.IntLiteral)[0]
assert value.p_expression_type is not None
print('Python import/context/parse/semantic query passed:', lal.__file__)
PY
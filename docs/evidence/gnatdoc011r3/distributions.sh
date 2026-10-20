#!/bin/sh
set -eu
E=/home/zboll/qualification/gnatdoc011r3
R=/home/zboll/git/ada-gnatdoc-enhancer-011r3
export TMPDIR="$E/tmp"
cd "$R"
mkdir "$E/sdist-source" "$E/sdist-wheel"
tar -xzf dist/*.tar.gz -C "$E/sdist-source"
S=$(find "$E/sdist-source" -mindepth 1 -maxdepth 1 -type d)
"$E/py-3.13/bin/python" -m pip wheel --no-deps --no-build-isolation "$S" -w "$E/sdist-wheel" > "$E/sdist-rebuild.log" 2>&1
for v in 3.11 3.12 3.13; do
 for kind in wheel sdist; do
  V="$E/$kind-$v"
  python$v -m venv "$V"
  if test "$kind" = wheel; then W="$R/dist"; else W="$E/sdist-wheel"; fi
  "$V/bin/python" -m pip install --no-deps "$W"/*.whl > "$E/$kind-$v-install.log" 2>&1
  "$V/bin/python" -m pip install markdown-it-py==3.0.0 mdurl==0.1.2 >> "$E/$kind-$v-install.log" 2>&1
  cd "$E"
  if test "$kind" = wheel; then T="$R"; else T="$S"; fi
  "$V/bin/python" "$T/scripts/test_installed.py" --fixtures "$T/tests/fixtures" > "$E/$kind-$v-smoke.json" 2> "$E/$kind-$v-smoke.log"
  "$V/bin/python" -m unittest discover -s "$T/tests" -v > "$E/$kind-$v-tests.log" 2>&1
  "$V/bin/gnatdoc-enhancer" conformance --fixtures "$T/tests/fixtures" > "$E/$kind-$v-conformance.json"
  echo 0 > "$E/$kind-$v.exit"
 done
done
echo 0 > "$E/distributions.exit"
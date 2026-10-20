#!/bin/sh
set -eu
B=/tmp/gnatdoc012-candidate
S=$B/source
mkdir "$B/extracted" "$B/rebuilt"
tar -xzf "$B/artifacts/ada_gnatdoc_enhancer-0.1.0.tar.gz" -C "$B/extracted"
python3.12 -m pip wheel --no-deps --wheel-dir "$B/rebuilt" "$B/extracted/ada_gnatdoc_enhancer-0.1.0" > "$B/rebuild.log" 2>&1
python3.12 "$S/scripts/check_distributions.py" --source "$S" --wheel "$B"/artifacts/*.whl --sdist "$B"/artifacts/*.tar.gz --rebuilt "$B"/rebuilt/*.whl > "$B/content-audit.json"
for V in 3.11 3.12 3.13; do
  python$V -m venv "$B/wheel-$V"
  "$B/wheel-$V/bin/python" -m pip install --no-deps "$B"/artifacts/*.whl > "$B/wheel-$V-install.log" 2>&1
  "$B/wheel-$V/bin/python" -m pip install markdown-it-py==3.0.0 mdurl==0.1.2 >> "$B/wheel-$V-install.log" 2>&1
  python$V -m venv "$B/sdist-$V"
  "$B/sdist-$V/bin/python" -m pip install --no-deps "$B"/rebuilt/*.whl > "$B/sdist-$V-install.log" 2>&1
  "$B/sdist-$V/bin/python" -m pip install markdown-it-py==3.0.0 mdurl==0.1.2 >> "$B/sdist-$V-install.log" 2>&1
done
unset PYTHONPATH
cd /tmp
for V in 3.11 3.12 3.13; do
  (
    "$B/wheel-$V/bin/python" "$S/scripts/test_installed.py" --fixtures "$S/tests/fixtures" > "$B/wheel-$V-smoke.json" 2>&1
    "$B/wheel-$V/bin/python" -m unittest discover -s "$S/tests" -v > "$B/wheel-$V-tests.log" 2>&1
    echo $? > "$B/wheel-$V-tests.exit"
  ) &
  (
    E=$B/extracted/ada_gnatdoc_enhancer-0.1.0
    "$B/sdist-$V/bin/python" "$E/scripts/test_installed.py" --fixtures "$E/tests/fixtures" > "$B/sdist-$V-smoke.json" 2>&1
    "$B/sdist-$V/bin/python" -m unittest discover -s "$E/tests" -v > "$B/sdist-$V-tests.log" 2>&1
    echo $? > "$B/sdist-$V-tests.exit"
  ) &
done
wait
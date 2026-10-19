#!/usr/bin/env python3
"""Compare complete regenerated publications against a separately imported base.

Only reads retained inputs. Both implementations reconstruct the same pristine
native HTML/CSS and generate every output byte, including presentation.json.
Does not claim this byte comparison freshly acquires the retained consumers.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import MANIFEST, _presentation, expected_output
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json


def output(root, config, pristine):
    setting = load(root, config)
    # Compare every previously approved profile, including GNATDOC-011 symbol
    # navigation. Only the new incoming-reference opt-in is excluded here.
    assert not getattr(setting, 'instance_references', False)
    _, values, counts = expected_output(setting, pristine)
    originals = {p.relative_to(pristine).as_posix():p.read_text() for p in (pristine/'api').glob('*.html')}
    values[MANIFEST] = sorted_json(_presentation(setting, pristine, originals, values, counts)).encode()
    result = hashes(pristine)
    result.update({name:digest(data) for name,data in values.items()})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True,
                        help='JSON list: label, root, config, publication')
    parser.add_argument('--baseline-src', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args(); args.workspace.mkdir(exist_ok=False)
    report = {}
    for entry in json.loads(args.inputs.read_text()):
        root = Path(entry['root']); publication = Path(entry['publication'])
        pristine = args.workspace/entry['label']; (pristine/'api').mkdir(parents=True)
        manifest = json.loads((publication/MANIFEST).read_text())
        for name, text in manifest['original_api_html'].items():
            path = pristine/name; path.write_text(text)
        (pristine/'api/gnatdoc.css').write_bytes((publication/'api/gnatdoc.css').read_bytes())
        actual = output(root, entry['config'], pristine)
        environment = dict(os.environ, PYTHONPATH=str(args.baseline_src))
        program = ('import sys,json; from pathlib import Path; '
                   'sys.path.insert(0,'+repr(str(Path(__file__).resolve().parent))+'); '
                   'from compare_default_symbol_outputs import output; '
                   'print(json.dumps(output(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]))))')
        # The baseline Config predates symbol_bookmarks: execute the same
        # reconstruction with a compatibility-only getattr guard below.
        expected = json.loads(subprocess.check_output([sys.executable,'-c',program,str(root),
                              entry['config'],str(pristine)],env=environment,text=True))
        assert actual == expected, entry['label']+' default output changed'
        report[entry['label']] = {'byte_identical':True, 'files':len(actual), 'sha256':actual}
    (args.workspace/'parity.json').write_text(sorted_json(report))
    print({label:value['files'] for label,value in report.items()})


if __name__ == '__main__':main()
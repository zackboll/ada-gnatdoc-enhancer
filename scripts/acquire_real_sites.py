#!/usr/bin/env python3
"""Reproduce native-only GNATdoc acquisition in NEW, detached local clones.

Requires the reviewed consumer prerequisites: Alire 2.1.1, GNAT 16.1.0,
GPRbuild Alire release 26.0.1, native OpenCV and GNATdoc 26.0.0 (20260415).
No consumer enhancement/deploy script is executed. See the qualification guide.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

PINS={
    'core':('opencv_core_ada','c5545eee815431568495c6c76af83df56cf5c3dd'),
    'imgproc':('opencv_imgproc_ada','9ce22ae5ab70008e1147475a9e6d7baef82f1df0'),
    'geometry':('opencv_geometry_ada','fa81e5140cbebf2aa41397a40c08ba194a5f6f73'),
    'mel':('ams-gra-mel-bridge','6065129aba5dee89e70b61e05a9e1c9b2c3061c0'),
}
CORE_DEP='f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'
DEPENDENCIES={
    'core-0.4.1':('opencv_core_ada','386c5360ac51f2b62e522853d94290aec4ee14a0'),
    'core-0.5.0':('opencv_core_ada',CORE_DEP),
}

# Core 0.4.1 predates documentation projects. This acquisition-owned harness
# selects its actual public src directory and production compiler switches.
# It is tooling, not a substitute source revision; preserve its exact bytes.
DOCS_API='''with "config/opencv_core_config.gpr";
with "docs_internal.gpr";
project Docs_API is
   for Languages use ("Ada");
   for Source_Dirs use ("src");
   for Object_Dir use "obj/docs";
   package Compiler is
      for Default_Switches ("Ada") use OpenCV_Core_Config.Ada_Compiler_Switches;
   end Compiler;
   package Documentation is
      for Excluded_Project_Files use
        ("docs_internal.gpr", "config/opencv_core_config.gpr");
   end Documentation;
end Docs_API;
'''
DOCS_INTERNAL='''project Docs_Internal is
   for Languages use ("Ada");
   for Source_Dirs use ("src/internal");
   for Object_Dir use "obj/docs-internal";
end Docs_Internal;
'''


def command(argv,cwd,log,env=None):
    result=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,text=True)
    with log.open('a') as stream:
        stream.write(json.dumps(argv)+'\n'+result.stdout)
    if result.returncode:raise RuntimeError(f'command failed ({result.returncode}); see {log}')
    return result.stdout


def clone(repo,sha,target,log):
    command(['git','clone','--no-checkout',f'https://github.com/zackboll/{repo}.git',str(target)],
            target.parent,log)
    command(['git','checkout','--detach',sha],target,log)
    if command(['git','rev-parse','HEAD'],target,log).strip()!=sha:
        raise RuntimeError('unexpected source revision')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--gnatdoc',type=Path,required=True)
    parser.add_argument('--dependencies-only',action='store_true',
                        help='independently acquire both actual Core dependencies')
    args=parser.parse_args()
    base=args.workspace.absolute()
    if base.exists():raise ValueError('acquisition workspace must be new')
    base.mkdir(parents=True);log=base/'commands.log'
    version=subprocess.run([str(args.gnatdoc),'--version'],capture_output=True,text=True)
    if (version.stdout+version.stderr).strip()!='GNATdoc 26.0.0 (20260415)':
        raise ValueError('unqualified GNATdoc binary')
    if command(['alr','--version'],base,log).strip()!='alr 2.1.1':
        raise ValueError('unqualified Alire')
    settings=base/'settings';settings.mkdir()
    alr=['alr','-n','-s',str(settings)]
    command(alr+['--force','toolchain','--select','gnat_native=16.1.0','gprbuild=26.0.1'],base,log)
    if not args.dependencies_only:
        clone('opencv_core_ada',CORE_DEP,base/'core-dependency',log)
    for profile,(repo,sha) in (DEPENDENCIES if args.dependencies_only else PINS).items():
        directory=base/profile;directory.mkdir();source=directory/'source'
        clone(repo,sha,source,log)
        # Export the immutable tracked snapshot BEFORE Alire generates files.
        archive=directory/'snapshot.tar'
        command(['git','archive','--format=tar','-o',str(archive),sha],source,log)
        (directory/'snapshot').mkdir()
        command(['tar','-xf',str(archive),'-C',str(directory/'snapshot')],base,log)
        env=os.environ.copy()
        if profile=='mel':
            command(['python3','scripts/check_doc_source_integrity.py'],source,log)
            prefix=alr+['-C','docs/toolchain','exec','--']
            command(prefix+['sh','-c','cd ../.. && python3 scripts/gnatdoc_inventory.py '
                            '--source-list obj/docs/public-sources.txt --report obj/docs/inventory.json '
                            '&& gprbuild -p -P docs_api.gpr -u -c -gnatc'],source,log)
        else:
            if profile=='geometry':
                command(alr+['pin','opencv_core','--use='+str(base/'core-dependency')],source,log)
            command(alr+['build'],source,log)
            prefix=alr+['exec','--']
            if args.dependencies_only and not (source/'docs_api.gpr').exists():
                for name,text in (('docs_api.gpr',DOCS_API),('docs_internal.gpr',DOCS_INTERNAL)):
                    (source/name).write_text(text)
                    (directory/name).write_text(text)
            if profile in ('imgproc','geometry'):
                resolved=command(prefix+['printenv','OPENCV_CORE_ALIRE_PREFIX'],source,log).strip()
                expected=CORE_DEP if profile=='geometry' else '386c5360ac51f2b62e522853d94290aec4ee14a0'
                if profile=='geometry':
                    if command(['git','rev-parse','HEAD'],Path(resolved),log).strip()!=expected:
                        raise ValueError('unqualified Core dependency revision')
                else:
                    # Alire's indexed build cache is an export, not a Git
                    # checkout. Its resolved lock records the immutable origin.
                    lock=tomllib.loads((source/'alire/alire.lock').read_text())
                    origins=[x['release']['origin'] for x in lock['solution']['state']
                             if x['crate']=='opencv_core']
                    if len(origins)!=1 or origins[0].get('commit')!=expected:
                        raise ValueError('unqualified indexed Core dependency revision')
                    with log.open('a') as stream:stream.write(json.dumps(origins[0])+'\n')
        tool_command=['sh','-c',('cd ../.. && ' if profile=='mel' else '')+
                      'gnat --version && gprbuild --version']
        versions=command(prefix+tool_command,source,log)
        if not re.search(r'^GNAT 16\.1\.0$',versions,re.M) or 'GPRBUILD 26.0.0 (2026-04-15)' not in versions:
            raise ValueError('unqualified compiler/project tools')
        (directory/'versions.txt').write_text(versions)
        for path in ('obj/docs','obj/docs-internal'):(source/path).mkdir(parents=True,exist_ok=True)
        native=[str(args.gnatdoc.absolute()),'-P','docs_api.gpr','--backend','html',
                '--generate','public','--style','trailing' if profile=='mel' else 'leading',
                '--warnings','-O',str(directory/'pristine/api')]
        if profile=='mel':
            # Alire -C changes the executable's working directory.
            import shlex
            native=['sh','-c','cd ../.. && '+shlex.join(native)]
        diagnostics=command(prefix+native,source,log,env)
        (directory/'gnatdoc.log').write_text(diagnostics)
        if re.search(r'(^|\s)(error:|fatal:|ignore file due to)',diagnostics,re.I):
            raise ValueError('incomplete native generation')
        if args.dependencies_only:
            print(profile,sha,'native output captured; no consumer presentation executed',flush=True)
            continue
        ratchet=['python3','scripts/compare_gnatdoc_warnings.py']
        if profile!='core':ratchet+=['--fail-on-removed']
        command(ratchet+['docs/gnatdoc-warning-baseline.txt',str(directory/'gnatdoc.log')],source,log)
        if profile in ('imgproc','geometry'):
            command(['python3','scripts/check_doc_coverage.py','--fail-on-removed',
                     'docs/gnatdoc-coverage-baseline.txt',str(directory/'pristine')],source,log)
        elif profile=='mel':
            command(['python3','scripts/check_doc_coverage.py',str(directory/'pristine'),
                     '--report',str(directory/'coverage.json')],source,log)
        print(profile,sha,'native output captured; consumer presentation NOT executed')


if __name__=='__main__':main()
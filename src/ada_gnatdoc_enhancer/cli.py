"""Command-line interface for already-generated, project-qualified GNATdoc HTML."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import load
from .coverage import report as coverage_report
from .errors import EnhancementError
from .inventory import packages
from .native_html import snapshot
from .pipeline import enhance, verify
from .util import sorted_json
from .warnings import compare, identities


def parser():
    p=argparse.ArgumentParser(prog='gnatdoc-enhancer', description=__doc__)
    p.add_argument('--version', action='version', version=__version__)
    subs=p.add_subparsers(dest='command',required=True)
    for command in ('inventory','enhance','verify','warnings','coverage'):
        sub=subs.add_parser(command)
        sub.add_argument('--config',required=True,help='TOML file relative to project root')
        sub.add_argument('--source-root',default='.',type=Path)
        sub.add_argument('--site',default='_site',type=Path)
        if command=='enhance':sub.add_argument('--dry-run',action='store_true')
        if command=='warnings':
            sub.add_argument('--log',required=True,type=Path)
            sub.add_argument('--baseline',required=True,type=Path)
            sub.add_argument('--allow-removed',action='store_true')
    con=subs.add_parser('conformance',help='offline four-profile fixture qualification')
    con.add_argument('--fixtures',default=None,type=Path)
    return p


def run(args):
    if args.command=='conformance':
        from .conformance import run
        return run(args.fixtures)
    root=args.source_root.resolve();config=load(root,args.config)
    site=args.site if args.site.is_absolute() else root/args.site
    if args.command=='enhance':return enhance(config,site,dry_run=args.dry_run)
    if args.command=='verify':return verify(config,site)
    if args.command=='inventory':
        from .pipeline import MANIFEST
        # For enhanced output, inspect the trusted captured raw native source.
        if (site/MANIFEST).exists():
            from .pipeline import verify as do_verify
            verified=do_verify(config,site)
            return {'project':config.project,'status':verified,'public_packages':sorted(x.name for x in packages(config).values())}
        native=snapshot(config,site)
        return {'project':config.project,'public_packages':sorted(p.package for p in native.pages.values()),
                'native_declaration_sections':sum(len(p.sections) for p in native.pages.values())}
    if args.command=='warnings':
        actual=identities(args.log.read_text(),packages(config))
        baseline=args.baseline.read_text().splitlines()
        return compare(actual,baseline,not args.allow_removed)
    if args.command=='coverage':
        from .pipeline import MANIFEST
        if (site/MANIFEST).exists():
            # The summary must refer to raw native sources, so reconstruct in
            # the validator and return an explicit not-yet-full-parity status.
            verify(config,site)
            return {'status':'verified enhanced presentation',
                    'coverage':'use consuming repository full coverage ratchet'}
        return coverage_report(packages(config),snapshot(config,site),
                               comment_style=config.source_style,
                               renderer_exceptions=config.renderer_exceptions)
    raise EnhancementError('unsupported command')


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        result=run(args)
        print(sorted_json(result),end='')
        return 0
    except (EnhancementError,ValueError,FileNotFoundError,UnicodeError,OSError,KeyError) as exc:
        print(f'gnatdoc-enhancer: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())

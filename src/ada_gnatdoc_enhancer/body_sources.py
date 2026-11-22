"""Schema-2 source ownership, discovered without publication metadata."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .body_inventory import package_header, parse_unit, Unit
from .source_view import owned
from .util import digest, inside, require


MODE = 'public-specifications-and-bodies'
SOURCE_PATH = re.compile(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z')


def path_name(root, name):
    require(isinstance(name, str) and SOURCE_PATH.fullmatch(name) and
            all(p not in ('.', '..') for p in name.split('/')), 'unsafe body-mode source path')
    return inside(root, name)


@dataclass(frozen=True)
class Body:
    name: str
    raw: bytes
    unit: Unit


def inventory(config, sources):
    """Bind all eligible bodies, not an output- or manifest-selected subset.

    A configured source directory is one ownership domain. Overlapping domains
    are rejected, as is a public body found outside its specification's domain.
    """
    directories = sorted(path_name(config.root, d) for d in config.sources)
    require(len({str(d).casefold() for d in directories}) == len(directories) and not any(
        d.is_relative_to(parent) for i, d in enumerate(directories) for parent in directories[:i]),
        'overlapping or case-colliding body-mode source directories')
    specs = {}; owners = {}; seen = set(); units = {}; bodies = {}
    for directory in directories:
        require(directory.is_dir() and all(not p.is_symlink() for p in (directory, *directory.parents)),
                'missing or symlink source-view directory')
        for p in sorted(directory.rglob('*')):
            require(not p.is_symlink(), 'symlink in source-view directory')
            if p.suffix.lower() not in ('.ads', '.adb') or p.is_dir():
                continue
            name = p.relative_to(config.root).as_posix()
            path_name(config.root, name)
            require(name.casefold() not in seen and p.suffix in ('.ads', '.adb'),
                    'unsupported or case-colliding Ada source path')
            seen.add(name.casefold())
    for key, pkg in sorted(sources.items()):
        name = pkg.path.relative_to(config.root).as_posix()
        require(name.casefold() in seen and pkg.path.suffix == '.ads', 'unsupported specification ownership')
        owners[key] = next(d for d in directories if pkg.path.is_relative_to(d))
        raw = owned(config.root, name).read_bytes()
        require(raw.decode('utf-8').replace('\r\n', '\n') == pkg.source,
                'source changed while constructing source view')
        specs[name] = dict(package=pkg.name, sha256=digest(raw))
        units[key] = parse_unit(pkg.source, body=False)
        if units[key] is not None:
            require(units[key].name == key, 'conflicting specification library identity')
    for directory in directories:
        for p in sorted(directory.rglob('*.adb')):
            if p.is_dir():
                continue
            name = p.relative_to(config.root).as_posix()
            raw = owned(config.root, name).read_bytes()
            text = raw.decode('utf-8')
            key = package_header(text, body=True)
            if key not in sources:
                continue
            # The legacy specification inventory also accepts certain generic
            # units and renamings. They do not establish ordinary body ownership.
            if package_header(sources[key].source, body=False) != key:
                continue
            require(owners[key] == directory, 'package body/specification directory ownership conflict')
            require(key not in bodies, 'duplicate Ada package body identity: ' + key)
            unit = parse_unit(text, body=True)
            require(unit is not None and unit.name == key, 'unsupported package body boundary: ' + name)
            bodies[key] = Body(name, raw, unit)
    return specs, bodies, units


def body_evidence(sources, bodies):
    return {body.name: dict(package=sources[key].name, sha256=digest(body.raw))
            for key, body in bodies.items()}
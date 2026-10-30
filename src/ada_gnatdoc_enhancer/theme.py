"""Qualified GNATdoc 26 metadata and bundled or source-approved theme bytes."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from .errors import EnhancementError
from .util import digest, inside, regular, require

NATIVE_LINK = '<link rel=stylesheet href=gnatdoc.css>'
METADATA = ('<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<link rel="stylesheet" href="gnatdoc-theme.css">')


def themed(original: str, enabled: bool=True) -> str:
    if not enabled:return original
    require(original.count(NATIVE_LINK)==1, "unknown GNATdoc stylesheet insertion point")
    require('gnatdoc-theme.css' not in original and '<meta name="viewport"' not in original,
            "unexpected preexisting theme/viewport")
    return original.replace(NATIVE_LINK,NATIVE_LINK+METADATA,1)


def asset(name: str) -> bytes:
    require(name in {'gnatdoc-theme.css','gnatdoc-guides.css','gnatdoc-navigation.js',
                     'gnatdoc-symbol-navigation.js','gnatdoc-instance-navigation.js',
                     'gnatdoc-search.js','gnatdoc-search.css'},
            "unapproved bundled asset")
    return files('ada_gnatdoc_enhancer').joinpath('assets',name).read_bytes()


def source_bytes(config, name):
    """Check lexical ancestors before reading; never authorize through a symlink."""
    require(isinstance(name, str) and ':' not in name and
            name == Path(name).as_posix(),
            'noncanonical custom theme source/configuration path')
    path = inside(config.root, name)
    require(all(not p.is_symlink() for p in (path, *path.parents)),
            'symlink custom theme source/configuration')
    return regular(path).read_bytes()


def theme_identity(config):
    """Input identity only; output metadata is never the approval authority."""
    if config.theme_css_source is None and config.theme_css_sha256 is None:
        return None
    import re
    require(config.theme and isinstance(config.theme_css_source, str) and
            isinstance(config.theme_css_sha256, str) and
            re.fullmatch('[a-f0-9]{64}', config.theme_css_sha256),
            'custom theme requires enabled theme, source and SHA-256')
    require(isinstance(config.theme_config_path, str) and
            isinstance(config.theme_config_sha256, str) and
            re.fullmatch('[a-f0-9]{64}', config.theme_config_sha256),
            'custom theme requires loaded configuration identity')
    payload = source_bytes(config, config.theme_config_path)
    require(digest(payload) == config.theme_config_sha256,
            'custom theme configuration changed after loading')
    import tomllib
    presentation = tomllib.loads(payload.decode('utf-8')).get('presentation', {})
    require(presentation.get('theme', True) is True and
            presentation.get('theme_css_source') == config.theme_css_source and
            presentation.get('theme_css_sha256') == config.theme_css_sha256,
            'custom theme differs from approved configuration')
    return {'source': config.theme_css_source, 'sha256': config.theme_css_sha256,
            'config': config.theme_config_path, 'config_sha256': config.theme_config_sha256}


def theme_asset(config):
    identity = theme_identity(config)
    if identity is None:
        return asset('gnatdoc-theme.css')
    content = source_bytes(config, identity['source'])
    require(digest(content) == identity['sha256'], 'custom theme CSS source hash mismatch')
    from .validation import css_safe
    css_safe(content)
    return content

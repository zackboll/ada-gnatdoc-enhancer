"""Strict project-owned TOML configuration; output metadata cannot add permissions."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import EnhancementError
from .util import inside, regular, require

TOP = frozenset({"schema_version", "project", "gnatdoc", "sources", "navigation", "presentation", "guides", "security", "external_types", "external_dependencies", "external_symbol_bookmarks", "renderer_exceptions", "generic_instances"})


def members(data, allowed, at):
    require(isinstance(data, dict), f"{at} must be a table")
    extra = data.keys() - set(allowed)
    require(not extra, f"unsupported {at} keys: {sorted(extra)}")


def words(value, at):
    require(isinstance(value, list) and all(isinstance(x, str) and bool(x.strip()) for x in value),
            f"{at} must be nonempty strings in an array")
    require(len(set(value)) == len(value), f"duplicate {at} entries")
    return tuple(value)


@dataclass(frozen=True)
class Config:
    root: Path
    project: str
    gnatdoc: str
    sources: tuple[str, ...]
    expected_packages: tuple[str, ...] = ()
    source_style: str = "leading"
    navigation: str = "packages"
    category_file: str | None = None
    theme: bool = True
    highlight: bool = True
    type_links: bool = True
    guides: str = "none"
    guide_manifest: str | None = None
    externals: dict[str, str] = field(default_factory=dict)
    allowed_hosts: frozenset[str] = frozenset()
    renderer_exceptions: tuple[str, ...] = ()
    dependencies: tuple[dict, ...] = ()
    generic_instances: dict = field(default_factory=dict)
    guide_sha256: str | None = None
    symbol_bookmarks: bool = False
    default_package: str | None = None
    instance_references: bool = False
    external_type_target: str | None = None
    theme_css_source: str | None = None
    theme_css_sha256: str | None = None
    theme_config_path: str | None = None
    theme_config_sha256: str | None = None
    external_symbol_bookmarks: dict = field(default_factory=dict)


def load(root: Path, path: str) -> Config:
    lexical_root = root.absolute()
    root = root.resolve()
    config_path = regular(inside(root, path))
    config_bytes = config_path.read_bytes()
    raw = tomllib.loads(config_bytes.decode('utf-8'))
    members(raw, TOP, "root")
    require(raw.get("schema_version") == 1, "unsupported configuration schema version")
    project = raw.get("project")
    require(isinstance(project, str) and bool(project.strip()), "project must be a nonempty string")
    gd = raw.get("gnatdoc", {})
    members(gd, {"version"}, "gnatdoc")
    version = gd.get("version", "26.0.0")
    require(version == "26.0.0", f"unsupported GNATdoc HTML version: {version}")
    src = raw.get("sources", {})
    members(src, {"directories", "packages", "comment_style"}, "sources")
    names = words(src.get("directories", ["src"]), "source directories")
    require(bool(names), "at least one source directory required")
    for name in names:
        path = inside(root, name)
        require(path.is_dir() and not path.is_symlink(), f"missing source directory: {name}")
    packages = words(src.get("packages", []), "expected packages")
    style = src.get("comment_style", "leading")
    require(style in ("leading", "trailing"), "comment_style must be leading or trailing")
    nav = raw.get("navigation", {})
    members(nav, {"mode", "categories", "symbol_bookmarks", "default_package"}, "navigation")
    mode = nav.get("mode", "packages")
    require(mode in ("packages", "operations", "none"), "invalid navigation mode")
    categories = nav.get("categories")
    symbols = nav.get('symbol_bookmarks', False)
    default_package = nav.get('default_package')
    require(type(symbols) is bool, 'navigation.symbol_bookmarks must be Boolean')
    if symbols:
        from .util import QNAME
        import re
        require(mode == 'packages' and categories is None,
                'symbol bookmarks require uncategorized package navigation')
        require(isinstance(default_package, str) and
                re.fullmatch(QNAME, default_package) is not None,
                'symbol bookmarks require a default_package Ada identity')
    else:
        require(default_package is None, 'default_package requires symbol_bookmarks')
    if categories is not None:
        regular(inside(root, categories))
    pres = raw.get("presentation", {})
    members(pres, {"theme", "syntax_highlighting", "type_links", "external_type_target",
                   "theme_css_source", "theme_css_sha256"}, "presentation")
    for k in pres.keys() - {"external_type_target", "theme_css_source", "theme_css_sha256"}:
        require(type(pres[k]) is bool, f"presentation.{k} must be Boolean")
    custom_theme = bool({'theme_css_source', 'theme_css_sha256'} & pres.keys())
    if custom_theme:
        import re
        require(all(not p.is_symlink() for p in (lexical_root, *lexical_root.parents)),
                'symlink custom theme source root')
        require({'theme_css_source', 'theme_css_sha256'} <= pres.keys(),
                'theme CSS source and SHA-256 must be configured together')
        require(pres.get('theme', True), 'custom theme CSS requires theme = true')
        regular(inside(root, pres['theme_css_source']))
        require(isinstance(pres['theme_css_sha256'], str) and
                re.fullmatch('[a-f0-9]{64}', pres['theme_css_sha256']),
                'custom theme CSS requires a lower-case SHA-256')
    external_target = pres.get('external_type_target')
    require(external_target is None or external_target == '_top',
            'presentation.external_type_target must be "_top" when specified')
    guide = raw.get("guides", {})
    members(guide, {"mode", "manifest", "sha256"}, "guides")
    guide_mode = guide.get("mode", "none")
    require(guide_mode in ("none", "html", "markdown", "authored-html", "authored-markdown"), "invalid guide mode")
    guide_manifest = guide.get("manifest")
    if guide_mode != "none":
        require(isinstance(guide_manifest, str), "guide manifest required")
        regular(inside(root, guide_manifest))
    else:
        require(guide_manifest is None, "guide manifest requires a guide mode")
    guide_hash = guide.get('sha256')
    import re
    if guide_mode.startswith('authored-'):
        require(isinstance(guide_hash, str) and re.fullmatch('[a-f0-9]{64}', guide_hash),
                'authored guide manifest requires SHA-256')
    else:
        require(guide_hash is None, 'guide SHA-256 requires authored mode')
    sec = raw.get("security", {})
    members(sec, {"external_hosts"}, "security")
    hosts = words(sec.get("external_hosts", []), "external hosts")
    for host in hosts:
        require(host and host.lower() == host and "/" not in host and ":" not in host,
                "external host must be an exact lower-case hostname")
    ext = raw.get("external_types", {})
    members(ext, ext, "external_types")
    require(len({k.lower() for k in ext})==len(ext),'duplicate case-insensitive external types')
    for name, url in ext.items():
        require(isinstance(url, str) and url.startswith("https://") and "#" in url,
                f"external type {name} requires explicit HTTPS page and anchor")
        from urllib.parse import urlsplit
        u = urlsplit(url)
        require(u.hostname in hosts and u.hostname == u.netloc and bool(u.fragment) and not u.query,
                f"external type target is not allowlisted: {name}")
    exceptions = words(raw.get("renderer_exceptions", []), "renderer exceptions")
    for ex in exceptions:
        require(ex == "AMS.MEL.IR.Health_Status.Metadata.Status", "unsupported renderer exception")
    dependencies=raw.get('external_dependencies',[])
    require(isinstance(dependencies,list),'external_dependencies must be an array of tables')
    fields={'repository','revision','manifest','manifest_sha256','acquisition',
            'acquisition_sha256','source','site','base_url','publication','types'}
    import re
    for dep in dependencies:
        members(dep,fields,'external dependency')
        require(set(dep)==fields,'incomplete external dependency')
        require(all(isinstance(v,str) for k,v in dep.items() if k!='types'),
                'external dependency fields must be strings')
        require(re.fullmatch('[a-f0-9]{40}',dep['revision']),'invalid expected dependency SHA')
        for key in ('manifest_sha256','acquisition_sha256'):
            require(re.fullmatch('[a-f0-9]{64}',dep[key]),'invalid external evidence hash')
        types=words(dep['types'],'external dependency types')
        require(types and len({t.lower() for t in types})==len(types),
                'duplicate case-insensitive dependency types')
        for key in ('manifest','acquisition','source','site'):
            inside(root,dep[key])
    generic = raw.get('generic_instances', {})
    members(generic, {'qualification', 'sha256', 'incoming_references'}, 'generic_instances')
    incoming = generic.get('incoming_references', False)
    require(type(incoming) is bool, 'generic incoming_references must be Boolean')
    if generic:
        require({'qualification', 'sha256'} <= set(generic), 'incomplete generic instance qualification')
        require(isinstance(generic['qualification'], str), 'generic qualification must be a path')
        regular(inside(root, generic['qualification']))
        require(isinstance(generic['sha256'], str) and re.fullmatch('[a-f0-9]{64}', generic['sha256']),
                'invalid generic qualification SHA-256')
    require(not incoming or (mode == 'packages' and symbols and pres.get('type_links', True)),
            'incoming instance references require type links and symbol package navigation')
    bookmarks = raw.get('external_symbol_bookmarks', {})
    if 'external_symbol_bookmarks' in raw:
        members(bookmarks, {'qualification', 'sha256', 'types'}, 'external_symbol_bookmarks')
        require(set(bookmarks) == {'qualification', 'sha256', 'types'},
                'incomplete external symbol bookmark qualification')
        regular(inside(root, bookmarks['qualification']))
        require(isinstance(bookmarks['sha256'], str) and
                re.fullmatch('[a-f0-9]{64}', bookmarks['sha256']),
                'invalid external symbol bookmark SHA-256')
        selected = words(bookmarks['types'], 'external symbol bookmark types')
        require(selected and len({n.lower() for n in selected}) == len(selected),
                'empty/duplicate external symbol bookmark types')
        require(external_target == '_top', 'external symbol bookmarks require external_type_target = "_top"')
    from .util import digest
    config = Config(root, project, version, names, packages, style, mode, categories,
                  pres.get("theme", True), pres.get("syntax_highlighting", True),
                  pres.get("type_links", True), guide_mode, guide_manifest,
                  ext, frozenset(hosts), exceptions, tuple(dependencies), generic, guide_hash,
                  symbols, default_package, incoming, external_target,
                  pres.get('theme_css_source'), pres.get('theme_css_sha256'),
                  config_path.relative_to(root).as_posix() if custom_theme else None,
                  digest(config_bytes) if custom_theme else None, bookmarks)
    if custom_theme:
        from .theme import theme_asset
        theme_asset(config)
    return config

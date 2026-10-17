"""Constrained, source-owned Vector/Matrix presentation, never native expansion.

Only complete, flat instantiations of two demonstrated templates are supported.
The project-owned, hash-bound qualification record is an external input, not an
output manifest. Every run rechecks source, original native bytes, grammar and
destinations. No destination filename or fragment is computed from an Ada name.
"""
from __future__ import annotations

import html
import json
import re

from .inventory import HEADER, mask_ada, normalized
from .native_html import verified_types
from .util import IDENT, QNAME, digest, inside, regular, require
from .validation import Page

VECTORS = 'opencv.core.vectors'
MATRICES = 'opencv.core.fixed_matrices'
FORMALS = {VECTORS: ('Length',), MATRICES: ('Row_Count', 'Column_Count')}
MEMBERS = {
    VECTORS: {
        'Component_Index': 'subtype Component_Index is Natural range 0 .. Length - 1;',
        'Vector': 'type Vector is array (Component_Index) of Element_Type;',
    },
    MATRICES: {
        'Row_Index': 'subtype Row_Index is Natural range 0 .. Row_Count - 1;',
        'Column_Index': 'subtype Column_Index is Natural range 0 .. Column_Count - 1;',
        'Matrix': 'type Matrix is array (Row_Index, Column_Index) of Element_Type;',
    },
}
ELEMENTS = {
    'UInt8_Value': ('opencv', 'subtype UInt8_Value is Interfaces.Unsigned_8;'),
    'Int8_Value': ('opencv', 'subtype Int8_Value is Interfaces.Integer_8;'),
    'UInt16_Value': ('opencv', 'subtype UInt16_Value is Interfaces.Unsigned_16;'),
    'Int16_Value': ('opencv', 'subtype Int16_Value is Interfaces.Integer_16;'),
    'Int32_Value': ('opencv', 'subtype Int32_Value is Interfaces.Integer_32;'),
    'Float16_Value': ('opencv.core', 'type Float16_Value is private;'),
    'Float32_Value': ('opencv', 'subtype Float32_Value is Interfaces.IEEE_Float_32;'),
    'Float64_Value': ('opencv', 'subtype Float64_Value is Interfaces.IEEE_Float_64;'),
}
CONVERSIONS = 'opencv.core.float32_matx3x3_conversions'
ANCHOR = 'instance-members-summary'
CLASS = 'generic-instance-summary'
PREFIX = ('<!DOCTYPE html>\n<html class=main>\n'
          '<link rel=stylesheet href=gnatdoc.css><body class=content>')


def title(package):
    return package.name


def native_instance(package):
    """Reconstruct only the qualified GNATdoc 26 plain-comment empty layout.

    Introductory p tags are deliberately unclosed in the native serialization.
    Inserting BEFORE Description cannot nest our section inside one of them.
    """
    lines = package.source.splitlines()
    header = HEADER.search(mask_ada(package.source))
    require(header is not None, 'missing instance header')
    declaration = package.source.count('\n', 0, header.start(2))
    intro = []
    i = declaration - 1
    while i >= 0 and (lines[i].lstrip().startswith('--') or not lines[i].strip()):
        intro.append(re.sub(r'^\s*--\s?', '', lines[i]))
        i -= 1
    text = '\n'.join(reversed(intro)).strip()
    require(text and not re.search(r'[<>&@]', text),
            f'unsupported instance introduction: {package.name}')
    paragraphs = [' '.join(p.split()) for p in re.split(r'\n\s*\n', text)]
    return (PREFIX + '<h1>' + html.escape(package.name) + '</h1><h2>Entities</h2>'
            '<h2>Description</h2>' + ''.join('<p>' + p for p in paragraphs))


def ancestor_visibility(package, owner, element, source):
    scope = package.rpartition('.')[0]
    while scope:
        require(scope in source, f'missing ancestor scope: {scope}')
        ancestor = source[scope]
        code = mask_ada(ancestor.source)
        header = HEADER.search(code)
        require(header and not header[1] and header[3].lower() == 'is',
                f'unsupported ancestor header: {scope}')
        require(not re.search(r'\b(generic|renames|use)\b', code, re.I) and
                not re.search(r'\b(package|task|protected|begin|declare)\b', code[header.end():], re.I),
                f'unsupported ancestor visibility: {scope}')
        if scope == owner:
            require(element.lower() in ancestor.public_types,
                    f'actual type not public in owner: {scope}.{element}')
            return
        # Include private parts, objects, subprograms and prefix aliases, not
        # just the public type inventory. Decline even potential private blockers.
        require(not re.search(r'\b(?:type|subtype|function|procedure|package)\s+' + re.escape(element) +
                              r'\b|(?:^|;)\s*(?:'+IDENT+r'\s*,\s*)*' + re.escape(element) +
                              r'\s*(?:[:,])', code[header.end():], re.I),
                f'potentially shadowing ancestor declaration: {scope}.{element}')
        scope = scope.rpartition('.')[0]
    require(False, f'actual owner not ancestor-visible: {package}')


def discover(source, expected):
    """Consume complete declarations; expected identities are never filenames."""
    result = {}; unsupported = []
    for key, package in sorted(source.items()):
        code = re.sub(r'(?<=\w) \. (?=[a-z])', '.', normalized(package.source))
        is_instance = re.search(r'\bpackage\s+' + QNAME + r'\s+is\s+new\b', code)
        mentions = any(t in code for t in FORMALS)
        if key not in expected and not (is_instance and mentions):
            if is_instance: unsupported.append(package.name)
            continue
        match = re.fullmatch(r'with (' + QNAME + r') ; package (' + QNAME +
                             r') is new (' + QNAME + r') \( (.*?) \) ;', code)
        require(match is not None, f'unsupported complete generic instantiation/context: {package.name}')
        imported, identity, template, arguments = match.groups()
        require(identity == key and imported == template and template in FORMALS,
                f'unknown/unimported generic template: {package.name}')
        associations = {}
        for part in arguments.split(','):
            assoc = re.fullmatch(r'\s*(' + IDENT + r') => (' + IDENT + r'|[1-9][0-9]*)\s*', part)
            require(assoc is not None, f'unsupported generic association: {package.name}')
            formal, actual = assoc.groups()
            require(formal not in associations, f'duplicate actual association: {package.name}')
            associations[formal] = actual
        require(set(associations) == {'element_type', *(f.lower() for f in FORMALS[template])},
                f'missing/unknown generic formal: {package.name}')
        candidates = [e for e in ELEMENTS if e.lower() == associations['element_type']]
        require(len(candidates) == 1, f'unsupported actual element type: {package.name}')
        element = candidates[0]; owner, signature = ELEMENTS[element]
        require(owner in source, f'missing actual element owner: {owner}')
        declaration = source[owner].public_types.get(element.lower())
        require(declaration and normalized(declaration.signature) == normalized(signature),
                f'changed actual type identity: {owner}.{element}')
        ancestor_visibility(key, owner, element, source)
        dimensions = []
        for formal in FORMALS[template]:
            actual = associations[formal.lower()]
            require(re.fullmatch('[1-9][0-9]*', actual), f'non-positive/nonliteral dimension: {package.name}')
            dimensions.append(int(actual))
        result[key] = {'package': package.name, 'template': template, 'element_type': element,
                       'element_owner': owner, 'dimensions': dimensions}
    require(set(result) == set(expected), 'generic instance inventory mismatch (missing/additional instances)')
    for template in {v['template'] for v in result.values()}:
        require(template in source, f'missing generic template source: {template}')
        package = source[template]
        complete = ('generic type Element_Type is private; ' +
                    ' '.join(f'{f} : Positive;' for f in FORMALS[template]) +
                    f' package {package.name} is ' + ' '.join(MEMBERS[template].values()) +
                    f' end {package.name};')
        require(normalized(package.source) == normalized(complete),
                f'altered/unsupported generic template declarations: {template}')
    for key, item in result.items():
        require(item == expected[key], f'qualified instance associations changed: {key}')
    return result, unsupported


def qualification(config, source, native):
    setting = config.generic_instances
    payload = regular(inside(config.root, setting['qualification'])).read_bytes()
    require(digest(payload) == setting['sha256'], 'generic qualification hash mismatch')
    record = json.loads(payload)
    require(isinstance(record, dict) and set(record) ==
            {'schema_version', 'instances', 'source_sha256', 'native_sha256'},
            'unsupported generic qualification record')
    require(record['schema_version'] == 1 and isinstance(record['instances'], dict) and record['instances'],
            'empty/invalid generic qualification inventory')
    current = {p.path.relative_to(config.root).as_posix(): digest(p.path.read_bytes()) for p in source.values()}
    require(record['source_sha256'] == current, 'generic qualified source hashes/inventory changed')
    current = {'api/' + p.path.name: digest(p.original.encode()) for p in native.pages.values()}
    current.update({'api/index.html': digest(native.index.encode()),
                    'api/gnatdoc.css': digest(native.original_css)})
    require(record['native_sha256'] == current, 'generic pristine native hashes/inventory changed')
    return discover(source, record['instances'])


def render(item, source, native, targets):
    template = item['template']; element = item['element_type']; dimensions = item['dimensions']
    require(template in native.pages, f'missing native template package: {template}')
    def link(destination, label):
        return '<a href="' + html.escape(destination, quote=True) + '">' + html.escape(label) + '</a>'
    def member(identity, label):
        require(identity in targets, f'missing genuine declaration anchor: {identity}')
        path, anchor = targets[identity]
        return link(path.name + '#' + anchor, label)
    args = [('Element_Type', member(item['element_owner'] + '.' + element.lower(),
                                   source[item['element_owner']].name + '.' + element))]
    args += list(zip(FORMALS[template], map(str, dimensions)))
    if template == VECTORS:
        length, = dimensions
        meanings = [f'Natural range 0 .. {length - 1}',
                    f'Array of {length} {element} components, indexed by Component_Index']
    else:
        rows, columns = dimensions
        meanings = [f'Natural range 0 .. {rows - 1}', f'Natural range 0 .. {columns - 1}',
                    f'{rows} × {columns} array of {element} elements, indexed by (Row_Index, Column_Index)']
    member_rows = ''.join('<tr><th scope="row">' + member(template + '.' + name.lower(), name) +
                          '</th><td>' + html.escape(meaning) + '</td></tr>'
                          for name, meaning in zip(MEMBERS[template], meanings))
    result = ('<section class="' + CLASS + '" id="' + ANCHOR + '"><h2>Instantiated Members</h2>'
              '<p>Explanatory instantiated equivalents, not additional source declarations.</p>'
              '<p>Instance: ' + html.escape(item['package']) + '</p><p>Generic template: ' +
              link(native.pages[template].path.name, source[template].name) + '</p>'
              '<h3>Actual generic arguments</h3><table><thead><tr><th scope="col">Formal</th>'
              '<th scope="col">Actual</th></tr></thead><tbody>' +
              ''.join('<tr><th scope="row">' + f + '</th><td>' + a + '</td></tr>' for f, a in args) +
              '</tbody></table><h3>Instantiated members</h3>'
              '<p>Member links lead to the generic template declarations, not native instance-member declarations.</p>'
              '<table><thead><tr><th scope="col">Member</th><th scope="col">Meaning</th></tr></thead><tbody>' +
              member_rows + '</tbody></table>'
              '<p>This is an ordinary Ada array, not a cv::Mat. Assignment follows Ada value semantics '
              'for the actual element type; this generic introduces no native handle. '
              'Ada array assignment is distinct from OpenCV Mat storage ownership.</p>')
    if template == VECTORS:
        result += ('<p>With the corresponding typed OpenCV APIs, each vector value represents one '
                   'complete multi-channel element. Component indices specify channel positions, '
                   'not semantic channel names.</p>')
    else:
        require(item['package'].lower() == 'opencv.core.float32_matx3x3' and dimensions == [3, 3]
                and element == 'Float32_Value', 'unsupported matrix conversion relationship')
        require(CONVERSIONS in native.pages and CONVERSIONS in source, 'missing separate matrix conversion package')
        signatures = ('function To_Mat (Value : OpenCV.Core.Float32_Matx3x3.Matrix) return Mat;',
                      'function To_Matx3x3 (Image : Mat) return OpenCV.Core.Float32_Matx3x3.Matrix;')
        require(all(sum(normalized(d.signature) == normalized(s) for d in source[CONVERSIONS].declarations) == 1
                    for s in signatures), 'unverified matrix conversion declarations')
        result += ('<p>The separate ' + link(native.pages[CONVERSIONS].path.name, source[CONVERSIONS].name) +
                   ' package copies between this array and Mat storage; it does not imply shared native storage.</p>')
    if element == 'Float16_Value':
        result += ('<p>Float16_Value stores exact IEEE-754 binary16 encodings. Stored representation '
                   'and numerical interpretation are distinct; numeric conversion uses To_Float32/To_Float16.</p>')
    # Native GNATdoc pages omit a charset. Character references are deterministic
    # and render correctly even when an HTTP server supplies no UTF-8 header.
    return (result + '</section>').encode('ascii', 'xmlcharrefreplace').decode('ascii')


def summaries(config, source, native):
    """Return exact authorized sections and separate, observed link accounting."""
    if not config.generic_instances: return {}, {}
    instances, unsupported = qualification(config, source, native)
    targets = verified_types(native, source)
    sections = {}; links = 0; vectors = 0; matrices = 0
    link_kinds = {'generic_template_links': 0, 'generic_member_links': 0,
                  'generic_actual_type_links': 0, 'generic_conversion_package_links': 0}
    for key, item in sorted(instances.items()):
        page = native.pages[key]
        require(not page.sections and '<h4' not in page.original, f'unexpected native instance members: {key}')
        require(page.original == native_instance(source[key]) and
                page.original.count('<h2>Description</h2>') == 1 and CLASS not in page.original,
                f'unsupported instance page shape/introduction/insertion: {key}')
        section = render(item, source, native, targets)
        parsed = Page(section)
        require(not parsed.issues and parsed.ids == [ANCHOR], 'unsafe generic summary presentation')
        def target_url(identity):
            path, anchor = targets[identity]
            return path.name + '#' + anchor
        destinations = {
            'generic_template_links': {native.pages[item['template']].path.name},
            'generic_member_links': {target_url(item['template']+'.'+m.lower()) for m in MEMBERS[item['template']]},
            'generic_actual_type_links': {target_url(item['element_owner']+'.'+item['element_type'].lower())},
            'generic_conversion_package_links': ({native.pages[CONVERSIONS].path.name}
                                                  if item['template'] == MATRICES else set()),
        }
        require(len(parsed.links) == len(set(parsed.links)) and
                set(parsed.links) == set().union(*destinations.values()), 'summary destination accounting mismatch')
        for kind, approved in destinations.items():
            link_kinds[kind] += sum(link in approved for link in parsed.links)
        # Destinations are also checked independently by validate_files on the
        # complete output, including all fragments. Never count TYPE_LINK here.
        links += len(parsed.links)
        require(len(parsed.links) == (4 if item['template'] == VECTORS else 6), 'summary hyperlink count mismatch')
        vectors += item['template'] == VECTORS; matrices += item['template'] == MATRICES
        sections['api/' + page.path.name] = section
    return sections, {'qualified_generic_instances': len(instances), 'vector_summaries': vectors,
                      'matrix_summaries': matrices, 'generic_summary_links': links,
                      'presentation_only_anchors': len(sections), 'unsupported_instances': unsupported,
                      'native_instance_member_declarations': 0, **link_kinds}
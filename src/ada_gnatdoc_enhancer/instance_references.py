"""Separately qualified explanatory type marks, NEVER native public symbols.

The admitted domain is the reviewed eight-depth 2/3/4 vectors and Float32 3x3
matrix. Qualification, pristine pages and exact summary rendering are rechecked
before targets exist. This module does not mutate verified_types/public_symbols.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import html
import re

from .generic_instances import ANCHOR, ELEMENTS, MATRICES, VECTORS, qualification, summaries
from .inventory import HEADER, mask_ada
from .profiles import reconcile
from .util import IDENT, require


@dataclass(frozen=True)
class InstanceReference:
    identity: str
    package: str
    page: str
    summary: str

    @property
    def href(self):
        return self.page + '#' + ANCHOR


def targets(config, source, native, sections=None):
    if not config.instance_references:
        return {}
    require(config.generic_instances and config.symbol_bookmarks and
            config.navigation == 'packages' and config.type_links,
            'incoming instance references lack explicit qualified profile')
    instances, _ = qualification(config, source, native)
    reconstructed, _ = summaries(config, source, native)
    require(sections is None or sections == reconstructed, 'changed explanatory summary sections')
    approved = {'opencv.core.' + element.removesuffix('_Value').lower() + '_vec' + str(length):
                (VECTORS, element, [length]) for element in ELEMENTS for length in (2, 3, 4)}
    approved['opencv.core.float32_matx3x3'] = (MATRICES, 'Float32_Value', [3, 3])
    result = {}
    for key, item in instances.items():
        require(key in approved and
                (item['template'], item['element_type'], item['dimensions']) == approved[key],
                'unapproved incoming instance-reference family')
        member = 'vector' if item['template'] == VECTORS else 'matrix'
        identity = key + '.' + member
        page = native.pages[key]
        require(not page.sections, 'instance summary cannot confer native declaration authority')
        section = reconstructed['api/' + page.path.name]
        require(section.count('id="' + ANCHOR + '"') == 1, 'ambiguous explanatory destination')
        result[identity] = InstanceReference(identity, key, page.path.name, section)
    return result


@lru_cache(maxsize=128)
def public_scope(text):
    """Bounded ordinary public scope; no aliases, use clauses or implicit scopes."""
    code = mask_ada(text); header = HEADER.search(code)
    if not header or header[1] or header[3].lower() != 'is':return None
    context = code[:header.start()]
    if re.search(r'\bgeneric\b', context, re.I):return None
    body = code[header.end():]
    if re.search(r'\bprivate\s+with\b', body, re.I):return None
    private = re.search(r'\bprivate\b(?!\s*;)', body, re.I)
    if private:body = body[:private.start()]
    else:body = re.sub(r'\bend\s+(?:[A-Za-z][A-Za-z0-9_.]*\s*)?;\s*$', '', body, flags=re.I)
    if re.search(r'\b(package|generic|task|protected|begin|declare|renames|use)\b', body, re.I):return None
    return context, body


def resolve(name, text, start, end, pkg, source, approved):
    """Exact import plus lexical ancestor lookup, with fail-closed shadow guards."""
    if not approved or '.' not in name:return None
    from .syntax import _current_type_context
    # RANGE inside a complete array index constraint is not an expression
    # context for the following OF type mark. Admit only balanced index syntax
    # and the final component type, not arbitrary text following RANGE.
    before = mask_ada(text)[:start]
    array = re.fullmatch(r'\s*type\s+' + IDENT + r'\s+is\s+array\s*\((.*)\)\s+of\s+',
                         before, re.I | re.S)
    array_component = False
    if array and not re.search(r':=|=>|\b(with|function|procedure|return)\b', array[1], re.I):
        depth = 0; valid = True
        for char in array[1]:
            if char == '(':depth += 1
            elif char == ')':depth -= 1
            if depth < 0:valid = False
        array_component = valid and depth == 0 and bool(re.fullmatch(r'\s*;', text[end:].strip()))
    if not array_component and not _current_type_context(text, start, end):return None
    matches = [d for d in pkg.declarations if reconcile(d.signature, text) is not None]
    if len(matches) != 1:return None
    declaration = matches[0]
    token = name.lower(); prefix = token.split('.')[0]
    owner = token.rpartition('.')[0]; scope = pkg.name.lower(); scopes = []
    while scope:
        if scope not in source:return None
        admitted = public_scope(source[scope].source)
        if admitted is None:return None
        # Decline every bare use of the prefix in the public region, including
        # objects, enum literals, discriminants, formals and comma declarations.
        # Qualified references and selected suffixes are not defining names.
        body = admitted[1]
        for occurrence in re.finditer(r'\b' + re.escape(prefix) + r'\b', body, re.I):
            if not body[occurrence.end():].lstrip().startswith('.') and not body[:occurrence.start()].rstrip().endswith('.'):
                return None
        scopes.append(scope); scope = scope.rpartition('.')[0]
    context, body = public_scope(pkg.source)
    if mask_ada(declaration.signature).strip() not in body:return None
    imports = set()
    # Only ordinary WITH clauses grant this new authority, never private or
    # limited context, package suffix matching, or inherited USE visibility.
    for clause in re.finditer(r'(?:^|;)\s*with\s+([^;]+);', context, re.I):
        imports.update(n.strip().lower() for n in clause[1].split(','))
    if '.' not in owner:
        for scope in scopes:
            candidate_owner = scope + '.' + owner
            if candidate_owner in source:
                candidate = candidate_owner + '.' + token.rsplit('.', 1)[1]
                return approved.get(candidate) if candidate_owner in imports else None
        return None
    return approved.get(token) if owner in imports else None


def metadata(approved):
    if not approved:return ''
    return ('<div id="instance-reference-navigation" hidden>' + ''.join(
        '<a href="' + html.escape(target.href, quote=True) + '" data-instance="' +
        identity + '"></a>' for identity, target in sorted(approved.items())) + '</div>')
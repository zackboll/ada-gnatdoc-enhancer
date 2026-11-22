"""Source-to-source body reconciliation (separate from native projections).

RM 6.3, 6.3.1: retain defining names, modes, subtype/result identity and
defaults in the supported subset. Native presentation equivalences are not
Ada conformance rules. A potential homograph we cannot rule out blocks a link.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re

from .profiles import callable_profile, closing, type_mark


STANDARD = frozenset('''boolean character wide_character wide_wide_character
string wide_string wide_wide_string integer natural positive short_integer
short_short_integer long_integer long_long_integer float short_float long_float
long_long_float duration'''.split())
FOREIGN = frozenset(('import', 'interface', 'convention', 'import_function', 'import_procedure',
                     'interface_name'))


@dataclass(frozen=True)
class Profile:
    # None for a mark means resolution failed, not a wildcard match.
    formals: tuple[tuple[str, str, str | None, tuple[str, ...]], ...]
    result: str | None

    @property
    def resolved(self):
        return self.result is not None and all(
            subtype is not None and (not default or default[0] != '?')
            for _, _, subtype, default in self.formals)


def profile(items, resolve):
    if not items or callable_profile(items) != len(items):
        return None
    formals = []
    names = set()

    def mark(parts):
        return None if not parts or parts[0] in names else resolve(parts)

    at = 2
    if items[at:at+1] == ('(',):
        end = closing(items, at)
        groups = []
        start = at + 1; i = start
        while i < end:
            if items[i] == '(':
                i = closing(items, i)
            elif items[i] == ';':
                groups.append(items[start:i]); start = i + 1
            i += 1
        groups.append(items[start:end]); at = end + 1
        for group in groups:
            colon = group.index(':')
            rest = group[colon+1:]; mode = 'in'
            for prefix in (('in', 'out'), ('in',), ('out',)):
                if rest[:len(prefix)] == prefix:
                    mode = ' '.join(prefix); rest = rest[len(prefix):]; break
            default = ()
            if ':=' in rest:
                split = rest.index(':='); default = rest[split+1:]; rest = rest[:split]
                # Literal equality alone is not enough for a named or operator
                # expression. Admit integer literals only, with their original
                # token spelling and a resolved contextual subtype.
                if len(default) != 1 or not re.fullmatch(r'[0-9]+(?:_[0-9]+)*', default[0]):
                    default = ('?',)
            subtype = mark(rest)
            for name in group[:colon:2]:
                if name in names:
                    return None
                names.add(name)
                formals.append((name, mode, subtype, default))
    result = mark(items[at+1:]) if items[0] == 'function' else ''
    return Profile(tuple(formals), result)


def resolver(spec, body, ancestors, line, *, implementation):
    """Resolve directly visible selected type marks without suffix equivalence.

    For independently reviewed, valid Ada sources, an unchanged selected
    name with the same nonlimited library visibility and no lexical shadow
    denotes the same declaration. Bare names require owned type evidence or
    Standard; resolution through USE clauses is never guessed.
    """
    chain = [spec, *ancestors]
    # Body declarations can hide the specification's names. Treat even later
    # declarations as potential shadowing rather than attempting visibility
    # recovery for unsupported declarative items.
    shadow = body.bindings if implementation else {}

    def resolve(items):
        if not type_mark(items):
            return None
        name = ''.join(items); root = items[0]
        if root in shadow:
            return None
        if len(items) == 1:
            for unit in chain:
                if unit is None:
                    return None
                if root not in unit.bindings:
                    continue
                if (unit.bindings[root] <= {'type', 'subtype'} and root in unit.public_types and
                        (unit is not spec or implementation or unit.public_types[root] < line)):
                    return unit.name + '.' + root
                return None
            return 'standard.' + root if root in STANDARD else None
        if any(unit is None or root in unit.bindings for unit in chain):
            return None
        owner, _, member = name.rpartition('.')
        if owner == 'standard':
            return name if member in STANDARD else None
        for unit in chain:
            if unit.name == owner:
                return name if (unit.bindings.get(member, set()) <= {'type', 'subtype'} and
                                member in unit.public_types and
                                (unit is not spec or implementation or
                                 unit.public_types[member] < line)) else None
        # Require the same selected library identity independently visible
        # from the spec's context (which also scopes over the body, RM 10.1.2).
        # A body-only WITH can make a different, longer child prefix visible.
        def library(context):
            paths = [p for p in context if owner == p or owner.startswith(p + '.')]
            return max(paths, key=len, default=None)
        lib = library(spec.contexts)
        if lib == owner and library(spec.contexts | body.contexts) == lib:
            return name
        return None

    return resolve


def may_overlap(left, right):
    if left is None or right is None:
        return True
    if len(left.formals) != len(right.formals):
        return False
    # Compare only candidates for this deliberately narrow subtype-identity
    # relation (not Ada overload legality, which uses base types). Unknown
    # marks do not make a candidate disjoint.
    pairs = [(a[2], b[2]) for a, b in zip(left.formals, right.formals)]
    pairs.append((left.result, right.result))
    return all(a is None or b is None or a == b for a, b in pairs)


def reconcile(pkg, declarations, specification, implementation, sources):
    """Return one (body line or omission reason) per native-backed callable."""
    operations = [d for d in declarations if d.declaration.kind in ('function', 'procedure')]
    if implementation is None or specification is None:
        reason = 'no-qualified-package-body' if implementation is None else 'unsupported-specification-scope'
        return {d.section.anchor: (None, reason) for d in operations}
    ancestors = []
    parts = pkg.name.lower().split('.')
    for i in range(len(parts)-1, 0, -1):
        ancestors.append(sources.get('.'.join(parts[:i])))
    spec_headers = defaultdict(list)
    spec_names = defaultdict(list)
    for header in specification.headers:
        spec_headers[header.kind, header.name, header.line].append(header)

    def bind(header, *, body):
        return profile(header.profile, resolver(specification, implementation, ancestors,
                                                header.line, implementation=body))

    for h in specification.headers:
        spec_names[h.kind, h.name].append((h, bind(h, body=False)))

    bodies = defaultdict(list)
    for h in implementation.headers:
        bodies[h.kind, h.name].append((h, bind(h, body=True)))
    # Direct pragmas with foreign/unknown calling conventions may govern a
    # declaration whose header is otherwise ordinary. Named association and
    # overloaded identifiers are intentionally not resolved here.
    foreign = {word for pragma in specification.pragmas + implementation.pragmas
               if pragma and pragma[0] in FOREIGN for word in pragma[1:]}
    result = {}
    for d in operations:
        decl = d.declaration
        key = (decl.kind, decl.name.lower())
        found = spec_headers[(*key, decl.source_line)]
        line = None
        if len(found) != 1 or not found[0].public:
            reason = 'unsupported-declaration-scope'
        elif found[0].form != 'declaration':
            reason = 'specification-' + found[0].form
        elif key[1] in foreign:
            reason = 'foreign-or-unsupported-convention'
        else:
            expected = bind(found[0], body=False)
            candidates = bodies[key]
            if expected is None or not expected.resolved:
                reason = 'unsupported-or-unresolved-profile'
            elif any(h is not found[0] and may_overlap(expected, p) for h, p in spec_names[key]):
                reason = 'ambiguous-specification-candidates'
            else:
                plausible = [(h, p) for h, p in candidates if may_overlap(expected, p)]
                if len(plausible) > 1:
                    reason = 'ambiguous-body-candidates'
                elif not plausible:
                    reason = 'no-conformant-direct-body'
                else:
                    h, p = plausible[0]
                    if h.form != 'body':
                        reason = 'implementation-' + h.form
                    elif p != expected:
                        reason = 'unsupported-or-nonconformant-body-profile'
                    else:
                        line, reason = h.line, None
        result[d.section.anchor] = line, reason
    # Distinct native destinations cannot share a single implementation. Do
    # not choose a winner if unsupported or inconsistent input led to a tie.
    reverse = defaultdict(list)
    for anchor, (line, _) in result.items():
        if line is not None:
            reverse[line].append(anchor)
    for anchors in reverse.values():
        if len(anchors) > 1:
            for anchor in anchors:
                result[anchor] = None, 'ambiguous-reverse-destination'
    return result
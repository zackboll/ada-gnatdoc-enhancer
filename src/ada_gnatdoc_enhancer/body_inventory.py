"""Boundary evidence for a single ordinary Ada library package.

This walker recognizes a deliberately limited grammar. It never searches past
an unknown boundary for a plausible END or a same-named subprogram. Tokens in
delimited expressions and literals cannot open or close declaration scopes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .profiles import identifier
from .source_lexer import tokenize

CONTRACT_ASPECTS = frozenset(('pre', 'post', 'global', 'depends'))


class Unsupported(ValueError):
    """The lexical scope or unit form could not be established."""


@dataclass(frozen=True)
class Header:
    kind: str
    name: str
    line: int
    profile: tuple[str, ...]
    form: str
    public: bool


@dataclass
class Unit:
    name: str
    line: int
    body: bool
    contexts: set[str] = field(default_factory=set)
    headers: list[Header] = field(default_factory=list)
    # Direct bindings, including private names; no nested declarations leak.
    bindings: dict[str, set[str]] = field(default_factory=dict)
    public_types: dict[str, int] = field(default_factory=dict)
    pragmas: list[tuple[str, ...]] = field(default_factory=list)


class Walker:
    def __init__(self, text):
        self.words = []; self.lines = []; self.pairs = {}
        line = 1; stack = []; self.balanced = True
        for token in tokenize(text):
            if token.kind not in ('space', 'comment'):
                word = token.text if token.kind in ('string', 'character') else token.text.lower()
                i = len(self.words)
                if word in ('(', '['):
                    stack.append((word, i))
                elif word in (')', ']'):
                    if stack and stack[-1][0] == {')': '(', ']': '['}[word]:
                        self.pairs[stack.pop()[1]] = i
                    else:
                        self.balanced = False
                if token.kind == 'plain':
                    self.balanced = False
                self.words.append(word); self.lines.append(line)
            line += token.text.count('\n')
        self.balanced &= not stack
        self.words.append('')
        self.at = 0

    @staticmethod
    def need(ok):
        if not ok:
            raise Unsupported('unsupported or unbalanced Ada scope')

    @property
    def word(self):
        return self.words[self.at]

    def take(self, word):
        if self.word != word:
            return False
        self.at += 1
        return True

    def expect(self, word):
        self.need(self.take(word))

    def name(self, *, operator=False):
        start = self.at
        if operator and self.word.startswith('"'):
            self.at += 1
        else:
            self.need(identifier(self.word)); self.at += 1
            while self.take('.'):
                self.need(identifier(self.word)); self.at += 1
        return ''.join(self.words[start:self.at])

    def scan(self, stops, *, forbidden=()):
        """Scan a flat clause, skipping only checked bracket/parenthesis pairs."""
        while self.word not in stops:
            self.need(self.word and self.word not in forbidden)
            self.need(self.word not in ('(', '[') or self.at in self.pairs)
            self.at = self.pairs.get(self.at, self.at) + 1

    def statement(self):
        self.scan({';'}, forbidden={'begin', 'end', 'declare'})
        self.at += 1

    def aspects(self):
        """Consume complete top-level associations; do not hide Import etc."""
        supported = True
        end = {'is', 'renames', ';'}
        while True:
            supported &= self.name() in CONTRACT_ASPECTS
            if self.take('=>'):
                self.scan(end | {','}, forbidden={'begin', 'end', 'declare'})
            if not self.take(','):
                self.need(self.word in end)
                return supported

    def context(self):
        contexts = set()
        while True:
            if self.word in ('use', 'pragma'):
                self.statement(); continue
            start = self.at
            limited = self.take('limited')
            self.take('private')
            if not self.take('with'):
                self.at = start
                return contexts
            while True:
                name = self.name()
                if not limited:
                    contexts.add(name)
                if not self.take(','):
                    break
            self.expect(';')

    def unit(self, body):
        self.at = 0
        self.need(self.balanced)
        contexts = self.context()
        line = self.lines[self.at] if self.word else 0
        self.expect('package')
        if body:
            self.expect('body')
        name = self.name()
        if self.take('with'):
            self.scan({'is'}, forbidden={';', 'begin', 'end', 'declare'})
        self.expect('is')
        self.need(self.word not in ('new', 'separate'))
        unit = Unit(name, line, body, contexts)
        self.region(name, body, unit=unit)
        self.need(not self.word)
        return unit

    def close(self, name):
        self.expect('end')
        if self.word != ';':
            self.need(self.name(operator=True) in (name, name.rsplit('.', 1)[-1]))
        self.expect(';')

    def region(self, name, body, *, unit=None, executable=False):
        public = not body
        while self.word not in ('end', 'begin'):
            if not body and self.take('private'):
                self.need(public); public = False
            else:
                self.declaration(unit, public)
        if self.take('begin'):
            self.need(body)
            self.handled_sequence()
        else:
            self.need(not executable)
        self.close(name)

    def declaration(self, unit, public, generic=False):
        start = self.at
        if self.take('generic'):
            self.need(not generic)
            while self.word in ('with', 'use', 'type') or identifier(self.word):
                # Formal type/object and WITH package/subprogram declarations.
                self.statement()
            self.need(self.word in ('package', 'procedure', 'function'))
            self.declaration(unit, public, generic=True)
            return
        if self.take('not'):
            self.expect('overriding')
        else:
            self.take('overriding')
        head = self.at; kind = self.word
        if kind in ('package', 'task', 'protected', 'function', 'procedure', 'entry'):
            self.at += 1
            body = self.take('body')
            self.need(not body or kind in ('package', 'task', 'protected'))
            if kind in ('task', 'protected'):
                self.take('type')
            name = self.name(operator=kind == 'function')
            self.need('.' not in name or name.startswith('"'))
            self.scan({'is', 'renames', ';', 'with', 'when'},
                      forbidden={'begin', 'end', 'declare'})
            profile = tuple(self.words[head:self.at])
            unsupported_aspects = self.take('with') and not self.aspects()
            if kind == 'entry' and self.take('when'):
                self.scan({'is'}, forbidden={';', 'begin', 'end', 'declare'})
                body = True
            if self.take('is'):
                form = {'new': 'instance', 'separate': 'separate', 'abstract': 'abstract',
                        'null': 'null', '(': 'expression'}.get(self.word, 'body' if
                             body or kind in ('function', 'procedure') else 'scope')
                if form in ('body', 'scope'):
                    self.region(name, form == 'body', executable=kind in (
                        'function', 'procedure', 'task', 'entry'))
                else:
                    self.statement()
            elif self.take('renames'):
                form = 'renaming'; self.statement()
            else:
                form = 'declaration'; self.expect(';')
            if unit is not None:
                if kind in ('function', 'procedure'):
                    unit.headers.append(Header(kind, name, self.lines[start], profile,
                                               'generic' if generic else 'aspects' if unsupported_aspects else form,
                                               public))
                self.bind(unit, name, kind)
            return
        self.need(not generic and start == head)
        if kind in ('use', 'pragma', 'for'):
            if kind == 'for':
                self.scan({';', 'record'}, forbidden={'begin', 'end', 'declare'})
                if self.word == 'record':
                    self.record(representation=True)
                self.expect(';')
            else:
                self.statement()
                if kind == 'pragma' and unit is not None:
                    unit.pragmas.append(tuple(self.words[start+1:self.at-1]))
            return
        if kind in ('type', 'subtype'):
            self.at += 1
            name = self.name()
            if unit is not None:
                self.bind(unit, name, kind)
                if public:
                    unit.public_types.setdefault(name, self.lines[start])
            self.scan({';', 'record'}, forbidden={'begin', 'end', 'declare'})
            if self.word == 'record':
                if self.words[self.at-1] == 'null':
                    self.at += 1
                else:
                    self.record()
                self.scan({';'}, forbidden={'begin', 'end', 'declare'})
            self.expect(';')
            return
        # Object/number/exception declarations: require the defining-name list
        # and colon, rather than skipping arbitrary unknown scope openers.
        while True:
            self.need(identifier(self.word))
            if unit is not None:
                self.bind(unit, self.word, 'object')
            self.at += 1
            if not self.take(','):
                break
        self.expect(':')
        self.statement()

    @staticmethod
    def bind(unit, name, kind):
        unit.bindings.setdefault(name, set()).add(kind)

    def record(self, *, representation=False):
        self.expect('record')
        variants = 0
        while True:
            self.scan({'end', 'case'}, forbidden={'begin', 'declare'})
            if self.take('case'):
                self.need(not representation); variants += 1
            else:
                self.expect('end')
                if self.take('record'):
                    self.need(variants == 0)
                    return
                self.expect('case'); self.expect(';')
                variants -= 1; self.need(variants >= 0)

    def condition(self):
        while True:
            self.scan({'then'}, forbidden={';', 'begin', 'end', 'declare'})
            self.at += 1
            if self.words[self.at-2] != 'and':
                return

    def handled_sequence(self):
        self.sequence({'end', 'exception'})
        if self.take('exception'):
            self.expect_handler()

    def expect_handler(self):
        self.need(self.word == 'when')
        while self.take('when'):
            self.scan({'=>'}, forbidden={';', 'end', 'begin', 'declare'})
            self.at += 1
            self.sequence({'when', 'end'})

    def sequence(self, stops):
        while self.word not in stops:
            self.need(self.word not in ('', 'end', 'else', 'elsif', 'exception', 'when'))
            if self.take('<<'):
                self.name(); self.expect('>>'); continue
            name = ''
            if identifier(self.word) and self.words[self.at+1] == ':':
                name = self.name(); self.expect(':')
                self.need(self.word in ('declare', 'begin', 'loop', 'while', 'for'))
            if self.take('declare'):
                self.region(name, True, executable=True)
            elif self.take('begin'):
                self.handled_sequence(); self.close(name)
            elif self.take('if'):
                self.condition(); self.sequence({'end', 'elsif', 'else'})
                while self.take('elsif'):
                    self.condition(); self.sequence({'end', 'elsif', 'else'})
                if self.take('else'):
                    self.sequence({'end'})
                self.expect('end'); self.expect('if'); self.expect(';')
            elif self.take('case'):
                self.scan({'is'}, forbidden={';', 'begin', 'end', 'declare'})
                self.at += 1; self.expect_handler()
                self.expect('end'); self.expect('case'); self.expect(';')
            elif self.word in ('loop', 'for', 'while'):
                self.scan({'loop'}, forbidden={';', 'begin', 'end', 'declare'})
                self.at += 1; self.sequence({'end'})
                self.expect('end'); self.expect('loop')
                if self.word != ';':
                    self.need(name and self.name() == name)
                self.expect(';')
            elif self.word in ('return', 'accept'):
                kind = self.word
                self.scan({'do', ';'}, forbidden={'begin', 'end', 'declare'})
                if self.take('do'):
                    self.handled_sequence(); self.expect('end')
                    if kind == 'return':
                        self.expect('return')
                    elif self.word != ';':
                        self.name()
                self.expect(';')
            else:
                self.need(self.word != 'select')
                self.statement()


def package_header(text, *, body):
    """Recognize the first library declaration, not any subsequent text match."""
    try:
        walker = Walker(text)
        walker.context()
        walker.expect('package')
        if body:
            walker.expect('body')
        name = walker.name()
        if body:
            # Register the claim even if its tail is malformed. A selected
            # package cannot evade inventory by breaking a delimiter later.
            return name
        if walker.take('with'):
            walker.scan({'is'}, forbidden={';', 'begin', 'end', 'declare'})
        walker.expect('is')
        walker.need(walker.word not in ('new', 'separate'))
        return name
    except (Unsupported, RecursionError):
        return None


def parse_unit(text, *, body):
    try:
        return Walker(text).unit(body)
    except (Unsupported, RecursionError):
        return None
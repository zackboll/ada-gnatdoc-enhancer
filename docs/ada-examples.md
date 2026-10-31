# Source-verified Ada examples (GNATDOC-027)

This is a development feature, not an official v0.1.3 archive or release.
Rendering is static, deterministic and offline. There is no browser highlighter,
network lookup, JavaScript dependency, external stylesheet or consumer-code execution.

## Configuration contract

The following optional Boolean fields extend the existing **configuration
schema_version = 1** contract. The authored qualification manifest remains schema 2.
Add them to an existing `[guides]` table (do not create a second table):

```toml
schema_version = 1
# ... existing project and source configuration ...
[guides]
mode = "authored-markdown"
manifest = "authored.json"
sha256 = "<independently approved SHA-256 of the qualification manifest>"
ada_example_highlighting = true
ada_example_api_links = true
ada_landing_example_highlighting = true
```

All three fields default to `false`. Only TOML Booleans are accepted; strings,
numbers, arrays and tables are errors. Presence of any example field, even `false`,
requires `authored-markdown`; legacy `markdown`, `html`, `authored-html` and `none`
are not supported. API links require `ada_example_highlighting = true`.
Landing highlighting is independently selectable. Landing API links require all
three fields. Existing `[presentation].syntax_highlighting` and `type_links`
continue to apply only to native declarations; they do not enable this feature.

Omitted options preserve the complete v0.1.3 output bytes, including publication
metadata. Explicit `false` in the supported mode has the same rendering behavior.
For custom consumer themes, configuration bytes are already hash-bound: changing
even disabled settings requires regeneration from pristine native input.

## Markdown

Only fences with exactly `ada` as their language are enhanced:

````markdown
```ada
with OpenCV.Core;
procedure Example is
   use OpenCV.Core;
   Image : Mat;
begin
   -- Source text remains selectable, including this comment.
   null;
end Example;
```
````

The existing lexer supplies `ada-keyword`, `ada-string`, `ada-character`,
`ada-number`, `ada-attribute`, `ada-comment` and `ada-operator` spans. Keywords
inside identifiers, strings and comments are not reinterpreted. HTML characters
are escaped, not executed. Decoded `<code>` text equals the Markdown parser's
original fence content, including capitalization, whitespace and final newline.
CommonMark's existing parsing rules (including newline/indent normalization) are
unchanged. `sh`, `shell`, `text` and unclassified fences keep their existing renderer.
An empty, text-free line-box span preserves the final LF in Chromium
native selection/clipboard; it adds no character to the decoded code text.

## Link evidence and conservative limitations

The new `ada-api-reference` anchors are reconstructed from `source_destinations`:
approved public source inventory, exact owning package, complete declaration
profile reconciled with native GNATdoc, observed filename and distinct native
anchor. Source-order overload ordinals are retained as evidence, **not** treated
as overload resolution. No destination is supplied by an example or publication
manifest. Existing verified `api:` prose links keep their existing behavior.

Supported example references are flat public types/subtypes in type-mark contexts
and uniquely declared functions/procedures followed by `(`, including multiline
calls. Fully qualified names establish the owner. Bare names require exactly one
explicit `use Package;` in the same fence, before the reference, without an intervening
`end`; multiple/unknown use-visible namespaces, package/generic scopes and derived
types suppress bare-name routing. Fragments without visibility evidence remain
unlinked; guide prose or a globally unique spelling does not grant Ada visibility.

The resolver deliberately does **not** infer argument types or prefixed object-call
semantics. All overloaded names remain unlinked, including pinned Core `Create`,
`Clone` and `OpenCV.Core.Float32_Access.Get`. A consumer with one uniquely supported
callable can link its qualified call. There is no symbol-level overload router.
`OpenCV.Core.Mat` and `Mat` link only in supported type contexts.

Local defining names (objects, formals, types, callable/package/task/protected
names, loop variables and enum literals) suppress that spelling across the whole
fence, including earlier scopes. This deliberately sacrifices valid links to avoid
guessing. Comments, strings, private declarations, unsupported generic/nested
packages, missing declarations and ambiguous ownership never create targets.
This is a narrow lexical adapter, not a complete Ada compiler or semantic resolver.

Guide links use `../api/<observed-file>#<anchor>`; homepage links use
`api/<observed-file>#<anchor>`. No external URL can become an example destination.
Verification reconstructs exact output again from source/native authority: updating
`presentation.json` checksums cannot authorize changed links, classes or markup.
The trust root remains independently approved project configuration/source/native
acquisition, not protection against replacement of all those authorities together.

## Landing example

Landing opt-in requires the existing qualification manifest's `landing_example`
source identity and its approved input hash. Exactly one **plain `<pre>`** must
have decoded text equal to that source with terminal LF characters removed, as
required by the existing homepage example convention. Missing, repeated or nested
matches, tags, comments and attributes inside/on the matched pre are errors.
Arbitrary consumer HTML attributes cannot act as rendering instructions.

Only that pre gains `class="ada-example"`, `tabindex="0"`, escaped token spans and
optional verified links. Other pre elements, shell commands and markup are unchanged.
A local stylesheet link is added to the existing head (including HTML's omitted-head
form). Existing stylesheets are never edited. Code remains keyboard-scrollable,
selectable and copyable; links are native, keyboard-focusable HTML anchors.

## Output changes and qualification

Opt-in adds `assets/gnatdoc-examples.css`, scoped to `.ada-example`, with light/dark
colors and focus outlines. Guide highlighting changes guide HTML only; landing
highlighting changes `index.html` only. Publication metadata changes only for the
new/changed output hashes (plus existing custom-theme configuration identity).
Native API pages, source-order identities, navigation/search records and existing
CSS bytes do not change. Regenerate a pristine site to enable/disable settings;
an existing publication is verified, not silently migrated.

`scripts/qualify_examples.py` compares five pinned profiles against the independently
installed official wheel, including Core's full native 195-package/search fixture.
`scripts/check_examples_browser.py` exercises generated localhost HTTP documentation
at 1280×900/390×900, light/dark, JavaScript enabled/disabled, retaining screenshots
and structured results. Playwright is a separate qualification tool only.
The unit suite includes source text, visibility, shadowing, ambiguity, landing
identity and rehashed-publication tampering tests. See the PR qualification report
for actual executed environment counts and remaining gates.

Baseline count discrepancy: the pinned official v0.1.3 Core search fixture contains
1,462 records (195 packages, 215 types/subtypes, 1,047 operations, five guides), as
asserted by the existing `test_search.py`. The task's stated 1,487 is not the count
of that fixture. Qualification preserves the official records byte-for-byte rather
than adding invented records. This discrepancy needs independent reconciliation
before claiming the requested 1,487-record production-site gate.
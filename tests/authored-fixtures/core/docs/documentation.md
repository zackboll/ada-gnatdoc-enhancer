# Public Ada API documentation

The specifications in `src/` are authoritative. The generated site is intended
for `https://zackboll.github.io/opencv_core_ada/`; its landing page is
`_site/index.html` and the native GNATdoc reference is `_site/api/index.html`.
Do not commit generated HTML.

## Searchable, bookmarkable native navigation (CORE-DOC-071)

The native API browser now offers local, case-insensitive substring search over
fully qualified package names. Clear restores the original order; no results is
announced through a labelled live status. Filtering never navigates the document
frame or filters the separate tagged-type list. The active package has both a
persistent visual indicator and `aria-current="page"`, independently of focus.

Share package URLs such as `api/index.html?package=OpenCV.Core.Sparse`.
Ada identifier case is ignored and the outer URL is canonicalized. Unknown,
duplicate, path-like or external package requests deterministically select
OpenCV.Core. Destinations come only from the verified native anchors, never
from query text. Initial selection uses frame location replacement once; sidebar
selection records outer history and replaces frame history. Same-origin iframe
loads reconcile package identity without changing declaration fragments. Back,
Forward and reload restore package selection. Declaration-level bookmarks and
foreign-origin iframe synchronization are explicitly outside this contract.

Without JavaScript, the search controls remain hidden and all 195 native package
links, four tagged-type links, and both fragment-based tabs remain functional.
No declaration page receives JavaScript. Native hrefs, target attributes, iframe,
declaration anchors and GNATdoc CSS are not rewritten.

### Qualified GNATdoc 26.0.0 shell and safety gate

The native `index.html` contains a `.side-navigation` with `.tab-bar` links to
`#compilation-units` and `#tagged-types`. Its `.content-column` contains two h2
headings followed by ul lists: 195 compilation units in case-insensitive lexical
order, then Mat, File_Storage, Sparse_Mat and UMat. All 199 native anchors target
`document-content`; tagged destinations include native type fragments. There is
one iframe named `document-content`, with no id or initial src. Native tabs
scroll the sidebar to headings; they are not JavaScript tab panels.

`enhance_gnatdoc_navigation.py` independently reconstructs this exact pinned
serialization from authoritative public source names, actual generated h1
headings and source-matched tagged declarations. It checks complete unique
coverage and discovers, rather than computes, the 64-hex filenames. An unknown
layout, swapped real destinations or altered target stops generation before
augmentation. The presentation manifest still protects all non-snippet HTML;
it cannot authorize an incorrect navigation shell. Only one hidden control
group and one deferred repository-owned script are permitted. The final
validator independently repeats reconstruction and compares shipped script
bytes. Exact serialization also rejects duplicate IDs, inline handlers and
unapproved scripts. Repeat installation is byte-idempotent.

### Local qualification

Starting main: `662e320201807e743072b3ed71c938fcd6227c9c`; PRs #71/#72 merged,
canonical worktree clean, no overlapping open PR. An isolated worktree was used;
CORE-DOC-070A/B worktrees were not modified. The negative-first test file failed
before the implementation module existed. The actual final validator rejects
duplicate/missing identities, wrong and swapped existing destinations, changed
iframe targets, missing/duplicate scripts, tampered assets, missing tagged
links, unsupported structure, duplicate controls, inline script/handlers,
external destinations and traversal. All 95 Python documentation tests pass.

Pinned generation retains 195 packages / 197 HTML pages, 25 enriched instances,
102 summary links, 2,698 type links on 168 pages, and 1,268 original snippets.
Warnings and added/removed warning identities remain zero. Saved-baseline byte
comparison finds every declaration page unchanged, including Float16 exact
encoding prose and syntax highlighting. Only the browser index and theme asset
change, with one new local script. Fresh regeneration and repeated navigation,
theme and highlighting installation are byte-identical. Final validation,
shell syntax, actionlint and whitespace checks pass.

Real headless Chrome over local HTTP exercises 1280px and 390px in light/dark:
default selection, filtering/clear/no-match/order, sidebar selection, copied
bookmark in a fresh context, reload, Back/Forward, iframe cross-package links,
Vector/Matrix summary links, tagged anchors, focus and page overflow. Native
navigation also passes with JavaScript disabled at both widths. Representative
screenshots were captured and visually inspected. Browser tooling is optional,
installed separately, and not a site runtime or library dependency:

```sh
python3 -m http.server 8071 --bind 127.0.0.1 --directory _site
# In another terminal, use an existing external Playwright installation:
PLAYWRIGHT_MODULE=/absolute/path/to/playwright node scripts/test_gnatdoc_navigation_browser.cjs
```

No executable Ada/C++, ABI, dispatch, dependency manifest or library behavior
changed. AUnit was not rerun; the previously recorded 2,025/2,025 evidence is
reused. Documentation CI runs the generated-site navigation mutation tests;
the optional browser harness is a local qualification tool. Pages deployment
remains restricted to main. This work stops at an open, unmerged review PR.

## Generic-instance signature links (CORE-DOC-070B)

Signature type marks now link to the existing explanatory summaries for exactly
the 25 independently qualified instances: the 24 vector instances and
Float32_Matx3x3. The enhancement-owned `instance-members-summary` ID belongs to
the summary section, not an Ada declaration. No native member anchors, h4
declarations or snippets are fabricated; summary member links still lead to
the real generic template declarations.

The native target collector previously found only source-backed native h4
types. Short selected names additionally failed its exact import-owner lookup.
The negative-first fixture reported no signature links for short and fully
qualified Vector/Matrix marks. Resolution now requires canonical package
identity, verified template/member and actual associations, an exact context
import, lexical ancestor lookup and no local/ancestor prefix blockers. Ada
identifier case is ignored. Consecutive context with clauses are all collected.
Unsupported scopes, renamings, unrelated instances and unsupported members
remain deliberately unlinked; this is not a general Ada semantic engine.

Before adding destinations the linker independently reconstructs and verifies
the summaries, native introductions and metadata. It discovers generated
filenames from package headings and never computes or hardcodes their hashes.
Every final link is recomputed from the original source-matched declaration;
wrong-but-existing instance destinations, missing links, missing/renamed
anchors and metadata/source mutations fail validation. Representative dense,
sparse and matrix links are mandatory in the final validator.

Qualification from main `bb91e81459b3bd446c7e12381783f5153b475d0d` (PR #71):

- 242 additional signature links: ten per vector instance (240), plus two
  matrix conversion references; total 2,698 on the same 168 enhanced pages.
- Independent saved-baseline comparison preserved all 2,456 original links
  and the escaped text of all 1,268 original declaration snippets.
- 195 public packages / 197 HTML pages; 25 enriched instances / 102 unchanged
  summary links; zero warnings and zero added/removed warning identities.
- All 92 documentation tests pass, including visibility negatives and final
  validator mutations redirecting Float16_Vec2 to Float32_Vec2 or Float16_Vec3.
- Fresh pinned regeneration and repeat enhancement/linking/highlighting produce
  byte-identical output. Final HTML validation, shell syntax, actionlint and
  diff whitespace checks pass.
- Headless Chrome clicks every instance-type link in the four representative
  packages in light/dark at 1280/390px, checks package identity and fragment
  scrolling, and navigates each representative through the native iframe.
- Executable Ada/C++, ABI, dependencies and manifests are unchanged. The
  existing PR #71 evidence of 2,025/2,025 AUnit tests is reused, not rerun.

## Generic instance summaries (CORE-DOC-070A)

GNATdoc 26.0.0's `Process_Generic_Instantiation` records package identity and
documentation, but does not populate instantiated members. The HTML backend
renders those empty collections; no supported CLI option expands them. The
pinned installed frontend/backend sources and native output were inspected.
No generator, installed template, or public Ada declaration is changed.

`scripts/enhance_gnatdoc_instances.py` discovers public instantiations from their
specifications. Support is limited to `OpenCV.Core.Vectors` (Element_Type,
Length) and `OpenCV.Core.Fixed_Matrices` (Element_Type, Row_Count, Column_Count).
Every named association must resolve exactly once; dimensions must be positive
decimal literals. Complete template declaration tokens must match the verified
private formal type, positive dimensions, zero-based subtypes and arrays.
Actual numeric source declarations are checked, including Float16's private
stored representation. Unknown actuals, positional/duplicate associations,
ambiguous visibility, changed templates and unsupported targeted vector/matrix
templates fail closed. Unrelated existing generic families are not enriched.

CORE-DOC-070A-R1 closes an ancestor-shadowing gap: finding the expected root
declaration does not establish that an unqualified actual denotes it. Resolution
now walks every parent scope through the expected owner, requires a single public
owner declaration, and rejects same-named intervening declarations regardless of
identifier case. It uses the full declaration index, not the public-only member
index. Renamings, use clauses, generics and other unsupported ancestor scopes fail
closed. Public child visible parts do not generally see ancestor private parts;
private descendants can. The bounded resolver deliberately rejects private
blockers too rather than guessing placement-dependent visibility. Float16's
private completion in its expected owner is not treated as a new declaration.

The public ancestor subtype regression was run before correcting production code
and failed with `CrossReferenceError not raised`, establishing that discovery had
accepted the shadowed actual. Tests now cover public/private ancestor blockers,
renamings, private descendants and mixed-case valid actuals. An isolated 2 × 4
matrix fixture independently asserts row bounds 0 .. 1, column bounds 0 .. 3,
dimensions and real template/type targets, then rejects exchanged bounds, wrong
dimensions and wrong-but-existing member anchors. It does not alter the 25-page
production baseline. Combined HTML/metadata tampering and byte-identical repeat
invocation remain qualified.

The baseline has 24 vector instances: UInt8, Int8, UInt16, Int16, Int32, Float16,
Float32 and Float64, each with lengths 2, 3 and 4; plus Float32_Matx3x3. Summaries
describe ordinary Ada arrays, actual element types, value semantics and zero-based
bounds. Float16 encodings are distinguished from numerical conversion. Vectors
receive no channel names. The fixed matrix links to its separate copying Mat
conversion package, without implying shared native storage.

Enrichment runs after diagnostics, zero-warning comparison and landing-page copy,
**before** theme installation, type linking and highlighting. Enhancement-owned
`section.generic-instance-summary` markup is inserted before native Description.
It creates no native `h4` sections, declaration snippets or instance-member
anchors. Member links explicitly lead to **generic template declarations**.
Package filenames and member/type anchors come from actual headings and
source-matched native declarations, never hardcoded hashes. The 102 new links
comprise 25 template-page, 51 template-member, 25 actual-type and one conversion
package link. Existing signature cross-references to instance members are deferred.

`generic-instances.json` records original instance HTML and package/file identity,
but is not the authority for facts or native content. Validation reparses sources,
recomputes bounds and targets, independently reconstructs the pinned native
empty-page serialization from each plain-text source introduction, and reproduces
the exact summary. Both published HTML and metadata must match. Unsupported
introduction markup and insertion layouts fail closed. Modified introductions
cannot qualify even if presentation and instance metadata are altered together.
Exactly 25 pages must qualify at the unchanged baseline.

The presentation manifest covers approved enriched non-snippet HTML; the separate
source-backed checker prevents it from blessing incorrect summaries. CORE-DOC-069
resolution is unchanged: 2,456 existing type links on 168 pages and 1,268 original
declarations remain protected by their existing link/highlighting contracts.

To extend support, establish authoritative semantics, association visibility and
native targets first; then add a narrow template contract, derivation and positive
and mutation fixtures. Never copy raw template HTML or invent native anchors.
Update exact baseline counts only after reviewed public source changes.

```sh
python3 -m unittest discover -s scripts -p 'test_gnatdoc_instances.py' -v
sh scripts/generate_docs.sh
python3 -m unittest discover -s scripts -p 'test_gnatdoc_instances.py' -v
python3 scripts/validate_docs.py _site
```

The first invocation uses realistic synthetic native HTML and real Ada fixtures.
The post-generation invocation additionally qualifies all 25 final pages,
existing type-link/snippet counts and idempotence. CI runs both. Metadata and HTML
are deterministic build artifacts and must not be committed.

## Modern presentation and Ada coloring (CORE-DOC-070)

GNATdoc remains pinned to 26.0.0. The generator first checks diagnostics and
the warning baseline, installs presentation metadata, resolves CORE-DOC-069
type links, colors declarations, and validates **final published HTML**.
No installed generator templates or native stylesheet are modified.

`docs/assets/gnatdoc-theme.css` is copied to `_site/api/gnatdoc-theme.css`.
`scripts/install_gnatdoc_theme.py` inserts its relative stylesheet link after
the exact native `gnatdoc.css` link and adds a mobile viewport to every API
page (including iframe documents). The landing page uses the same stylesheet.
System UI and monospace fonts require no external font service. Semantic CSS
variables provide light appearance by default and a separately selected dark
palette through `prefers-color-scheme`. Links are underlined, focus outlines
are explicit, and declaration targets have a border and background indication.
There are no added animations, runtime scripts, CDNs or theme-toggle scripts.

The sidebar scrolls independently on desktop. At widths of 800px and below,
navigation occupies the upper 30% of the viewport and the native iframe the
remaining space; long names wrap and declarations scroll horizontally inside
their panels. Native compilation-unit/tagged-type tabs remain anchor links.
The native browser does not track the selected package or select an initial
iframe document; CSS cannot provide persistent selected-package state. Hover,
keyboard focus and tab anchor targets are indicated instead. Search is out of
scope. Native links and declaration fragments are never rewritten.

`scripts/highlight_gnatdoc_ada.py` recognizes case-insensitive Ada 2022 reserved
words (including modes), decimal/based/exponent numbers with underscores,
strings with doubled quotes, characters, attributes, comments, and punctuation
and operators. It is lexical coloring, not parsing or semantic classification;
ordinary identifiers and uncertain input remain uncolored. Existing
`a.type-reference` elements are atomic and never receive nested spans. Original
entity spelling and declaration whitespace are preserved using decoded offsets.

The combined checker reconstructs type links from the trusted original snippets
and current public sources, then reconstructs syntax spans. It compares the
complete final markup exactly, not just whether destinations exist. Only flat
approved `span.ada-*` classes and the existing exact type-link format qualify.
Wrong-but-existing destinations, valid-HTML token mutations, unsupported tags,
extra attributes, nested anchors and incorrect token classes fail closed.
Removing approved markup must reproduce the original escaped Ada text exactly.
The existing non-snippet hashes remain enforced. `presentation.json` additionally
stores native non-snippet HTML for every API page, including the browser index;
validation reconstructs only the two approved metadata insertions and verifies
both the unchanged native CSS and the exact repository theme bytes. Both
transformations are deterministic and idempotent. Generated manifests are build
artifacts, not files to edit to accommodate an integrity failure.

Local qualification:

```sh
python3 -m unittest discover -s scripts -p 'test_highlight_gnatdoc_ada.py' -v
python3 -m unittest discover -s scripts -p 'test_link_gnatdoc_types.py' -v
python3 -m unittest discover -s scripts -p 'test_compare_gnatdoc_warnings.py' -v
sh scripts/generate_docs.sh
python3 scripts/validate_docs.py _site
git diff --check
```

When upgrading GNATdoc, inspect real native HTML/CSS first. Update the exact
insertion/section contracts and fixtures deliberately, retain semantic negative
tests, and regenerate/compare the original snippets and navigation. Never bypass
a format mismatch by accepting arbitrary HTML or regenerating native anchors.
The documentation workflow runs all three suites before publication; existing
artifact uploads and main-only Pages permissions are unchanged.
At DOC-070, Markdown guides remained links to GitHub. DOC-072 adds the five
published guide pages described below without changing native API pages.

### Local DOC-070 qualification

Starting main was `a56231a3f4179c210f0e8cce55ec574f356d9800` (PR #69 merge).
Pinned generation built the unchanged library and produced zero warnings,
zero added/removed warning identities, 195 packages and 197 HTML pages.
All 1,268 original declaration snippets retained byte-exact escaped text, and
all 2,456 links on 168 pages retained exact markup and ordering against a saved
baseline. The final validator found no broken local links/anchors/assets or
highlighting errors. Repeated theme/highlighting processing preserved hashes of
every generated file. Fresh fixture generation was also byte-identical.
The 21 new tests, 21 original cross-reference tests and 26 warning tests passed.
Executable library/test inputs did not change; existing AUnit evidence is reused.

Firefox 153.4.0esr headless screenshots were captured and inspected: landing at
1440px; native browser at 1440/768/375px; Core at 1024px light and 375px dark;
all nine requested representative packages at 768px dark. The UInt8_Access
declaration shows colored keywords, underlined atomic type links and parameter
spacing; target borders/backgrounds are visible. These are static screenshots,
not automated interaction qualification: keyboard focus, actual clicking within
the iframe and horizontal scrolling were structurally checked, not exercised
with browser input. Some long pages' screenshots show only their initial entity
lists. The final semantic/link validator covers all their declarations and anchors.

## Automatic declaration type cross-references (CORE-DOC-069)

The existing GNATdoc package/entity navigation is unchanged. A separate,
standard-library Python enhancement adds ordinary, keyboard-accessible,
underlined HTML links **inside Ada declaration snippets**, not comments or
prose. It runs automatically after warning-baseline comparison and landing-page
installation, before final site validation. Failure prevents artifact upload
and Pages publication; the existing main-only deployment restrictions remain.

### Research gate and native output contract

Inspection of the installed GNATdoc **26.0.0 (20260415)** executable and its
bundled source established that its CLI offers HTML, ODF and RST, not an XML
backend. The HTML backend's only extra CLI option is OOP grouping. Its entity
proxy's `code` value is a string from `Get_Ada_Code_Snippet`, not a token stream
with reference identities. `Resources_Dir` permits template customization but
does not add semantic information to that string. Libadalang is used internally
by GNATdoc; its Python binding is not supplied in this documentation environment.
Using a locally cached Ada library would not make that binding available in CI
without an additional dependency. The publication pipeline and templates have
therefore not been replaced or patched.

Actual output has one native `<h1>` package heading and adjacent
`<h4 id=...>Name</h4><pre class=ada-code-snippet><code>...</code></pre>`
sections. Types, subtypes, records, arrays and access types retain their source
declaration text and terminating semicolon. Subprogram snippets omit the final
semicolon and aspects; overloads have distinct native anchors. Generic formal
types have sections but are not ordinary public type targets. Generic instances
(for example `OpenCV.Core.UInt8_Vec3`) have package pages with no independently
rendered `Vector` declaration anchor. Those instance references remain unlinked;
linking them to the generic foundation's `Vector` would be misleading.

### Bounded source-backed resolution

`scripts/link_gnatdoc_types.py` discovers filenames and anchors from actual
generated HTML, indexes type **and subtype** declarations by complete,
case-insensitive package identity, and matches every rendered profile to a
unique declaration in the current public specification. Hashed filenames and
native anchors must **never** be synthesized or hardcoded. Source files are
read-only inputs; no Ada source, installed template or generated file outside
the API site is modified.

Eligible positions include function/procedure parameters (multiple names, modes,
aliased and anonymous access forms), nested access-to-subprogram profiles,
function results, array element types, subtype bases, derived bases and named
access designated types. Record component type marks also qualify. Original
identifier spelling, whitespace, punctuation and entity escaping are retained.

Resolution checks the current package's earlier declarations, then lexical
parent packages, then unambiguous context-clause `with`/`use` visibility. A
non-type declaration or generic formal blocks lookup rather than falling through
to a namesake in a parent. Parameter/discriminant names conservatively block
potentially shadowed references, including nested profiles. Full qualified names
are eligible only when their owning package is a lexical scope or an explicit
context import. There is no global short-name replacement dictionary.

This is intentionally **not a complete Ada semantic resolver**. Generic formal
types, generic instance members without native anchors, external language/library
types, unknown names, ambiguous imports, attributes and constraint/default
expressions remain plain text. Nested packages, package renamings, task/protected
scopes and local package-use clauses disable resolution for the affected package;
they require a fuller semantic model. Unqualified imported types are linked only
when exactly one explicitly imported, published package supplies the declaration.
Comments, string literals, subprogram/parameter names, enumeration literals and
ordinary prose are not link opportunities. Internal packages are forbidden.

### Integrity and reproduction

The generated `api/type-crossrefs.json` records original snippet HTML and hashes
of all non-snippet HTML. It contains no filesystem paths or private source text.
The enhancer validates every input and planned replacement before writing.
Validation independently rediscovers native type targets and recomputes expected
links from source profiles, not from the link's `data-type` assertion. Thus
redirecting `Mat` to the real anchor for `UMat` fails even though both anchors
exist. Original snippets must strip back to byte-identical HTML, stronger than
visible-text equivalence. All headings, anchors, prose and navigation outside
snippets must hash identically. Exact markup comparison rejects nested/duplicate
links, malformed links, non-relative destinations and missing links. Existing
site link/asset and full-profile overload checks still run.

```sh
python3 -m unittest discover -s scripts -p 'test_link_gnatdoc_types.py' -v
python3 -m unittest discover -s scripts -p 'test_compare_gnatdoc_warnings.py' -v
sh scripts/generate_docs.sh
python3 scripts/link_gnatdoc_types.py _site/api --check
python3 scripts/link_gnatdoc_types.py _site/api  # idempotent second pass
python3 scripts/validate_docs.py _site
```

The scripts print linked, ambiguous and unsupported opportunity counts plus
counts by type family. Qualification enforces at least 500 verified links across
100 public package pages; it does not count all textual identifier occurrences
as opportunities. CORE-DOC-069's inspected output contains 1,268 snippets across
195 public package pages (197 HTML pages including indexes/landing page).
Local qualification produced **2,456 links on 168 pages**: Mat 969, UMat 159,
Index_Array 166, Buffer_Array 320, Dimension_Array 136 and Float16_Value 20.
Three conservatively shadow-blocked and 822 unsupported candidates remained
unlinked. All 21 cross-reference tests and 26 existing comparator tests passed,
including wrong-real-anchor and nonexistent-page/anchor negative controls.
The full generator reported zero warnings and a zero added/removed baseline
delta. A second enhancement pass preserved every site file's SHA-256 exactly.
Unexpected GNATdoc structure, conflicting type identities, duplicate anchors,
unmatched source profiles or integrity failures stop generation explicitly.
After a GNATdoc format change, update and requalify the parser and realistic
fixtures; do not bypass the failure or silently choose a package-level target.

## Reproduce on Linux — pinned generation environment

Required qualification versions:

| Tool | Release / executable version |
| --- | --- |
| Alire | 2.1.1 |
| GNAT Native | Alire `gnat_native=16.1.0`, executable GNAT 16.1.0 |
| GPRbuild | Alire `gprbuild=26.0.1`, executable 26.0.0 (2026-04-15) |
| GNATdoc | Alire `gnatdoc_bin=26.0.0`, executable 26.0.0 (20260415) |

Also install a supported native OpenCV development library, pkg-config,
a C++ compiler, POSIX shell and Python 3.9 or newer (standard library only).
The authoritative OpenCV compatibility policy is in the
[README](../README.md). Local qualification used OpenCV 4.10.0; documentation
CI uses Ubuntu 24.04's native OpenCV package. No documentation or testing
dependencies are added to the library manifest.

```sh
alr -n --force toolchain --select gnat_native=16.1.0 gprbuild=26.0.1
sh scripts/generate_docs.sh
```

Run from a checkout; the script itself locates the repository root. It installs
the pinned binary GNATdoc crate into `.doc-tools/gnatdoc-26.0.0` when absent.
Alire verifies the binary archive against the index's SHA-256. An existing
installation can be reused without reinstalling:

```sh
GNATDOC_PREFIX=/tmp/doc-001-gnatdoc-26 sh scripts/generate_docs.sh
```

The script builds `opencv_core.gpr` through Alire to resolve dependencies and
generate its normal supported configuration. It then invokes:

```sh
alr exec -- "$GNATDOC_PREFIX/bin/gnatdoc" -P docs_api.gpr \
  --backend html --generate public --style leading --warnings -O "$PWD/_site/api"
python3 scripts/validate_docs.py _site
```

`docs_api.gpr` uses production compiler switches, publishes only `src/`, and
excludes the configuration and `docs_internal.gpr` projects. Internal sources
remain available to Libadalang for resolution. These projects do not import
the production project: importing it while redeclaring its public sources
would violate GPR source ownership. The normal library projects, ABI, source
comments and dependencies are unchanged. Tests and applications are not
built for documentation generation.

Output is deleted before each generation. Full diagnostics are retained in
`obj/docs/gnatdoc.log`, not published. `--warnings` stays enabled. Generation
errors, partial-generation diagnostics, absent public package pages, and broken
local links fail the build.

Historical documentation warnings are measured, not suppressed. After a
successful GNATdoc run, `scripts/compare_gnatdoc_warnings.py` compares
`obj/docs/gnatdoc.log` with `docs/gnatdoc-warning-baseline.txt`. The baseline
stores one identity per warning:

```text
filename: enclosing scope: normalized declaration signature: warning: message
```

The signature is the complete Ada declaration with comments removed and
whitespace normalized. A semicolon inside a parameter list does not end it, so
a function identity keeps its return profile. The enclosing scope is the
package, nested package, generic formal, or record that contains the
declaration. Two identical profiles in different scopes, and two record
components with the same name, remain different warnings. Source line and
column numbers are used only to find that declaration in the current `src/`
tree. A pure line shift, comment edit, or reordering of the log matches. A warning that moves
from one declaration to another is an addition and fails the build, even when
the filename, column, and message text are unchanged.

Every warning must map to exactly one declaration. An unmapped location, two
declarations with the same normalized profile, or a warning-shaped diagnostic
that is not the pinned GNATdoc 26.0.0 `file:line:column: warning:` form fails
the comparison. Ordinary non-warning log text is ignored. Removed warnings are
printed and do not fail the build. Do not silence a warning with `@exclude`,
an empty comment, or a changed generator invocation.

## Current documentation status

Milestone PRs [#65](https://github.com/zackboll/opencv_core_ada/pull/65),
[#66](https://github.com/zackboll/opencv_core_ada/pull/66) and
[#67](https://github.com/zackboll/opencv_core_ada/pull/67) are merged and complete
the public API documentation campaign:

- **Zero GNATdoc warnings**, with `--warnings` enabled.
- **Empty structured warning baseline**; qualification reports zero added and
  zero removed warning identities.
- **195 public packages**, **197 generated HTML pages**, including the API index
  and documentation landing page, with validated local links and assets.
- [Published API reference](https://zackboll.github.io/opencv_core_ada/api/index.html)
  and [Documentation Home](https://zackboll.github.io/opencv_core_ada/).

Historical inventories, qualification details and obsolete cleanup plans are
retained in [the campaign record](gnatdoc-campaign-progress.md), not as current
instructions. A zero warning count is not a proof of semantic correctness.

The empty baseline is a regression gate, not permission to accept new warnings.
Do not rewrite it to bless a documentation regression. When an intentional,
reviewed baseline change is needed, derive identities from a complete pinned
GNATdoc 26.0.0 log and the sources of that same revision:

```sh
python3 scripts/compare_gnatdoc_warnings.py --write-baseline \
    docs/gnatdoc-warning-baseline.txt obj/docs/gnatdoc.log
```

Do not replace the baseline with a raw log: source line numbers do not remain
attached to the same declaration after comment edits.

### GNATformat and generic-instance comments

The approved PR #66 interaction affects **25 generic-instance specifications**:
the 24 `opencv-core-<type>_vec{2,3,4}.ads` files and
`opencv-core-float32_matx3x3.ads`. GNATformat inserts a blank line between the
leading package comment and instantiation; GNATdoc 26.0.0 then drops the comment.
Those specifications retain the GNATdoc-valid adjacent leading comment form.
This is a narrow, documented formatting conflict, not a general formatter
exemption. Keep normal GNATformat checks for other specifications, review these
25 explicitly, and continue running GNATdoc with warnings and the unchanged
structured comparator. Do not weaken either tool or change generator options
to hide the conflict.

### Rendering and overload checks

`validate_docs.py` now checks these APIs per overload. Sections are keyed by
the complete normalized declaration and by native GNATdoc anchor, never by
the bare name, so one overload's text cannot satisfy another overload's
check; the leading prose, `Parameters` and `Return Value` text are each
required inside the correct section. The older simplified section key used
for type declarations is unchanged and is not used for overloaded operations.

GNATdoc 26.0.0 limitation observed: enumeration literals and record
components are documented from the type's leading block with `@enum` and
`@field`. The same block documents discriminants and variant components of a
discriminated record; each appears under "Record fields" and the prose must
state which variant component exists, because GNATdoc does not render the
variant condition beside the field.

## Coverage and qualified limitations

The current build documents all 195 public specification packages, including
`OpenCV`, `OpenCV.Core`, `Transfers`, `Persistence`, `Sparse`, typed scalar/vector
access, row/buffer access and scoped views, and the fixed-matrix/vector generic
foundations and instances. `Mat`, `UMat`, `Sparse_Mat`, arithmetic and matrix
operations are present. Public module-interoperability packages in `src/` are
intentionally included; unsupported `OpenCV.Internal` units and generated
configuration are excluded. Private completions, bodies and C/C++ files are
not published.

GNATdoc 26 parses this repository's Ada 2022 declarations, controlled public
views, overload signatures, discriminated records and generic formal parts.
GNATdoc 26.0.0 attaches documentation for enumeration literals through
`@enum` (`@value` is not recognized) and for generic formals through `@formal`
in the generic unit's leading comment block. Tested arrangements: `@formal`
alone clears the generic-formal warning but its text is not rendered anywhere
on the page; adjacent leading comments on the individual formals alone render
under each formal's heading but leave the warning; both together clear the
warning and render under each formal. The generic units therefore use both, and
`validate_docs.py` checks the formal descriptions on the intended package
pages. Overloads have distinct native anchors. Native GNATdoc generic-instance
pages contain introductions but no instantiated members or template links;
CORE-DOC-070A adds explicitly labeled source-backed summaries.
The native index provides a flat, fully qualified compilation-unit list and
tagged-type links, not a collapsible hierarchy. Package filenames are native
hashes; do not depend on handwritten package filenames. Package coverage is
checked against actual specifications, not a fixed count.

Generation uses **leading** comments. The completed campaign documents the
public declarations in that style; comments must remain adjacent to the intended
entity. Validation checks package coverage and representative rendering separately
from warning identities. Neither zero warnings nor those checks prove that every
comment or cross-reference is semantically perfect.

GNATdoc `--version` prints to stderr and exits 1 in this exact release; version
checking handles that quirk explicitly. Generator execution must still succeed.
Local URL validation checks file references and HTML anchors, including native
CSS, and rejects filesystem/root-absolute local links so repository-relative
hosting works. External website availability is not tested. No custom JavaScript,
analytics or second documentation generator is used.

## Comment convention for future PRs

Use adjacent **leading** `--` comments for new public declarations. Do not
insert a blank line between a documentation block and its declaration. Use
GNATdoc's `@param`, `@return` and `@exception` annotations where appropriate;
names must match the actual Ada declaration. For example:

```ada
--  Return an independent copy of the source matrix.
--  @param Self Source matrix, borrowed for this call.
--  @return A matrix with independent pixel storage.
--  @exception OpenCV_Error Native allocation or OpenCV failure.
function Clone (Self : Mat) return Mat;
```

For every new API, describe package purpose, parameter units/ranges, result
meaning, exceptions and rejection conditions. State ownership and lifetimes,
including `Mat`/`UMat`/`Sparse_Mat` assignment aliasing versus explicit deep copy,
view/callback lifetime restrictions, overlap restrictions and native-library
safety limitations. Document relevant OpenCV version constraints and examples
when helpful. Do not imply that native failures provide rollback unless the
API promises it. Preserve existing comments; migrate only focused comments
when reviewing the affected API. A new public declaration must not add a
GNATdoc warning: the documentation workflow fails when the warning baseline
grows. Generate documentation and inspect rendering in the PR artifact. The
specification remains the source of truth, not a second handwritten API manual.

## CI and Pages review gate

`documentation.yml` runs for PRs targeting main, pushes to main, and manual
dispatch. PR jobs have only `contents: read`, generate and validate the site,
and upload a review artifact plus diagnostics. They never configure or deploy
Pages and do not receive Pages/OIDC write permissions.

Only trusted `refs/heads/main` runs upload a Pages artifact. A separate job,
dependent on successful generation, uses `actions/deploy-pages` with
`pages: write`, `id-token: write`, and the `github-pages` environment. Main runs
share a cancel-in-progress concurrency group so superseded publication runs
are cancelled. Manual runs on other branches can validate but cannot publish.
No PAT or `gh-pages` branch is needed.

Pages must use **Settings → Pages → Build and deployment → Source: GitHub
Actions**, with the `github-pages` environment allowing **main only**. The site
was deployed after PR #67. CORE-DOC-068 checked the direct API URL and received
HTTP 200; `docs/index.html` links to `api/index.html` and the workflow publishes
`_site/` at the repository-relative `/opencv_core_ada/` route. Feature-branch
qualification is not evidence of a new public deployment. The five approved
developer guides are rendered into `_site/guides/`; other repository Markdown
documents remain source links on GitHub.

### Published developer guides (DOC-072)

The authoritative sources are `ownership-and-views.md`, `typed-access-guide.md`,
`core-operations-guide.md`, `sparse-and-persistence-guide.md`, and
`interop-and-compatibility.md`. Their HTML pages augment the 197 existing pages,
giving 202 total; all 195 native package pages remain unchanged.

Install the documentation-only renderer in an isolated environment:

```sh
python3 -m venv .doc-tools/markdown
.doc-tools/markdown/bin/pip install -r docs/requirements.txt
export DOC_PYTHON="$PWD/.doc-tools/markdown/bin/python"
sh scripts/generate_docs.sh
"$DOC_PYTHON" -m unittest discover -s scripts -p 'test_*.py' -v
"$DOC_PYTHON" scripts/validate_docs.py _site
```

`markdown-it-py==3.0.0` and `mdurl==0.1.2` are exact documentation-only pins;
they are not Alire dependencies or browser runtime dependencies. The generator
rejects raw HTML, malformed fences, unsafe schemes, missing source destinations,
and invalid fragments. Native package destinations are discovered from generated
headings and checked against public Ada specifications. Duplicate source headings
receive stable GitHub-style suffixed identities; generated IDs remain unique.

The final validator independently reconstructs expected pages from Markdown and
checks exact HTML and stylesheet bytes. It does not trust a generated manifest.
All fenced code remains escaped with original indentation and newlines. Wide
tables and code scroll locally; guide navigation needs no JavaScript. Optional
Chrome qualification uses `scripts/test_gnatdoc_guides_browser.cjs` with an
externally installed Playwright module specified by `PLAYWRIGHT_MODULE`.

## Building, testing and contributing

For native prerequisites, library kinds, platform-specific C++ toolchains and
installed consumers, see the
[build guide](interop-and-compatibility.md#building). To qualify the public API:

```sh
alr build
alr test
python3 -m unittest discover -s scripts -p 'test_compare_gnatdoc_warnings.py' -v
sh scripts/generate_docs.sh
alr exec -- gprbuild -P docs/example.gpr
obj/docs-example/example
git diff --check
```

Tests and verification tools remain owned by the separate `tests` crate. Work on
a feature/corrective branch, keep each change cohesive, qualify the exact head,
and open an unmerged PR against `main` with auto-merge disabled. Follow
[the contribution policy](interop-and-compatibility.md#contributing) and the
repository `.clinerules`. Do not commit generated HTML or add development-only
dependencies to the public library.

## Historical DOC-001 qualification

This initial record predates the completed campaign above.

Starting main: `e0d505103fd69a16b863f409c7c451ac5bce993c` (PR #57 merge).
The existing compatibility workflow succeeded on that exact SHA.

Commands run in the isolated DOC-001 worktree:

```sh
alr -n build
alr -n test
GNATDOC_PREFIX=/tmp/doc-001-gnatdoc-26 sh scripts/generate_docs.sh
python3 scripts/validate_docs.py _site
sh -n scripts/generate_docs.sh
alr exec -- gnatformat --check -P docs/example.gpr docs/example.adb
alr exec -- gprbuild -P docs/example.gpr
obj/docs-example/example
git diff --check
```

The existing build succeeded; AUnit reported 2024 successful tests, zero failed
assertions and zero unexpected errors. Generation produced 195 public package
pages, a native API index and CSS (197 HTML pages including the landing page).
All local links/anchors/assets resolved. No production source, test source,
production project, dependency or release metadata was changed.
The landing-page example was compiled with assertions and warnings-as-errors
and executed successfully. ShellCheck 0.11.0 and actionlint 1.7.12 validated
the script and new workflow; GNATformat 26.0.0 formatted the example.
A copied-site negative test with `api/gnatdoc.css` removed was correctly
rejected with missing-asset and broken-link errors. Generated HTML was scanned
for local filesystem paths and common credential markers; none were found.
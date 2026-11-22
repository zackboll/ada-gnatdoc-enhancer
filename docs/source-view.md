# Optional offline Ada source browser

Source browsing is **disabled by default**. Existing configurations produce
exactly the same publication bytes. It requires no JavaScript, runtime Python,
network service, GitHub source URL, font download or CDN.

## Visibility and scope

Enabling this feature deliberately publishes the **entire original `.ads`
file**, including comments and any **private section inside a public package
specification**. It does not redact that section or claim the text is public-only.
Review specifications for confidential material before enabling it.

Only public library package specifications independently discovered in the
configured source directories are eligible. Schema 1 excludes `.adb` files;
schema 2 additionally authorizes complete bodies of eligible packages. Neither
mode publishes arbitrary repository files, private library units or unselected
dependencies. The existing conservative Ada inventory and exact native
profile reconciliation authorize type, subtype, function and procedure links,
plus existing supported constant identities. Unsupported declarations receive
no guessed link. Package headings have package-level links. Overloads retain
their distinct native anchors and actual declaration-token source lines.

## Configuration and reviewed input evidence

The versioned contract is strict; all four fields are required:

```toml
[source_view]
schema_version = 1
mode = "public-specifications"
native_manifest = "docs/source-native.json"
native_manifest_sha256 = "<SHA-256 of the reviewed input evidence>"
```

`native_manifest` is a project-relative, source-owned input, **not**
`api/presentation.json`. Its schema-1 JSON has `files` (complete pristine native
API HTML/CSS SHA-256 inventory) and `sources` (complete eligible specification
SHA-256 inventory). Paths and hashes are exact, case-sensitive identities.
Pinning both inputs prevents a resealed output manifest from authorizing
substituted source, wrong native anchors or swapped overload destinations.

Before adding the opt-in table, acquire pristine GNATdoc **26.0.0** output and
record its identity with the shipped source-distribution utility:

```sh
python /absolute/enhancer/scripts/pin_source_view.py \
  --source-root /absolute/project --config docs/gnatdoc-enhance.toml \
  --site /absolute/pristine-site \
  --output /absolute/project/docs/source-native.json
```

Independently review the input acquisition and evidence; commit the JSON and its
printed hash in configuration. Do not generate authorization from an enhanced
publication. Regenerate/review the pin after changing source or native input.
Then use the normal enhance/verify commands with the opt-in configuration.
No original Ada file or pristine acquisition is edited. As with existing
enhancement, the publication copy of native HTML receives bounded insertions.

### Opt in separately to specification and body browsing

```toml
[source_view]
schema_version = 2
mode = "public-specifications-and-bodies"
native_manifest = "docs/source-native-bodies.json"
native_manifest_sha256 = "<SHA-256 of independently reviewed schema-2 evidence>"
```

This mode publishes the **whole original `.adb`**, not just implementations of
public declarations. Private helpers, algorithms, comments and any sensitive
material in the file become public. Review every complete file and its
redistribution terms before enabling this mode. If you cannot publish all
eligible bodies in the configured source selection, use schema 1 or a separately
reviewed, appropriately scoped input tree. A bodyless public package is allowed.

Generate a new pin with `pin_source_view.py --schema-version 2` and the same
arguments as above, using a configuration without `[source_view]`. Do not
overwrite the old pin or re-seal an enhanced publication. The schema-2 evidence
has exactly five fields: `schema_version` (integer `2`), `mode` (the exact string
above), `files` (pristine native API HTML/CSS paths to SHA-256), `sources` and
`bodies`. The latter two objects map complete canonical project-relative `.ads`
and `.adb` paths, respectively, to objects with exactly `package` (the exact
specification spelling) and `sha256` (lowercase SHA-256 of the original complete
file bytes). They are inventories, not body allowlists: verification discovers
the eligible set again from the tree and requires exact agreement. Filename
stems do not determine ownership. Unknown fields, encoded paths, symlinks,
duplicate or case-colliding paths/owners and cross-directory ownership fail.

Each configured directory is a nonoverlapping ownership domain. The first
library declaration in an eligible body names an ordinary public package
selected by the specification and native inventories in the same domain.
Generic library templates, package renamings, instances, stand-alone subprograms
and separate subunits do not authorize `.adb` publication. If an eligible
body's complete single-unit boundary cannot be established (e.g. an unsupported
statement or a second compilation unit), publication fails closed.

## Layout and navigation

For `ada/src/ams-mel-ir-image.ads`, the static page is
`api/source/ada/src/ams-mel-ir-image.ads.html`. Native declaration headings gain
a small **View source** link. `AMS.MEL.IR.Image.Navigation_Report`, for example,
opens that file at `#L663`; `Submit_Navigation_Report` opens at `#L775` in the
retained MEL qualification input. These are qualification examples, not fixed
counts or promised locations for future revisions.

In schema 2, native headings instead say **View specification** and, when there
is a verified destination, **View body**. Types and subtypes have specification
links only. Both source pages link to the corresponding package heading. The
**Corresponding operations** list pairs line-numbered declarations and bodies
in both directions without adding text inside the source `<code>` element.

### How body destinations are established

This is a conservative lexical subset of Ada 2022 RM 6.3 and 6.3.1, not a
compiler or general Ada name resolver. Review and compile the same production
sources independently. A link requires one direct, complete same-package body
with matching callable kind, defining name, parameter names, order, modes,
supported subtype and result identities, and defaults. Omitted `in` and explicit
`in` are equivalent. Named defaults, anonymous access profiles, constraints and
other unproven conformance rules are not guessed. Only integer literal defaults
with matching spelling and resolved subtype are supported. Known Standard and
directly owned type marks can be matched in selected and bare notation when
their binding is established. Unresolved aliases, use visibility and possible
shadowing are not treated as name equivalence. Overloads match independently of
the order in either file. Duplicate, unresolved or otherwise ambiguous candidates
do not win by position.

There is no operation body link for abstract, imported/intrinsic, renamed,
instantiated, null or expression-only operations; for nested/protected/task or
generic operations; or when the supported profile/scope rules cannot establish
correspondence. `is separate` is only a stub (RM 10.1.3): neither it nor an
unverified subunit is an implementation destination. Package-level browsing
remains available when operation links are omitted. The schema-2 publication
manifest records a `body_omission` reason for native-backed callables without
links, or `body_source` and `body_line` for verified destinations.

Links leave the native iframe for a directly addressable static source page;
browser Back returns to the API. Every physical line has a stable `#L1`, `#L2`,
etc. Keyboard-focusable line links expose their line number accessibly. Displayed
numbers are CSS-generated, not source text, and do not contaminate copied code.
The layout supports narrow screens and system light/dark color preferences.

The complete UTF-8 source, indentation, tabs, LF or CRLF and missing final newline
are preserved in the code element's DOM text and independently tested. HTML
character references preserve CR without HTML newline normalization. Browser
clipboard/OS newline conversion is outside this byte-identity guarantee. Invalid
UTF-8, NUL, bare CR, unsafe path characters and symlinked input trees fail closed.

## Static Ada syntax highlighting

Source pages reuse the existing presentation setting (enabled by default):

```toml
[presentation]
syntax_highlighting = true
```

This setting does not enable source browsing: the separately reviewed
`[source_view]` input evidence above is still required. Set
`syntax_highlighting = false` to render plain-text source HTML in either mode.
Highlighting has no separate flag and cannot authorize body browsing.

The existing display-only Ada lexer styles reserved words (case-insensitively),
comments, strings (including doubled quotes), character literals, numeric
literals (including based literals and underscores), attributes and operators.
Ordinary identifiers, whitespace and unclassified text remain unstyled. Unicode
identifiers and all original decoded UTF-8 text are preserved, including trailing
spaces, blank lines, CRLF and terminal-newline presence or absence. Token text
reconstruction and the complete code element's `textContent` equal the original
source; highlighting never normalizes or edits it. Source text is always escaped
before insertion into fixed token spans; it cannot introduce HTML or links.

The standalone source stylesheet uses the normal GNATdoc light/dark Ada palette
without requiring the main theme stylesheet. Active fragment targets use paired
system highlight colors, overriding nested token colors for readable contrast.
The static HTML/CSS works with JavaScript disabled, offline, without remote
resources or browser-side highlighting dependencies.

This is lexical display, not compiler-semantic classification or Ada validation.
Unrecognized/malformed constructs remain literal text; lexical categories may be
approximate for unsupported Ada syntax. It adds no type-reference hyperlinks,
compiler/Libadalang dependency, declaration mappings or ownership authority.

## Verification and compatibility

The publication manifest records ownership, source hashes, line counts and
declaration/anchor/line correspondence. Verification reconstructs all pages and
links from source and pinned native evidence, then compares exact output bytes
and the complete inventory. Output-side digests do not authorize themselves.
Only the exact reconstructed source markup is admitted; no blanket HTML,
`data-*`, scripting or URL permission is introduced. Malicious comments remain
inert source text. Existing native anchors, search, navigation, bookmarks,
guides, examples and theme assets are unchanged by this opt-in.

The qualification utility records complete disabled/enabled publication hashes
and the compatibility delta for retained official GNATdoc MEL/Core fixtures,
without freezing source-page counts in the product contract. A dedicated hosted
Chromium job covers both configurations and the mandatory Navigation Report
journey. Retained fixtures do not represent a new GNATdoc/compiler execution.

Absence of `[source_view]` and the schema-1 source/native contract remain
unchanged. Source navigation is static and relative in both modes.
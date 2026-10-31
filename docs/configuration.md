# Configuration

## Opt-in Ada example presentation (GNATDOC-027)

Configuration schema 1 adds three strict Boolean fields under `[guides]`:
`ada_example_highlighting`, `ada_example_api_links`, and
`ada_landing_example_highlighting`. All default to false and require
`mode = "authored-markdown"`; API links require example highlighting.
See [Ada examples](ada-examples.md) for the complete public contract, source/native
link evidence, conservative ambiguity rules and exact landing-example checks.

## Documentation search (GNATDOC-023, unreleased opt-in)

```toml
[search]
schema_version = 1
mode = "documentation"
```

Requires enabled navigation. Adds a version-one deterministic index and scoped
results stylesheet; no existing consumer is opted in automatically. See
[documentation search](documentation-search.md) for source/native authorization,
coverage, static hosting, keyboard controls, limits and verification contracts.

## External symbol bookmarks (GNATDOC-018R1, development opt-in)

Ordinary `[external_types]` still requires explicit HTTPS native page/fragment
destinations without queries. Selected destinations can additionally use a
separately reviewed, hash-bound publisher record:

```toml
[presentation]
external_type_target = "_top"

[external_types]
# Keep the existing independently verified native page/fragment mappings here.

[external_symbol_bookmarks]
qualification = "docs/qualified-core-symbol-bookmarks.json"
sha256 = "<SHA-256 of independently approved qualification record>"
types = ["OpenCV.Core.Mat"]
```

The illustrative digest must be replaced by the approved record's actual hash.
The type list is nonempty, unique ignoring case, and requires exact source
spelling. A record cannot introduce a selected type without its matching direct
native destination. Unselected mappings remain direct: mixed policies are valid.
The only supported protocol is `core-symbol-router-v1`, not arbitrary queries.

The strict JSON record contains `schema_version=1`, `profile`, allowlisted HTTPS
`base_url` ending `/api/`, `acquisition={path,sha256}`, `source`, `native`,
`publication`, complete `publication_sha256`, `router_source`, `provenance` and
`artifacts`. Paths are relative to the source root. `acquisition` uses the existing
source/native dependency input specification. `provenance` has hash-bound JSON
`{path,sha256}` references for `run`, `deployment`, `statuses`, and `artifacts`:
archived GitHub workflow, Pages deployment, statuses wrapped as `{"statuses": [...]}`,
and artifact-list API observations. `artifacts` identifies `review` and `pages`,
each with exact `id` and GitHub `sha256:...` digest. Source/revision, successful
workflow/deployment and artifact membership must cross-check. These unsigned
records need independent approval; they cannot authenticate their own origin.

Enhancement and verification recheck all local evidence without network access.
The complete symbol index is rebuilt from source/native authority, not accepted
from HTML or presentation metadata. Router bytes must match the qualified protocol
fingerprint and approved source. A new router implementation requires separate
toolkit qualification, even if it preserves symbol names. Acquisition may not
import further bookmarks. No new Ada resolver or consumer-specific identity is
introduced. Generic-formal/private/unsupported identities cannot become targets.

Canonical URLs are constructed as `index.html?package=<source owner>&symbol=<source
qualified name>`, exactly that order with no encoding, extra key or fragment.
Only reconstructed exact URLs receive query permission; malformed, duplicate,
encoded, conflicting or substituted URLs fail verification. A rehashed output
manifest does not authorize a changed destination.

Remove the entire opt-in table and regenerate from independently retained pristine
native input to roll back to direct mode. Do not edit an existing enhanced site's
manifest to change policy. JavaScript-disabled precise selection requires direct
mode. A mutable publisher update requires new independent source/native,
artifact/deployment/router and full-inventory live qualification before approving
new record hashes. The library never silently fetches or accepts live changes.

# Source-verified consumer theme (GNATDOC-017, development opt-in)

Omitting both options retains the bundled default theme and the exact v0.1.1
publication/manifest bytes. To preserve an established consumer presentation,
add both fields to the existing presentation table. Real Core example, pinned
to source `33a2a4f3b83606a5c779b8a93abeb6c91fa49a21`:

```toml
[presentation]
theme = true
theme_css_source = "docs/assets/gnatdoc-theme.css"
theme_css_sha256 = "fa265d63e73436a6a449fd16011c3db68a5430e7fa6a98ea8eb0fd6821dca9b2"
```

The source path is relative to `--source-root`, **not** to the TOML directory.
It must name a regular file through canonical relative path components: no
absolute/drive paths, traversal, encoding, symlinks (including ancestors/root)
or outside-root resources. Both fields are mandatory together; `theme = false`
is incompatible. SHA-256 must be exactly 64 lower-case hexadecimal characters,
independently reviewed against the complete original source bytes. Never copy
an output-manifest hash into configuration as an approval procedure.

Enhancement and `verify` independently read source/configuration, check identity,
validate CSS and reconstruct the original approved bytes at `api/gnatdoc-theme.css`.
The existing relative HTML links are unchanged. No sanitizer, substitution or
newline normalization is applied. UTF-8 only (no BOM or encoding directives);
imports, URL/resource functions (including string-form image sets), local font
loading, executable constructs, escapes and unsupported controls are rejected.
Variables, media queries, pseudo-classes and Core's target/card rules are allowed.
There are no new runtime dependencies, remote downloads, scripts or inline styles.

Only opt-in publications add `theme_source` identity metadata (source path/hash
and loaded configuration path/hash); this is an audit/check value, not authority.
Any CSS byte change, source-path substitution or configuration byte change after
enhancement requires a **new pristine build**, reviewed approval and fresh
verification. Retain independently approved configuration/source identities;
the manifest is not a signed attestation against an attacker replacing *all*
trusted inputs and output metadata together.

Do not confuse the theme with native `api/gnatdoc.css` (always preserved), the
separately hash-approved authored guide stylesheet (e.g. Core's
`guides/gnatdoc-guides.css`), or source-owned landing HTML. Custom CSS changes none
of their bytes, nor navigation, native declarations, anchors or summary routing.
It does not enable authored guides or generic summaries; configure those existing
features independently. Consumer CSS is not bundled in the toolkit wheel.

**Rollback:** remove both custom fields, keep `theme = true`, regenerate from
pristine GNATdoc inputs, then run `verify` and consumer/browser gates. Do not edit
published CSS or rehash presentation metadata to migrate an existing output tree.
Version remains 0.1.1 during development; adoption/release requires later review.

# Opt-in stable public symbol bookmarks

Package navigation may explicitly enable source/native-verified type/subtype
bookmarks:

```toml
[navigation]
mode = "packages"
symbol_bookmarks = true
default_package = "OpenCV.Core"
```

Disabled by default. A verified default package is mandatory with this option;
it is rejected without the option. Categories and other navigation modes are
incompatible. Unknown keys remain errors. See
[stable public symbol bookmarks](stable-public-symbol-bookmarks.md) for query
rejection rules, authority boundaries, unchanged default bytes, and the current
**partial Core migration** disposition.

GNATDOC-011R1 separately adds `[generic_instances].incoming_references = true`.
It requires the hash-qualified generic-instance record, `type_links = true`, and
symbol-enabled package navigation. It defaults to false and does not expand
native-symbol bookmark eligibility. See the corrective section of the same
document for the 25-instance boundary and explanatory history URL contract.

# Authored-content opt-in

`guides.mode = "authored-markdown"` and `"authored-html"` require `manifest`
and its reviewed `sha256`. They do not change `mode = "none"` or the original
original guide modes. The schema-2 contract binds explicit sources, canonical
output paths, guide identities/order, stylesheet bytes, verified native input
hashes, example ownership/build projects, and approved portal inputs.
Unknown/duplicate keys and unlisted publication inputs are rejected.

Full contracts and proof boundaries are documented in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/authored-guides-portal-compatibility.md`.
The Markdown documentation-only extra remains pinned to
`markdown-it-py==3.0.0` and `mdurl==0.1.2`.

# TOML configuration

Configuration is scoped to a consuming repository root. Paths are relative to
that root and validated against traversal and symlinks. Unknown keys fail.

```toml
schema_version = 1
project = "MyAdaLibrary"
[gnatdoc]
version = "26.0.0"
[sources]
directories = ["src"]
packages = ["MyAdaLibrary"]
comment_style = "leading"  # or trailing
[navigation]
mode = "packages"          # packages | operations | none
# categories = "docs/api-categories.json"  # operation mode
[presentation]
theme = true
syntax_highlighting = true
type_links = true
# external_type_target = "_top"  # opt in to leaving the API iframe
[guides]
mode = "none"              # html | markdown | none
# manifest = "docs/site-map.json"
[security]
external_hosts = []
```

A package profile with `sources.packages` requires **exactly** those packages;
an empty list allows discovery but still checks native h1 destinations against
actual Ada source files. Operation categories support the one-package Imgproc
shape or Geometry's `packages` array with per-package categories. Declaration
names must exist in observed native h4 headings; all overloaded destinations
are included, with no synthetic native anchors.

HTML guide mode consumes `docs/index.html` and a site manifest matching MEL's
schema, with canonical `docs/guides/{id}.html` source files. Only the literal
substitutions `{{navigation}}`, `{{package-directory}}` and
`{{package:Fully.Qualified.Unit}}` are allowed. To render optional Markdown,
install `.[guides]` and pin the exact renderer; see `guides.py` for the strict
source/example contract. The manifest cannot grant permission to add scripts
or arbitrary site assets.

`project` names the site in every generated document title (`OpenCV.Core —
MyAdaLibrary`, `API Reference — MyAdaLibrary`) and must be one line of visible
text. Markdown guide H1s must equal their site-map labels, which become their
titles. Author pages (`docs/index.html`, HTML guides, authored portals) must
carry exactly one title, a language and a UTF-8 charset; they are validated,
not rewritten. See `docs/html-page-metadata.md`.

Qualified cross-repository links may be defined with `external_types` using
complete, already independently verified HTTPS URLs including native fragment
anchors, and `security.external_hosts`. Do not guess an OpenCV Core HTML hash.
An explicit external URL is not proof of its target unless the consuming CI
qualifies that external site's exact revision independently.

### Opt-in top-level external type navigation (GNATDOC-014)

`[presentation].external_type_target = "_top"` adds the literal
`target="_top"` only to source-verified external type-reference anchors. This
applies equally to explicit `external_types` and qualified dependency mappings.
It does not add eligible type marks, bypass import/ownership checks, authorize a
host, verify external hosting, or enable production dependency manifests.

Omit the key to preserve v0.1.0 output **byte-for-byte**: no target attribute,
and external links clicked within the native API iframe stay in that iframe.
The only accepted explicit value is the string `"_top"`; empty strings,
`"_self"`, `"_blank"`, `"_parent"`, named frames, nonstrings and unknown keys fail.
Local links, native navigation, generic-instance explanation links, guides and
assets are unaffected. With `type_links = false` the setting has no output
effect. No JavaScript is required for top-level activation.

The opt-in exits the embedding frame and navigates the top document to the exact
allowlisted HTTPS page-plus-fragment URL. It intentionally does not convert that
destination into a package query or symbol bookmark. Browser Back returns to the
consumer shell; Forward returns to the external declaration. This is a consumer
navigation-policy choice, not blanket migration approval. Changing the setting
requires regeneration from pristine native output: an already enhanced tree is
verified against its original settings and is not silently rewritten.

The strict snippet grammar recognizes only the canonical optional literal
` target="_top"` after `data-type`. Independent publication reconstruction still
requires the exact source/config-derived bytes; valid grammar alone cannot
authorize a target on a local link or in a default publication. See
[qualification and evidence](external-type-target-navigation.md).

### Version-pinned dependency manifests (GNATDOC-005)

`[[external_dependencies]]` is an optional, backward-compatible alternative to
hand-entering `external_types`. It requires all of these fields:

| Field | Contract |
| --- | --- |
| `repository` | Exact repository identity in the reviewed acquisition |
| `revision` | Consumer's expected full immutable 40-character Git SHA |
| `manifest`, `manifest_sha256` | Root-relative type manifest and its independently reviewed SHA-256 |
| `acquisition`, `acquisition_sha256` | Root-relative acquisition record and independently reviewed SHA-256 |
| `source`, `site` | Root-relative original dependency source snapshot and pristine native site, containing `api/` |
| `types` | Nonempty array of explicitly selected fully qualified type/subtype identities |
| `base_url` | Explicit allowlisted HTTPS directory URL, including the full dependency SHA as a path segment |
| `publication` | Currently only `"offline-test"`; requires a reserved `.invalid` hostname |

All paths belong to the consumer configuration root; the native site is **not**
the consumer output directory. Hashes in project configuration are the trust
boundary: do not regenerate them automatically from unreviewed evidence. Every
enhancement and independent publication reconstruction checks the hashes,
reconciles the supplied source/native inputs, and requires the manifest to equal
the reconstructed inventory. There is no filename or fragment synthesis.

Keep `security.external_hosts` explicit. Selected identities cannot conflict
case-insensitively with explicit entries or other manifests. Unqualified names
do not gain external destinations. Source-owned local packages retain ownership;
public external references require ordinary visible package ownership, not
private/limited context clauses, aliases or generic-instance inference.

This first profile deliberately **does not enable production manifest URLs**.
Offline `.invalid` URLs are test publication mappings, not usable public links.
`verify_published` provides a separate explicit-fetch audit that rejects redirects
and requires exact pinned native HTML/CSS bytes; a deployment-owner stability
guarantee and reviewed production configuration profile remain adoption blockers.
Existing explicit HTTPS `external_types` remain supported with their existing
allowlist policy, but do not acquire manifest-level proof automatically.

See `/home/zboll/git/ada-gnatdoc-enhancer/docs/external-core-type-links.md` for
acquisition, replay commands, evidence, counts and publication limitations.

The only supported `renderer_exceptions` entry is the known
MEL `AMS.MEL.IR.Health_Status.Metadata.Status` package renaming. It remains a
**gap**, not documentation credit; the consumer's full coverage checker still
owns its evidence and approval.

The `qualify` subcommand accepts a reviewed JSON acquisition specification and
constructs this same TOML inside a new isolated workspace. Relative `--site`
paths still belong to `--source-root`; no consumer checkout is enhanced. See
`/home/zboll/git/ada-gnatdoc-enhancer/docs/real-site-qualification.md` for the
pinning, input hashes, public-source staging contract and non-certification
boundary of successful structural runs.

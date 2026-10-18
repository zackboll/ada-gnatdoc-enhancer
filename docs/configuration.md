# Authored-content opt-in

`guides.mode = "authored-markdown"` and `"authored-html"` require `manifest`
and its reviewed `sha256`. They do not change `mode = "none"` or the original
bootstrap guide modes. The schema-2 contract binds explicit sources, canonical
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

The only supported `renderer_exceptions` entry in the bootstrap is the known
MEL `AMS.MEL.IR.Health_Status.Metadata.Status` package renaming. It remains a
**gap**, not documentation credit; the consumer's full coverage checker still
owns its evidence and approval.

The `qualify` subcommand accepts a reviewed JSON acquisition specification and
constructs this same TOML inside a new isolated workspace. Relative `--site`
paths still belong to `--source-root`; no consumer checkout is enhanced. See
`/home/zboll/git/ada-gnatdoc-enhancer/docs/real-site-qualification.md` for the
pinning, input hashes, public-source staging contract and non-certification
boundary of successful structural runs.

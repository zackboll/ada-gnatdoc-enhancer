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

Qualified cross-repository links may be defined with `external_types` using
complete, already independently verified HTTPS URLs including native fragment
anchors, and `security.external_hosts`. Do not guess an OpenCV Core HTML hash.
An explicit external URL is not proof of its target unless the consuming CI
qualifies that external site's exact revision independently.

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

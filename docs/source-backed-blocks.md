# GNATDOC-036: bounded authored-HTML source blocks

This is an opt-in **schema-3 authored manifest**, not a template engine. The
configuration schema stays 1 and `guides.mode` stays `authored-html`. Existing
schema-2 manifests, profiles, HTML permissions and output bytes are unchanged.
There is no production consumer adoption or release in this change.

## API and input contract

Start with the complete schema-2 manifest described in
[authored guides](authored-guides-portal-compatibility.md), change its
`schema_version` to `3`, and add exactly this object (paths are illustrative):

```json
"source_blocks": {
  "profile": "executable-ada-catalog-v1",
  "manifest": "docs/examples/manifest.json",
  "project": "docs/examples/ams_mel_doc_examples.gpr",
  "guide": "guides/examples.html",
  "catalog_guide": "guides/api-map.html",
  "symbol_policy": "stable-public-types-and-root-constants-v1",
  "use_policy": "qualified-types-and-unique-operations-v1"
}
```

All fields are required; unknown fields, profiles and policies fail. Both guides
must already exist in the site map and must be distinct. Manifest and GPR project
must share a directory. Stable public symbol bookmarks must be enabled. The
existing source-text, source/native profile, anchor, directory and exception
checks remain mandatory.

The existing `inputs` mapping must bind the example manifest, GPR project, every
main/support source and **every public package specification**, in addition to
all preexisting authored inputs. Each value is SHA-256 of exact source bytes.
Configuration binds the enclosing manifest SHA-256 as before. Missing, unlisted,
nonregular, symlinked (including ancestor symlinks), substituted or ambiguously
owned inputs fail. Duplicate JSON keys fail.

The example manifest has exactly `schema_version: 1` and an ordered nonempty
`examples` array. Each entry has exactly:

* `id`: unique lowercase hyphenated identity;
* `title`, `purpose`, `provider_family`, `mock_library`: nonempty inert text;
* `main`: `src/<lowercase_ada_name>.adb`;
* `support`: explicit list of `src/<lowercase_ada_name>.ads`/`.adb` paths;
* `guide`: the declared example guide plus `#<id>`;
* `packages`: nonempty list of actual public package identities;
* `cases`: ordered nonempty list described below;
* `executable`: the main filename without its `.adb` extension.

Main ownership is exclusive. Support ownership can be explicitly shared between
examples; a main cannot also be support. All files in every literal GPR
`Source_Dirs` directory must be listed; no recursive/glob/project evaluation is
performed. `Main` must equal the exact main inventory. Duplicate lists,
conditional/inherited projects and nonliteral source/main expressions fail.
Other project attributes are not interpreted or executed.

Each case contains exactly `id`, `configuration`, `provider`, `exit`, `expected`.
IDs are globally unique lowercase hyphenated identities, configuration is
nonempty text, provider is `normal` or `missing`, exit is integer 0 or 1, and
expected is a nonempty list of nonempty strings. Cases are **instructions and
expected observations**, never measured outcomes. The bounded serialization
prints `sh <manifest-directory>/run.sh <case-id>` as escaped display text; it
does not read or run that script. No shell command field is accepted.

### Independent provenance is a separate boundary

A digest is not an independent authority when its supplier can also replace the
bytes. Consumers must export regular files from an independently selected Git
commit/tree, compare all input bytes against that export, regenerate native
evidence, and compare the **complete derived contract** against the submitted
one before invocation. Rehashing a substituted source and contract is not
qualification. The renderer cannot distinguish an authorized new source epoch
from a maliciously substituted but self-consistent epoch without that independent
input authority. Output-side `presentation.json` never supplies it.

The qualification script below preserves that separation. It executes trusted
consumer auditing code only in qualification tooling, never in the library.

## Exactly three expansions

* `{{example:known-id}}`: exactly once per manifest entry, in its own
  `<section id="known-id">` on `source_blocks.guide`. That section must contain
  its declared public package tokens. Complete UTF-8 main bytes, including final
  newline, are escaped and annotated; each explicit support file is displayed in
  a generated inert `<details><summary>Supporting source: PATH</summary>…`.
  Cases follow in manifest order.
* `{{public-symbol-index}}`: exactly once on `catalog_guide`. Stable symbols use
  the existing public-bookmark selection and source/native correspondence, not
  caller-provided rows. The policy name is retained from the proposed interface;
  it does **not** widen existing bookmarks to arbitrary constants.
* `{{example-usage-index}}`: exactly once on `catalog_guide`. Additional types
  and uniquely resolved operations come only from actual main/support references.

Existing `navigation`, `package-directory` and `package:…` tokens are unchanged.
Every other template expression, wrong-guide token, missing/duplicated token or
unknown example fails. No imports, callbacks, rendered-HTML inputs or executable
build commands are accepted.

Use resolution accepts ordinary context imports, unshadowed initial package
renamings and complete qualified type marks/unique parenthesized operations.
Comments, literals, ambiguous overloads, shadowed prefixes, unsupported scopes,
use-visibility guessing and prefixed object calls confer no association. Source
order and observed native anchors remain authoritative. Repeated uses in an
example produce one association; shared support produces explicit associations
for each owning example. The known omitted native renaming stays omitted.

## HTML and publication validation

Only exact independently recomputed blocks authorize:

* generated inert `details`/`summary`;
* `data-example-source` on its exact generated `code` listing;
* `data-catalog-entry`, `data-kind`, `data-scope` on exact generated catalog `li`;
* the exact empty `<span class="ada-source-end" aria-hidden="true"></span>`.

Validation removes each canonical generated block exactly once and applies the
unchanged schema-2 HTML allowlist to the entire authored remainder. Thus forged
annotations elsewhere, reordered rows, altered source spans/links/labels and
changed observations fail. The full page still passes ordinary duplicate-ID,
resource, URL and local-fragment validation. There is no blanket `data-*`, ARIA
or attribute exemption. Scripts, handlers and active resources remain prohibited.

For the new opt-in only, `api/presentation.json` adds `authored_source_blocks`
with contract path/digest/profile/input hashes. Its existing `output_sha256`
also records all nine portal outputs. Both are independently reconstructed on
verification; neither can authorize a source, declaration or destination.

## Exact MEL oracle and reproduction

Principal fixture: MEL PR #196 commit
`039bd4f05be969f0f224747728dfbae5305ee29b`, tree
`44aa2c2ae4eba378b85694f34e07cfbaf20a33a6`, **seven** guides, landing and CSS.
The older schema-2 six-guide fixture remains unchanged and remains tested.
The new fixture includes original source/native/reference bytes and separate
SHA-256 provenance. Native evidence is regenerated for that source epoch, not
copied from the historical anchor ledger.

From an absolute checkout path, run the ordinary suite and the independent
consumer reconstruction (replace absolute input paths with your qualified ones):

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_source_blocks.py -v
PYTHONPATH=src python scripts/qualify_source_blocks.py \
  --consumer /absolute/trusted/mel-checkout \
  --baseline /absolute/fresh/mel-source-epoch-qualification \
  --official-python /absolute/official-v015-env/bin/python \
  --workspace /absolute/new/qualification-workspace
```

The latter exports the exact commit, independently reconstructs the consumer
publication using its official-wheel origin checks in the supplied interpreter,
reuses all 18 pilot rejection cases unchanged, validates canonical source listings
and parsed catalog rows using consumer auditors, compares all nine portal bytes
and the full publication inventory, and checks deterministic generation and
idempotence. Only `api/presentation.json` may differ, and only the fields above.
It writes full evidence to the supplied workspace. It is not a deployment path.

Optional Playwright qualification of a freshly enhanced **complete** candidate
(no production-page fallback) is available as
`python scripts/check_source_blocks_browser.py --workspace /absolute/new/browser`.
It exercises all eight HTML pages at 1280/390px, light/dark and JavaScript on/off,
complete listing text, support disclosures, catalog/native anchors and default
package navigation. The existing browser CI job runs it and retains its JSON.

The controlled declaration fixture was generated in a separate full Git export:
derive `obj/docs/public-sources.txt` using the consumer's `specifications`, run
`gprbuild -p -P docs_api.gpr -u -c -gnatc`, then GNATdoc with
`-P docs_api.gpr --backend html --generate public --style trailing --warnings
-O /absolute/fresh/api`. The original regeneration must match `mel/native` before
adding `Source_Epoch_Probe` after `pragma Pure` in `ada/src/ams.ads` and repeating
both commands. The compiler-free regression retains just the changed source,
independently regenerated native page and provenance; it rejects old source,
native and contract combinations before accepting the fully regenerated epoch.

Compiler/run evidence remains separate. Rendering source never claims compiler,
runtime, provider, hardware or production-adoption success. A new release must be
separately qualified **after independent review and merge**; v0.1.5 is untouched.
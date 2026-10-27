# GNATDOC-007: source-verified authored content

## GNATDOC-017 presentation opt-in

Authored guide/portal permissions remain separate from theme approval. A
consumer can select its original `gnatdoc-theme.css` using the paired
`[presentation] theme_css_source` and `theme_css_sha256` fields described in
[configuration](configuration.md). Core's landing already links
`api/gnatdoc-theme.css`; it needs no HTML rewrite. Its five guides retain the
separately approved `gnatdoc-guides.css`, source text and destinations. Native
GNATdoc CSS remains untouched. Other consumers need their own CSS approval and
DOM/browser qualification: a successful Core pilot does not authorize arbitrary
stylesheets or consumer adoption. Roll back by removing both options and building
fresh, not by rewriting landing HTML or presentation metadata. Defaults and
existing authored contracts remain unchanged.

This is shared-tool qualification, **not consumer adoption or publication**.
The starting main revision is `4c75e86524648bd84fad17f112ea2f56f24ebffa`.
The clean baseline passed all 306 original tests and four synthetic profiles.
Historical GNATDOC-002 through GNATDOC-006 evidence is not rewritten.

## Authoritative contracts

| Consumer | Pinned revision | Authored inventory |
| --- | --- | --- |
| Core | `c5545eee815431568495c6c76af83df56cf5c3dd` | landing + five Markdown guides in `docs/` |
| Imgproc | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` | landing + five Markdown guides in `docs/guides/` |
| Geometry | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` | landing + five Markdown guides in `docs/guides/` |
| MEL | `6065129aba5dee89e70b61e05a9e1c9b2c3061c0` | landing + six authored HTML guides |

The original OpenCV renderers fix guide identities, ordering, titles, entry
points, source attribution, heading collision handling, source links, fence
languages and stylesheet bytes. Imgproc and Geometry require every complete
Ada fence to have one exact example owner and every example to appear. Their
operation browsers define overload numbers in **source order**, matching full
profiles to observed native declaration anchors. A native HTML list position
or a name alone is insufficient. Core has source-text Ada examples: no compiled
guide-fence claim is added to its original workflow.

MEL's original site map fixes Getting Started, Architecture, IR Workflows, RF
Workflows, Ownership and Errors, and API Map in that order, with their original
IDs and canonical paths. The portal substitutes only navigation, the package
directory, and qualified package references. It uses `assets/portal.css`, not
the generic enhancer guide stylesheet. Home and API Map contain the complete
29-package directory, grouped Shared/Core, IR, RF. The independently observed
native pages are reconciled against all original anchor evidence, including
signatures, rather than authorizing filenames from package names alone.

Original scripts, validators, workflows, guide inputs, CSS, reference output,
fragments and links are fingerprinted in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc007/`.
Authentic fixtures retain their source bytes and SHA-256 provenance. Synthetic
adversarial mutations are explicitly labeled in the test module and do not
replace authentic inputs. Fixtures are integration inputs, not compile evidence.

## Opt-in configuration and trust boundary

Existing `guides.mode = "none"`, `html`, and `markdown` remain supported.
Two new modes, `authored-markdown` and `authored-html`, require a project-owned
schema-2 JSON contract and its SHA-256 in TOML:

```toml
[guides]
mode = "authored-markdown"
manifest = "authored.json"
sha256 = "<the reviewed contract's full SHA-256>"
```

The contract explicitly binds each guide's identity, label, source and output,
home, stylesheet, source reference mappings, example/build project inputs,
approved fence languages, renderer exceptions, native input hashes, and portal
groups/directory pages where applicable. See the complete executable contracts
in `/home/zboll/git/ada-gnatdoc-enhancer/tests/authored-fixtures/` and
`/home/zboll/git/ada-gnatdoc-enhancer/scripts/qualify_authored.py`.

This is **not an arbitrary Markdown/HTML publishing permission**. Unknown or
duplicate JSON keys, extra inputs, duplicate identities, ambiguous mappings,
noncanonical outputs, source/native byte changes, unrecognized tokens,
unsupported markup/resources and unauthorized paths fail closed. The Markdown
extra must contain exactly `markdown-it-py==3.0.0` and `mdurl==0.1.2`; versions
are checked before rendering. Source HTML is checked against a limited element
and attribute vocabulary as well as the existing whole-site validator.

No consumer renderer executes in production. The qualification harness imports
original renderers only in isolated reference processes. Publication verification
reconstructs authored bytes from the trusted source contract, not an output-side
manifest. Changing published bytes and their publication hash together fails.
Generation and validation run in staging before any caller-owned site writes.
This protects against qualification failure; it is not a crash-safe filesystem
transaction or a concurrent-writer publication protocol.

URI escapes are rejected in the opt-in authored contract because no qualified
input requires them. Exact observed parent links to approved root pages/assets
are supported; arbitrary traversal, queries, executable schemes, embedded
resources, unapproved hosts and symlinked inputs/outputs are not. Mutable prose
links to GitHub Pages are preserved as prose, never treated as pinned Core
dependency evidence. Production dependency URLs remain disabled.

## Executed qualification and parity

The original renderers were run independently against hash-checked GNATDOC-002
native acquisition. Every approved guide, landing page and authored stylesheet
is byte-identical to that independently generated reference. This specific
authored-output result does **not** assert that the enhanced native API pages
are byte-identical to consumer-specific API enhancement implementations.
Per-guide hashes, headings and links are recorded separately in each report.

| Consumer | Native sections | Local type links | Offline external links | Authored target |
| --- | ---: | ---: | ---: | --- |
| Core | 1,268 | 2,459 | 0 | landing + 5 |
| Imgproc | 314 | 326 | 549 | landing + 5 |
| Geometry | 130 | 171 | 95 | landing + 5 |
| MEL | 1,237 | 1,418 | 0 | landing + 6 |

Core retains 195 packages, 25 summaries and 102 separately counted explanatory
links, with zero fabricated native instance members. MEL retains 29 packages,
1,238 source/1,237 native sections, 4,294/4,295 coverage and the single uncredited
Health Status metadata renaming omission. Its 73 historical warnings are all
private-part warnings, with no public/tool/unclassified additions. No fabricated
Health Status declaration or link is emitted.

Original OpenCV generation/validation scripts were executed without deployment.
Geometry's first run rejected an unpinned dependency; the successful run used
its required detached Core `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` checkout.
Imgproc resolved indexed Core `386c5360ac51f2b62e522853d94290aec4ee14a0`.
MEL's complete original generation, coverage, portal validation, documentation
tests and approved integrity guard ran in a detached Git checkout. The guard
checked 1,162 protected files with the original reviewed native-test state.

Both `docs/example.gpr` and `docs/examples/examples.gpr` were built, and the
landing executable plus all five guide executables were run for Imgproc and
Geometry. Compilation, execution status, ownership and input hashes are separate
evidence. Source equality alone is never reported as a successful build/run.
Core's landing example was also built/run; its guide fences remain source-text
qualification only.

Chromium qualification extends the prior framework to every authored page,
direct heading fragments, guide navigation, real package/declaration links,
Back/Forward, keyboard focus, responsive tables, 1280px/390px, light/dark and
JavaScript on/off. MEL visits all directory destinations on both directory pages.
The machine records contain individual executed assertions, not inferred passes.
No screen-reader certification, production URL availability, full AMS GRA Skill,
MFA, or production-service implementation is established.

## Reproduction and remaining adoption requirements

Use a new absolute workspace and the historical hash-checked native acquisitions:

```sh
PYTHONPATH=src .venv/bin/python scripts/qualify_authored.py \
  --name geometry --sources /tmp/gnatdoc007/exports \
  --acquisition /tmp/gnatdoc002-acquisition \
  --previous /tmp/gnatdoc006/qualified \
  --workspace /tmp/gnatdoc007/new-geometry \
  --reference /tmp/gnatdoc007/reference --output /tmp/gnatdoc007/new-evidence
```

Hosted CI installs the pinned documentation-only extra and runs authentic
fixtures, adversarial tests, four synthetic profiles and installed wheel/sdist
tests on Python 3.11/3.12/3.13. Hosted fixture tests do **not** execute original
consumer Ada builds, MEL's Git integrity guard, or Chromium. Those full-site
integration results remain separate local evidence.

Adoption still requires independent review, consumer-owned policy approval and
workflow integration, a verified version-stable external hosting contract, and
broader accessibility/visual review. No consumer workflow, production Ada source,
approved MEL integrity policy, historical dependency manifest or published Pages
content was changed. No tag, release, merge or auto-merge is authorized.
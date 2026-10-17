# GNATDOC-005 — version-pinned external Core type links

## Disposition and trust boundary

**READY_FOR_INDEPENDENT_REVIEW**, **PUBLISHED_URL_PENDING**.
Hosted CI and the final tested commit are recorded on the open PR; they are not
inferred from local results. No consumer repository, workflow, deployment,
warning policy, coverage baseline, MEL integrity policy, tag or release changed.

Starting point: clean `origin/main` at
`c1a691452cf436624809f4043b30087de6688052` (merged GNATDOC-004).
All original **189 tests** passed before implementation. Historical evidence
under GNATDOC-002/003/004 is unchanged.

Three evidence levels are intentionally separate:

1. **Dependency anchor verified:** original source/native bytes at the actual
   dependency SHA, reconciled declaration identity, unique observed page/anchor.
2. **Consumer link verified offline:** emitted links checked against those bytes
   and exercised in Chromium through explicit local HTTPS interception.
3. **Published link verified:** **not established**. No stable hosted deployment
   was supplied or discovered as a reviewed deployment contract. No mutable
   GitHub Pages address is assumed to represent either dependency SHA.

The implementation therefore allows manifest generation/consumption only with
explicit **offline-test** mappings on reserved `.invalid` hosts. It does not
pretend those links are usable production URLs. Production manifest linking is
fail-closed pending a version-stable deployment and a reviewed enabling profile.
Existing explicit HTTPS links retain their original allowlist policy.

## Independently acquired dependencies

| Consumer | Consumer SHA | Core release | Required Core SHA | Exported public types/subtypes |
| --- | --- | --- | --- | ---: |
| Imgproc | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` | 0.4.1 | `386c5360ac51f2b62e522853d94290aec4ee14a0` | 203 |
| Geometry | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` | 0.5.0 | `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` | 210 |

Each was freshly cloned, detached, commit-checked, and archived **before** Alire
generated build files. Both built successfully before documentation generation.
Native generation stopped before any consumer presentation script. A second
native generation produced identical full-site bytes for each dependency.

Tools: Alire **2.1.1** with isolated settings; GNAT **16.1.0**;
GPRbuild **26.0.0 (2026-04-15)**, Alire release **26.0.1**;
GNATdoc **26.0.0 (20260415)**. The default PATH GNATdoc **27.0w** was not used.
Original source, all native HTML and native CSS hashes are in each `*-input.json`.
Exact commands and compiler versions are preserved in `dependency-commands.txt`.

Core 0.4.1 predates `docs_api.gpr`. The acquisition script supplies a small,
recorded documentation-only harness selecting its own `src` and production
compiler switches, with `src/internal` available for resolution but excluded
from publication. These harness bytes/hashes are recorded separately; they are
not claimed to be original Core source and no newer Core source is substituted.
Core 0.5.0 uses its own committed documentation project.

Five scanner-discovered types per revision are deliberately not exported from
packages containing nested scopes. Generic-instance members are not synthesized.
The previously qualified Core `c5545eee...` remains a separate consumer baseline,
never a stand-in for these dependencies.

## Manifest and consumption

`external_types.inventory` first validates complete source/native input hashes,
stages only independently inventoried public source files, and uses the existing
source/native profile reconciler. A second HTML parser independently checks the
heading, declaration text and unique anchor. Ordinary flat package-owned public
types/subtypes only are exported. Manifest records contain fully qualified Ada
identity, owner, kind, source file/line, source file/declaration SHA-256, observed
native filename/anchor and native declaration SHA-256, plus exact qualification
scope. JSON duplicate keys, including case variants, fail closed.

The optional TOML `external_dependencies` array pins the expected repository and
SHA, both evidence hashes, original source/native directories, selected fully
qualified names, allowlisted base URL and publication level. Consumption checks
the entire reconstructed manifest, **not merely whether a claimed anchor exists**.
Thus swapping to another valid declaration, page or dependency revision fails.
Independent output verification repeats the checks and reconstructs output from
source. Output metadata cannot grant permissions or redefine dependency proof.

Local resolution precedes external resolution. An existing local package cannot
import a different owner for its types. Unqualified spellings never select an
external destination. External guards decline private/limited context clauses,
nested/generic packages, aliases and shadowed prefixes. This is a conservative
profile extension, not a general Ada semantic resolver. Unsupported references
stay plain text rather than broadening inference.

## Executed full-site results

| Consumer | Packages | Native declaration sections preserved | Local links preserved | External links verified offline |
| --- | ---: | ---: | ---: | ---: |
| Core | 195 | 1,268 | 2,459 | 0 |
| Imgproc | 1 | 314 | 326 | **549** |
| Geometry | 2 | 130 | 171 | **95** |
| MEL | 29 | 1,237 | 1,418 | 0 |

All four pass original declaration/anchor/text/link preservation, native CSS
byte preservation, source integrity, independent output reconstruction,
two-copy determinism, byte-idempotence, and anchor/link/asset/source tamper
rejection. External and local counts are reported separately.

Every observed candidate was audited by native section and offset. In these
pinned inputs all 549 Imgproc candidates (14 identities) and 95 Geometry
candidates (seven identities) passed the supported typed-context and visibility
guards and were linked. Unresolved, unsupported and ambiguous counts are **zero
for these observed candidates**, not a promise about arbitrary Ada syntax.
Each accepted occurrence and its source/native proof is in `*-references.json`.
These counts came from executed output and an independent candidate audit, not
by treating the GNATDOC-002 inventory as automatic link credit.

Consumer coverage checks pass unchanged on native **and enhanced** output:
Imgproc **1,512/1,512**, Geometry **452/452**. Existing warning comparison scripts
pass with `--fail-on-removed`; the exact outputs are in `consumer-ratchets.json`.
The conservative enhancer scanner is not a replacement consumer coverage model.

## Adversarial and distribution qualification

The new suite tests revision cross-substitution in both directions; wrong valid
page and wrong valid declaration; arbitrary fragments; deleted anchors; source
identity changes; post-qualification source/native mutation; ownership and alias
conflicts; duplicate case-insensitive keys/types; ambiguous local use owners;
unqualified, invisible and shadowed references; unsupported generic-instance
targets and source profiles; malformed/corrupt manifests; evidence hash changes;
cross-host redirects/substitution; unsafe schemes, encodings, traversal, queries
and fragments; and an existing deployment response containing wrong bytes.

Reduced authentic Core root packages from **both actual revisions** are shipped
for offline hosted tests. Their source/package-page bytes are authentic; the
filtered index is explicitly fixture scaffolding, not pristine full-site proof.
Reduced Geometry resolves 94 external occurrences because this deliberately
reduced dependency fixture omits `OpenCV.Core.Mat`; that one remains unlinked.
Full-site qualification independently resolves all 95 with the complete artifact.

The Python 3.11/3.12/3.13 hosted matrix runs unit/mutation tests, four synthetic
profiles and authentic reduced inputs. Clean installed-wheel and extracted-sdist
rebuilt-wheel checks run outside the source checkout. Heavy full-site acquisition
remains an explicit local operation; hosted CI does not pretend to have those
inputs. Exact test/packaging evidence and hosted status are in the evidence and PR.

## Browser and publication boundary

The Chromium driver revalidates dependency manifests before intercepting
`https://core.invalid/FULL_SHA/api/...` with pinned **local** bytes. For Imgproc
and Geometry it clicks a rendered external link, checks the revision, package,
native anchor and declaration fingerprint, exercises direct navigation and
Back/Forward, and checks 1280px/390px layouts, light/dark themes and
JavaScript-disabled fallback. Original internal navigation checks remain.
Core and MEL browser checks also run. Driver failures encountered while fixing
iframe-history and explicit browser-context handling are retained in the local
logs; only final executed passing reports count as qualification.

This browser simulation is **not evidence of real HTTPS hosting**. The separate
`verify_published` audit requires an explicit fetch callback and compares every
native file's bytes, rejects redirect/host substitution, and never treats HTTP
success or an existing ID as declaration-identity proof. Tests exercise matching
and mismatching responses; no actual public deployment has been qualified.

Final local suite: **238 tests passed** (189 preserved + 49 new). The clean
installed wheel and extracted-sdist/rebuilt wheel each execute the same 238 tests
and four-profile conformance successfully. Hosted checks are tracked against the
exact PR head, separately from these local results.

## Reproduction and evidence

From `/home/zboll/git/ada-gnatdoc-enhancer`, with the reviewed native prerequisites:

```sh
python scripts/acquire_real_sites.py --dependencies-only \
  --workspace /absolute/new-dependency-acquisition \
  --gnatdoc /absolute/gnatdoc-26.0.0/bin/gnatdoc
PYTHONPATH=src python scripts/qualify_external_types.py \
  --acquisition /absolute/original-four-site-acquisition \
  --dependencies /absolute/new-dependency-acquisition \
  --workspace /absolute/new-qualification --output /absolute/new-evidence
PYTHONPATH=src python scripts/check_real_browser.py \
  --workspace /absolute/new-qualification/imgproc --output /absolute/imgproc-browser.json
PYTHONPATH=src python scripts/check_real_browser.py \
  --workspace /absolute/new-qualification/geometry --output /absolute/geometry-browser.json
make test conformance compile
```

Evidence directory:
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc005/`.
It contains dependency acquisition records, complete source/native hashes,
qualified manifests, consumer mapping, occurrence-by-occurrence proofs, structural
reports, browser assertions, ratchets, negative test results and validation status.
Original native artifacts remain in isolated acquisition directories; they are
reproducible inputs, not silently replaced by reduced fixtures.

## Remaining blockers / recommended next task

Obtain deployment-owner agreement for immutable version-specific Core 0.4.1 and
0.5.0 documentation URLs. Independently verify their exact pinned artifacts,
then review a production consumption profile (including availability/stability
and explicit publication attestations). Do not enable it based on mutable Pages
content or browser interception. Consumer adoption/workflow migration, authored
guides, MEL portal/integrity approval, and Core generic-instance summaries remain
separate tasks. Stop at independent review: leave the PR open, non-draft,
unmerged, with auto-merge disabled.
# GNATDOC-034 qualification and adoption boundary

## Identities and scope

Fetched and verified enhancer main before implementation:

* commit `d15ca9febbe939feee70fb6ce9c96a31e89150b5`
* tree `0eb491843a32df60ab1611aef86487bc9adf344d`

Core was independently cloned at:

* commit `dbdb410c0d86b640271733d7b999ede5a5f92267`
* tree `5bcbe86967fea4f718aab96a348fcaef5e8cfe8a`

Implementation commit: `5b4884bea29cfd9b9cf8a7f06d6176ca02c366e2`, tree
`b3e16171c66fe1b9f2204809e6b21fc745c6def5`. The final documentation/evidence
commit and hosted run identities are reported on PR #29 (avoiding a self-referential
commit hash). No release, consumer checkout edit, deployment, or merge is included.

## Authentic homepage destinations

All four destinations use native page
`api/6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html`:

| Call | Public declaration line | Exact native anchor |
| --- | ---: | --- |
| `Create (2, 3, ...)` returning Mat | 1130 | `9453fef18922c567cef4a785986626da5ded5225eecc2276f7b7ab8de77d92c6` |
| `Image.Clone` (Mat) | 1242 | `f0d347c5f5d28b39c4b977115b9879f00e12c48a5e95816c85142ade1ea40af1` |
| `Copy.Rows` (Mat) | 3661 | `00f85810953412f15e0bdb21a86dff989020f06dbf58da2dc35eaf46a9a95eab` |
| `Copy.Columns` (Mat) | 3669 | `a6e49bbc3415c1da655a5142bc8e9a9e3d651204a4bb49699636cd0d5941bd50` |

The resolver reconstructs these from selected defining token, complete profile,
source hash and observed native evidence, not supplied URLs. Both HTML tests and
real clicks assert Mat `Clone`, not UMat `Clone`; source and native-profile mutation
tests reject substitution. Existing two lexical Mat type links remain, for six
homepage code links total. The original landing source and displayed example text
are unchanged (the established display rule removes final LF characters only).

## Mixed-guide and production controls

`tests/verified-fixtures/mixed-core/guide.md` contains an authentic complete Core
unit, an unchanged ownership-guide fragment, an ambiguous unauthenticated
`Copy := Image.Clone;`, lexical type references, Markdown prose, and shell/text
fences. Only the four authenticated call tokens gain links. The remainder of the
HTML after the first fence is exactly equal with verification on/off. A modified
near-match complete fence also stays lexical. No compilation context is invented.

`production/authored.json` is Core's original source-text manifest, with an empty
guide example inventory. The fixture constructor restores all five **original**
guides and the original homepage using hash-checked overlays. All 38 original Ada
fences are retained. Verification on/off leaves every guide HTML byte unchanged;
only the separately authorized landing example gains the four compiler links.

Fourteen new tests include positive rendering and negatives for missing/wrong
project coverage, project outside compiler snapshot, conditional projects,
duplicate source contents, unapproved guide mapping, missing guide example,
changed landing whitespace/offsets/content, and disabled missing mappings.
The predecessor tests retain wrong-overload, stale input, pin, native anchor,
unsupported classification and overlapping-span controls.

## Local qualification

* Original baseline: **723 tests passed**.
* Full enhanced suite: **737 tests passed**.
* Optimized verified tests: **34 passed**, including all 14 new tests.
* Clean compiler-free installed wheel: **737 tests passed**; Libadalang absent.
* GNATDOC-031 qualified environment: **23 tests passed**, no skips.
* GNATDOC-032 qualified integration: **18 passed**, normal and optimized, no
  skips (16 static positives, 15 negatives and three unsupported controls).
* GNATDOC-033 fresh compiler generator: **4 passed**, including wrong-overload
  injection, unsupported canonical form and concurrent source mutation.
* Fresh authentic Core mapping: **4 accepted / 1 unsupported skip**, one fresh
  unit compilation, GNAT 16.1.0 / GPRbuild 26.0.0 / Libadalang 26. The skipped
  reference at line 9 is not an explicit static subprogram call. Portable mapping
  SHA-256: `2eeeb283aa0a54113dbeb423653549f13f6238f587c282ab391b9debfc6ba61a`.
* Full reconstructed Core pipeline: enhancement and verification passed,
  idempotent, 195 packages / 202 HTML pages / 208 files / 4,582 links.
* Chromium: **8 cases passed**, desktop 1280 and mobile 390, light/dark,
  JavaScript on/off, real clicks to all four exact anchors, original Core custom
  stylesheet, exact text and clipboard, keyboard focus, syntax colors, no nested
  links, no runtime errors or external requests. Mixed positive/negative browser
  controls also passed. Screenshots and structured results are retained locally
  and by the hosted examples-browser artifact.
* Five historical consumer output sites are byte-identical to verified main
  when verification is disabled (Core, Core search, Imgproc, Geometry, MEL).
* Wheel and sdist build, strict Twine validation, independent sdist wheel rebuild
  and archive audits passed: no mandatory dependencies; only the existing pinned
  optional Markdown dependencies; source/wheel/sdist/rebuilt module and asset
  identities equal. Version remains 0.1.4; these are test builds, not releases.

Structured browser and archive evidence is under `docs/evidence/gnatdoc034`.
Complete logs, local compiler receipts, builds, screenshots and wheels are retained
outside the repository at `/home/zboll/gnatdoc034-private`. Final sdist tests,
strict legacy screenshot comparisons and hosted final-commit qualification are
reported in the PR delivery record after completion. Screenshot assertions are
unchanged: no visual tolerance or blanket retry was introduced.

## Reproduction and remaining limits

Use the existing generation instructions in `docs/compiler-verified-examples.md`.
For a compiler-free checkout with the existing optional guides dependencies:

```sh
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -p 'test_verified*.py' -v
python scripts/check_verified_examples_browser.py --workspace /new/empty-browser-output
```

Core adoption requires only its existing publishing configuration to select and
pin the generated mapping; `source-text`, the five guides and `docs/example.adb`
can remain unchanged. This task does not modify that consumer configuration.

Generic/renaming/dispatching calls, implicit/inherited/local declarations,
operators, unsupported ALI forms, non-ASCII/tab/CRLF source columns and automatic
fragment compilation remain unsupported. Source-text build coverage intentionally
accepts explicit literal local project inventories, not computed/inherited or
conditional GPR evaluation. Installed publishing remains compiler-free; no new
review authorization or governance mechanism is introduced.
# HTML document metadata (GNATDOC-010)

GNATdoc 26.0.0 API pages carry no document title, language, head element or
character-encoding declaration, and the enhancer's Markdown guides had no
title. Browser tabs, history, bookmarks and search results then show a URL,
and assistive technology cannot announce the page (WCAG 2.4.2 Page Titled,
3.1.1 Language of Page). This task adds deterministic, source-verified
metadata without modifying any native declaration content, so consumers can
publish accessible documentation without editing generated HTML.

Starting `main`: `53a321915da2c5a02a54581040673b61f8595b25` (GNATDOC-008A #8
and GNATDOC-008B #9 merged; clean tree; 392 tests, four-profile conformance and
compile passing). Implementation: `8768548d30018148643de2fc19c3aa7d132fb7bd`;
browser/consumer harnesses: `2a42e8520b52ec91896a99a01b25f741d8a2f576`
(`src/` unchanged). Evidence: [evidence/gnatdoc010](evidence/gnatdoc010/).

GNATDOC-010-R1 reconciled this branch with `main`
`426f38852ef7dfff264f73ad01aab458f5e12b23` (GNATDOC-009A, PR #11:
source-verified ordinary subtype-base links) by a normal two-parent merge,
`077cb5e4e52e90159ae05e77d81597739828226c`, and requalified the combined
behavior; see [Reconciliation with GNATDOC-009A](#reconciliation-with-gnatdoc-009a)
and [evidence/gnatdoc010r1](evidence/gnatdoc010r1/). Sections that cite `main`
`53a3219` record the original PR head `79f4d23` and are kept as history.

## Failing baseline (OpenCV Features)

Measured on the actual merged Features source
`78a07df8bfd4884a9546cee78904fb5ff93aae21` (DOC-009 Pages infrastructure),
regenerated in a disposable clone with GNATdoc 26.0.0 and its production
enhancer pin `478d0bb`:

| Item | Observed |
| --- | --- |
| Public API packages / native declaration sections | 4 / 38 |
| Documented public elements, GNATdoc warnings | 127/127, 0 |
| HTML pages | 13 |
| Pages with a valid title | 1 (the authored portal) |
| Pages lacking a title | 12 (5 native API pages, 7 Markdown guides) |
| Pages lacking a language | 5 (the native API pages) |
| Features Pages gate (`check_pages_site.py`) | `publication_ready = false` (12 untitled pages) |

The enhanced output equals Features' committed evidence byte for byte. With
enhancer `main` (`53a3219`) instead of `478d0bb` every Features HTML page is
byte-identical; only the navigation script, theme stylesheet and presentation
manifest differ. Hashes: [features-preflight.json](evidence/gnatdoc010/features-preflight.json).

## Supported native page shape

Every real GNATdoc 26.0.0 (20260415) API page, from all qualified consumers,
begins exactly

```text
<!DOCTYPE html>\n<html class=main>\n<link rel=stylesheet href=gnatdoc.css><body class=content>
```

(`<body class=main>` for `api/index.html`), with no `<head>`, `<title>`,
`<meta charset>` or `lang`, and no closing `</body></html>`. The repository's
synthetic conformance pages use the same element sequence without the two line
breaks and the html class. `metadata.check_native_input` accepts only these
two forms and rejects, before any output is written:

- a missing doctype, another or an extra html attribute, a bare or other
  `<body>` class, or any element between the native stylesheet and the body;
- any preexisting `<title>`, `<head>`, `<meta charset>` or html `lang`, anywhere
  (a titled native page is not GNATdoc 26.0.0 output and is never overwritten);
- a duplicate html root or body.

The reduced profile harness in `tests/test_declaration_profiles.py` now wraps
its authentic declaration excerpts in the real prologue instead of a bare
`<html><body>`; the excerpts and every assertion are unchanged.

## Authorized insertion

Metadata is the last transformation of an API page, after code highlighting,
type links, generic summaries, the theme and navigation. It is one bounded
insertion: `lang="en"` joins the existing html start tag (its native
attributes stay), and an explicit head wraps the head content the pipeline has
already approved, preceded by the charset and the escaped title. Authentic
Geometry index, after:

```html
<!DOCTYPE html>
<html class=main lang="en">
<head><meta charset="utf-8"><title>API Reference — opencv_geometry_ada</title><link rel=stylesheet href=gnatdoc.css><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="gnatdoc-theme.css"><script src="gnatdoc-navigation.js" defer></script></head><body class=main>...
```

The wrapped content must equal exactly the native stylesheet, plus the theme
viewport and stylesheet when `presentation.theme` is enabled, plus the
navigation script on the index when navigation is enabled; anything else is
rejected. Metadata does not depend on theming: with the theme, highlighting,
type links and navigation all disabled, removing the authorized metadata from
each enhanced page yields the original GNATdoc bytes exactly
(`test_metadata_is_the_only_change_without_presentation_features`). No body,
section, anchor, heading, link or code byte is added, removed or reordered.

## Title derivation

| Page | Title | Source of each component |
| --- | --- | --- |
| Package page | `<package> — <project>` | Native h1, reconciled by `NativeSite` with an Ada source package whose declared name must match it exactly (case included); `project` from the validated configuration |
| `api/index.html` | `API Reference — <project>` | Validated configuration |
| Markdown guide | `<label> — <project>` | Source-owned site map label, which must equal the guide's rendered H1 |
| Authored Markdown guide | `<label> — <title_suffix>` | Unchanged GNATDOC-007 generation from the hash-bound authored manifest |
| Portal, HTML guide, authored portal page | the author's own title | Author source; validated, never replaced |

A title is never constructed from an output filename, URL, fragment or page
hash. Components must be one line of visible text: no leading or trailing
space, no control, format (including bidirectional overrides and zero-width
characters), line or paragraph separator, no non-breaking or other non-ASCII
space, at most 300 characters. Titles are HTML-escaped; a project named
`Ada <Docs> & "Tools"` renders as text in the title, and a parser reads back the
exact name.

## Language and character set

Generated pages (API and Markdown guides) are English: `lang="en"` and
`<meta charset="utf-8">` in an explicit head. Author-provided pages keep their
own values, which must be a valid language tag and UTF-8. All qualified
profiles are English; other languages need a reviewed configuration extension.

## Guide modes and author pages

| Mode | Generated metadata | Author pages |
| --- | --- | --- |
| `none` (default) | API pages only | none; existing consumers without guides need no change |
| `markdown` | API pages and every guide | `docs/index.html` must carry its metadata |
| `html` | API pages | `docs/index.html` and each `docs/guides/*.html` must carry it |
| `authored-markdown` | API pages (guides already titled) | landing page must carry it |
| `authored-html` | API pages | every authored page must carry it |

"Carry its metadata" means exactly one html root with one valid `lang`, at
most one head, exactly one nonempty single-line `<title>` and one UTF-8
`<meta charset>` in the head (explicit or implicit), and no metadata in the
body. A missing or duplicate title is an error; the enhancer does not invent
one. All 21 authentic authored guides and four landing pages already comply;
only the synthetic MEL `html`-mode fixture needed titles, which its portal,
guides and generator (`scripts/make_synthetic_fixtures.py`) now carry.

## Verification and preservation

- `validate_files` checks the document contract on every published HTML page
  and, for generated pages, the exact verified title, explicit head and
  `lang="en"`, using an HTML parser that shares no strings with the generator.
- `verify` reconstructs every page, including its metadata, from the pristine
  GNATdoc bytes in the presentation manifest (which remain the reconstruction
  authority) and the source, and requires byte equality before the contract
  check. The manifest schema is unchanged.
- `qualification.preserve_native` records document metadata separately, so
  title text is never counted as visible native body content, and accounts
  for it exactly: on a pristine-to-enhanced comparison each page must gain
  only `lang="en"`, one head, one UTF-8 charset and one title whose subject is
  the verified package (or `API Reference`) and whose project label is the
  same on every page (and equals `config.project` when given). Headings,
  declarations, code, visible body text, anchors and native links are compared
  as before.
- `strip_native_document` removes exactly the authorized metadata and fails if
  anything metadata-like remains; it is the basis of the byte-level
  publication diff against the predecessor.

## Adversarial tests

`tests/test_page_metadata.py` (26 tests) runs every mutation below through
`enhance` or `verify` on the authentic Geometry site unless noted:

| Mutation | Result |
| --- | --- |
| Missing, empty or duplicate generated title | rejected |
| Wrong package title (another verified page's), conflicting index title | rejected |
| Missing or wrong (`fr`) language, conflicting charset, duplicate head | rejected |
| Changed native h1 or h4, changed anchor, modified declaration code | rejected |
| Changed native CSS, extra executable script, injected external URL | rejected |
| Tampered presentation manifest (output hash, captured original, forged title with recomputed hash) | rejected |
| Source modified after enhancement, output changed after enhancement | rejected |
| HTML-unsafe project name | escaped and verified; untrusted names (newline, bidi override, padding) rejected |
| Titled, language-bearing, metadata-bearing or case-renamed native input | rejected, input bytes unchanged |
| Each metadata defect, through the independent document check alone | rejected with a specific reason |
| Unauthorized or inconsistent titles through `preserve_native` (with and without configuration) | rejected |
| Markdown guide H1 differing from its label; author portal without, or with duplicate, title, language or charset | rejected |
| Authored-HTML page without a title (re-authorized manifest); HTML-mode guide without a title | rejected |

Unit tests cover every unknown native layout, the bounded insertion and exact
removal, and each document-contract violation. All 392 earlier tests remain
active and pass unchanged in their assertions.

## Compatibility outcomes

Real consumers were requalified with `scripts/qualify_page_metadata.py` from
the reviewed GNATDOC-008B workspaces (whose enhancer tree equals `main`), with
pristine native inputs re-verified against the GNATDOC-002 acquisition hashes:

| Site | Source SHA | Packages | Native declarations | Pages | Titles / lang added | Author pages | Local links (before = after) | Mutations rejected |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Core | `c5545ee` | 195 | 1,268 | 202 | 196 | 6 | 4,565 | 13/13 |
| Imgproc | `9ce22ae` | 1 | 314 | 8 | 2 | 6 | 1,750 | 13/13 |
| Geometry | `fa81e51` | 2 | 130 | 9 | 3 | 6 | 749 | 13/13 |
| MEL | `6065129` | 29 | 1,237 | 37 | 30 | 7 | 2,965 | 13/13 |
| Imgproc (008 navigation) | `9ce22ae` | 1 | 314 | 8 | 2 | 6 | 1,750 | 13/13 |
| OpenCV Features | `78a07df` | 4 | 38 | 13 | 5 + 7 guides | 1 | 248 references | see preflight |

For every site: two independent enhancements are byte-identical,
re-enhancement is byte-idempotent, `verify` reconstructs the output, the
pristine input is bound, and native packages, declarations, signatures,
anchors and links are preserved. Every page now has exactly one title and a
language. Only the API pages and `api/presentation.json` change; every guide,
landing page, stylesheet and script is byte-identical to the predecessor, and
removing exactly the authorized metadata from each API page yields the
predecessor page byte for byte. GNATDOC-008A operation labels and 008B
declaration history are therefore unchanged.

Each consumer's own authoritative checks were re-executed unchanged: GNATdoc
warning comparisons 0 added / 0 removed (all four); coverage on the new
enhanced HTML Imgproc 1,512/1,512, Geometry 452/452, MEL 4,294/4,295 (the one
uncredited Health Status renderer omission), identical to pristine; MEL's
source-integrity guard 1,162 protected files. Titles are not credited as
documentation. Results: [consumer-metadata.json](evidence/gnatdoc010/consumer-metadata.json),
[consumer-ratchets.json](evidence/gnatdoc010/consumer-ratchets.json).

## Features Pages preflight

In disposable clones of Features `78a07df`, with a recorded temporary
configuration (the enhancer pin constant and asset inventory only; the
production pin is not changed) for `main` and for this candidate, the Features
pipeline, its own `enhance_docs.py` checks and its tests ran end to end:

- 13/13 pages have a title, a language, an explicit head and a UTF-8 charset
  (enhancer `main`: 1, 8, 8 and 8 of 13).
- 127/127 documented, zero warnings, 4 packages, 38 declaration anchors; the
  regeneration and two enhancements are byte-identical; native comparison,
  site links (13 pages, 248 references, 0 external) and the inventoried added
  files pass; both Ada example fences remain byte-identical; the masked
  `Detect_And_Compute` link resolves.
- Versus enhancer `main` on the same input, only the five API pages (native
  metadata only), the seven guides (title element only) and the presentation
  manifest change; the portal and all stylesheets and scripts are identical.
- `check_pages_site.py` reports no inventory, link, title or metadata error;
  `pages_without_title` and `pages_without_lang` are empty.
- It still reports `publication_ready = false` for one unrelated reason: its
  JavaScript heuristic (`://` or a quote followed by `/`) matches the literal
  `lastIndexOf('/')` in the navigation script introduced by GNATDOC-008B. The
  same result occurs with enhancer `main` alone. The Features pin-update PR
  must refine that heuristic in review; this task does not change navigation
  code or the Features gate.

The refinement belongs to Features and must not weaken the gate: it may
exempt only a one-character `'/'` or `"/"` literal that is the sole argument
of a string search such as `lastIndexOf`, `indexOf` or `split`, and must keep
rejecting every other `://`, root-relative (`'/x'`), protocol-relative
(`'//host'`) or template (`` `/${x}` ``) literal, including a bare `'/'` that is
concatenated or assigned (`'/' + path`, `href = '/'`). It should carry
negative tests for each of those and keep the pinned asset hash and the
browser check that every request stays below the project prefix. Until that
reviewed change passes, `publication_ready` remains false and nothing may be
described as published.

## Browser qualification

Chromium 156.0.8078.4 (Playwright 1.64.0 Python, 1.64.1 Node, Node v20.19.2),
local only. `check_real_browser.py` keeps all earlier checks and adds index and
frame titles with language and charset, frame titles across package
navigation and Back, title restoration on Back/Forward, JavaScript-disabled
titles and authored page titles; `check_metadata_browser.py` checks every page
of a site served below `/opencv_features_ada/`.

| Site | Checks passed | Predecessor (008B) checks, all present and passing | Added |
| --- | ---: | ---: | ---: |
| Core | 1,500/1,500 | 1,442 | 58 |
| Imgproc | 1,678/1,678 | 1,620 | 58 |
| Geometry | 1,486/1,486 | 1,428 | 58 |
| MEL | 1,192/1,192 | 1,126 | 66 |
| Imgproc (008 navigation) | 1,678/1,678 | 1,620 | 58 |
| Operation navigation and history (Imgproc, Geometry) | 144/144, 160 traces | 144 | 0 |
| OpenCV Features below `/opencv_features_ada/` | 86/86 | new | 86 |

Features' own Chromium suites also pass on the candidate site: 64/64 at the
root, 109/109 below the project prefix and 64/64 for the root suite below the
prefix (identical to enhancer `main`). Details:
[browser-summary.json](evidence/gnatdoc010/browser-summary.json). This is not
cross-browser, screen-reader or full accessibility certification.

## Reconciliation with GNATDOC-009A

GNATDOC-009A (PR #11, merged as `main` `426f388`) changed only
`src/ada_gnatdoc_enhancer/syntax.py` among runtime files; this branch changed
`guides.py`, `metadata.py`, `pipeline.py`, `qualification.py` and
`validation.py`. No file was changed by both sides, so `origin/main` merged
normally without conflicts as `077cb5e` (parents `79f4d23` and `426f388`).
Subtype linking runs inside the existing presentation step, before metadata
is added, and the metadata checks never look at snippet links; both sets of
protections are kept unchanged.

**Regressions.** The merged suite runs **441 tests**: the 392 baseline tests,
the 26 metadata tests in `test_page_metadata.py` and the 23 subtype tests in
`test_subtype_bases.py`. All pass locally on CPython 3.13, from the installed
wheel and from a wheel rebuilt from the extracted sdist; four-profile
conformance, the reduced real Geometry CLI qualification and compilation pass.
No test or expected value was changed.

**Real consumers.** `qualify_page_metadata.py` now regenerates each
predecessor publication with the separately installed merged base (`main`
`426f388`), which must also verify it, and then requires that the combined
output differs from it only by the authorized metadata. It also requires the
008B → base delta to be exactly the recorded GNATDOC-009A delta, and the
current Geometry source to keep its verified Core link:

| Site | Source | Pages with title, `lang` and charset | API titles added | Declarations | Local links (base = combined) | External links (identical) | 009A subtype links kept | Mutations rejected |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core | `c5545ee` | 202/202 | 196 | 1,268 | 4,565 | 35 | none in source | 13/13 |
| Imgproc | `9ce22ae` | 8/8 | 2 | 314 | 1,759 | 562 | 9, as recorded by 009A | 13/13 |
| Geometry (historical) | `fa81e51` | 9/9 | 3 | 130 | 749 | 106 | none in source | 13/13 |
| MEL | `6065129` | 37/37 | 30 | 1,237 | 2,966 | 0 | 1, as recorded by 009A | 13/13 |
| Imgproc (008 navigation) | `9ce22ae` | 8/8 | 2 | 314 | 1,759 | 562 | same page as Imgproc | 13/13 |
| Geometry (current) | `8690927` | 9/9 | 3 | 130 | 750 | 107 | `Contour` → Core `OpenCV.Point_Array` | 13/13 |

For every site, two independent enhancements are byte-identical,
re-enhancement is byte-idempotent, `verify` reconstructs the output from source
and the pristine originals, native declarations and anchors are preserved, and
`api/gnatdoc.css` equals the pristine stylesheet. Removing exactly the
authorized metadata from each API page gives the merged-base page byte for
byte, so every subtype link, including the current Geometry destination
`https://core.invalid/f8aef00…/api/ea2ebcbc….html#da696e09…` (offline-test),
is unchanged. External link inventories are identical, so no unverified
external link is introduced. Core and historical Geometry outputs are
byte-identical to the original PR head. Imgproc, Imgproc 008 and MEL differ
from it only by the 009A subtype page and the manifest.

Each consumer's own checks still pass: GNATdoc warnings 0 added and 0 removed
(all four); coverage Imgproc 1,512/1,512 (both configurations), Geometry
452/452 (historical and current), MEL 4,294/4,295 as before; MEL integrity
1,162 protected files.

**Browsers.** Chromium 156.0.8078.4, local:

| Harness | Passed | Earlier checks missing |
| --- | ---: | ---: |
| Core, historical Geometry (outputs unchanged) | 1,500/1,500; 1,486/1,486 | 0 |
| Imgproc, Imgproc 008 | 1,678/1,678 each | 0 |
| MEL | 1,192/1,192 | 0 |
| Geometry (current) | 1,486/1,486 | 0 (same check set as historical Geometry) |
| Operation navigation and history | 144/144, 160 traces | 0 |
| `Contour` → hash-verified Core `Point_Array` (009A harness) | 4/4 | — |
| OpenCV Features below `/opencv_features_ada/` | 86/86 | — |

**Features.** The disposable-clone preflight above was repeated with the merged
base and the merged candidate. Features declares no subtypes, so GNATDOC-009A
changes nothing there: the merged-base site equals the previous `main`
output and the merged candidate equals the original candidate. All 13 pages
are titled, with `lang`, head and charset. Only API metadata, guide titles and
the manifest differ from the merged base. The Features suites pass (64, 109
and 64 Chromium assertions). The only `check_pages_site.py` error is still the
`lastIndexOf('/')` match on line 103 of the unchanged navigation script, so
`publication_ready` stays false until the Features change described above.

Evidence: [evidence/gnatdoc010r1](evidence/gnatdoc010r1/). The original
GNATDOC-010 records in [evidence/gnatdoc010](evidence/gnatdoc010/) are kept
unchanged.

## Migration impact

- Every enhanced API page and Markdown guide gains metadata, so their bytes and
  the presentation manifest's output hashes change. The manifest fields and
  schema version are unchanged; recorded hashes from earlier revisions are not
  reusable, and historical GNATDOC-001 to 008 evidence is retained unchanged.
- Author pages in `html`, `markdown` and authored modes must carry a title,
  language and UTF-8 charset; Markdown guide H1s must equal their labels; a
  native h1 must match its Ada package name exactly.
- Consumers adopt this only through their own reviewed pin update.

## Reproduction

```sh
python -m unittest discover -s tests -v          # includes test_page_metadata.py and test_subtype_bases.py
# <base python>: a separate environment with the merged base main installed (not this checkout)
python scripts/qualify_page_metadata.py --previous <008B final-qualified> \
  --baseline-python <base python> --geometry-consumer <Geometry clone, read only> \
  --geometry-inputs <GNATDOC-009 type-gate inputs> --geometry-pristine <GNATDOC-009 pristine> \
  --workspace <new> --output <new>
python scripts/check_real_browser.py --workspace <new>/core --output core.json --source-sha c5545ee...
python scripts/qualify_subtype_browser.py --workspace <adapter of <new>/geometry-current> --output subtype.json
python scripts/check_metadata_browser.py --root <features clone> --config docs/gnatdoc-enhance.toml \
  --site <features clone>/_site-enhanced --output features-browser.json
```

The original GNATDOC-010 evidence was produced by the earlier form of
`qualify_page_metadata.py` (predecessor = the reviewed 008B outputs); R1
regenerates the predecessor with the merged base CLI instead.

## Remaining limitations

- Generated language is fixed to English; project and guide labels are used
  verbatim (for example `opencv_core_ada`); the index label is English.
- Only the GNATdoc 26.0.0 shape is supported; no other GNATdoc version is accepted.
- Evidence is Chromium-only and local; no hosted deployment is claimed.
- Features publication additionally needs its reviewed pin update and the
  JavaScript-heuristic refinement noted above.
- The current Geometry Core destination is `offline-test` (`core.invalid`);
  production Core hosting is not claimed.
- Python 3.11 and 3.12 were exercised only by hosted CI; locally only 3.13.

# GNATDOC-002 — pinned real-site compatibility qualification

## Disposition and boundary

**READY_FOR_INDEPENDENT_REVIEW**, with **EVIDENCE_INCOMPLETE** for full adoption.
All four genuine native API sites were obtained. None is labeled fully
qualified. Core/Imgproc/MEL fail closed on authentic unsupported declaration
profiles; Geometry passes API structural and browser checks but lacks qualified
external Core destinations and authored-guide certification. Hosted CI runs
reduced regressions, **not four full-site builds**. No consumer migration,
publication, production-source change, release or policy relaxation occurred.

Starting SHA: `f2529eef6d3b6cceea1fed0d4347ae13129bf79b` (`origin/main`, merged
GNATDOC-001). Initial working tree clean; original **70 tests passed**.
Final tested SHA and exact hosted check status are recorded in the open PR;
an in-tree document cannot contain its own commit SHA. The final local test
suite contains **90 tests** (all original 70 plus 20 new regressions).

## Selected immutable revisions

The reviewed references were available and selected unchanged:

| Consumer | Selected Git SHA | Packages expected / observed | Native HTML / h4 sections |
| --- | --- | --- | --- |
| opencv_core_ada | `c5545eee815431568495c6c76af83df56cf5c3dd` | 195 / 195 | 196 / 1,268 |
| opencv_imgproc_ada | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` | 1 / 1 | 2 / 314 |
| opencv_geometry_ada | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` | 2 / 2 | 3 / 130 |
| ams-gra-mel-bridge | `6065129aba5dee89e70b61e05a9e1c9b2c3061c0` | 29 / 29 | 30 / 1,237 |

HTML counts include each native index, not an authored root portal. Package
counts come independently from public library headers and native h1 headings.
Native IDs, h4 declarations, visible code text and original links are retained
in machine-readable reports. The shared conservative scanner inventories only
types/subtypes/named calls (1,262 / 308 / 126 / 1,203 respectively), not all
objects, exceptions, nested elements or full consumer coverage identities.
It must not be presented as a replacement coverage model.

## Native acquisition and reproducibility

Actual tools: Alire **2.1.1**, **GNAT 16.1.0**, **GNATdoc 26.0.0 (20260415)**,
GPRbuild **26.0.0 (2026-04-15)** from Alire release **26.0.1**; Linux native
OpenCV **4.10.0**, pkg-config **1.8.1**. The default PATH GNATdoc 27.0w and
system GNAT 14.2 were deliberately **not** used. GNATdoc's version command
returns 1 even for the expected version; generation itself must return zero.

Initial acquisition exported exact commits with `git archive` into new
isolated directories. OpenCV libraries were built with `alr -n build` before
generation, preserving their compiler switches and warning policy. Imgproc
resolved indexed Core 0.4.1 at
`386c5360ac51f2b62e522853d94290aec4ee14a0`; Geometry used an isolated Core
0.5.0 checkout at `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`, as its script
requires. Neither is the selected Core documentation revision: this matters
for external anchor qualification, which was **not** inferred from filenames.

For each OpenCV project the native stage was:

```sh
alr -n build
alr exec -- /absolute/gnatdoc-26.0.0/bin/gnatdoc -P docs_api.gpr \
  --backend html --generate public --style leading --warnings \
  -O /absolute/acquisition/PROFILE/pristine/api
```

For MEL the unchanged documentation-only environment and public source list
were used (no production native build):

```sh
alr -n -C docs/toolchain exec -- sh -c 'cd ../.. &&
  python3 scripts/gnatdoc_inventory.py --source-list obj/docs/public-sources.txt \
    --report obj/docs/inventory.json &&
  gprbuild -p -P docs_api.gpr -u -c -gnatc'
alr -n -C docs/toolchain exec -- sh -c 'cd ../.. &&
  /absolute/gnatdoc-26.0.0/bin/gnatdoc -P docs_api.gpr \
    --backend html --generate public --style trailing --warnings \
    -O /absolute/acquisition/mel/pristine/api'
```

Generation was stopped **before** `enhance_gnatdoc_instances.py`, theme,
type-linking, navigation, guide or MEL portal scripts. No published Pages
artifact was used. Fresh native regeneration to a second output location was
byte-identical for **all four** sites, including native CSS. SHA-256 inventories
bind each pristine byte and every Ada source, project file, TOML and relevant
category/baseline manifest used by the harness. These are reviewed acquisition
attestations, not cryptographic proof of how an arbitrary external site arose.

The reusable acquisition script makes new detached clones and records commands;
it never edits the original consumer checkout. It fails on tool, dependency,
generation or warning/coverage gate discrepancies. Prerequisites must already
be installed; it does not weaken or replace consumer scripts:

```sh
/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python \
  /home/zboll/git/ada-gnatdoc-enhancer/scripts/acquire_real_sites.py \
  --workspace /tmp/gnatdoc002-fresh-acquisition \
  --gnatdoc /absolute/qualified-gnatdoc/bin/gnatdoc
```

`/home/zboll/git/ada-gnatdoc-enhancer/scripts/record_real_site.py` records new
acquisitions; compare the resulting pins to the reviewed evidence rather than
silently replacing a mismatching baseline. Full generated trees remain outside
Git. Small authentic excerpts and Geometry API inputs are retained separately
under `/home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures` with provenance.

## Qualification runner contract

```sh
gnatdoc-enhancer qualify \
  --spec /home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc002/geometry-input.json \
  --source-root /tmp/gnatdoc002-fresh-acquisition/geometry/snapshot \
  --site /tmp/gnatdoc002-fresh-acquisition/geometry/pristine \
  --workspace /tmp/gnatdoc002-fresh-qualification/geometry
```

The workspace **must not exist** and must not overlap either input. Paths and
descendants must be regular, with no symlinks. Relative `--site` belongs to
`--source-root`, matching the current CLI. Inputs must be pinned by a full Git
SHA, exact generator identity and source/pristine checksums. A TOML project is
constructed inside each of two isolated workspaces. Original sources retain
their relative paths; only explicitly inventoried public specifications are
also staged under `qualification-public` because normal source-directory
discovery is recursive and consumer documentation excludes internal projects.
This does not change the enhancer's source-root contract or production sources.

The runner records source and native inventories, dry-run validates, enhances,
calls independent publication verification, binds the captured raw payload
back to the external pristine authority, and independently compares native
IDs, signatures, headings and links using HTMLParser. It checks native CSS,
repeat-enhancement byte-idempotence, two-fresh-copy determinism, and rejection
of altered native anchors, links, assets and valid-but-changed source files.
Original inputs are rehashed at completion. A semantic failure emits a report
and exits 2 without claiming later checks ran; invalid acquisition pins fail
before the qualification workspace is constructed. Successful structural
qualification exits 0 but does **not** mean full adoption is qualified.

## Four-repository compatibility matrix

| Category | Core | Imgproc | Geometry | MEL |
| --- | --- | --- | --- | --- |
| Genuine native input | Verified | Verified | Verified | Verified |
| Package inventory | 195/195 | 1/1 | 2/2 | 29/29 |
| Declaration identities after enhancement | Untested: inventory rejects Make_Scalar | Untested: inventory rejects Color_Conversion | **130/130 preserved** | Untested: inventory rejects Cannot_Comply |
| Theme / navigation | Untested | Untested | **Pass structural + Chromium** | Untested |
| Type hyperlinks | Untested | Core unresolved; enhancement blocked | **171 local links valid**, external Core unresolved | Untested |
| Native stylesheet | Pristine hash recorded | Pristine hash recorded | **Preserved byte-for-byte** | Pristine hash recorded |
| Browser checks | Not executed | Not executed | **34 pass** | Not executed |
| Native generation repeatability | Pass | Pass | Pass | Pass |
| Enhancer determinism / idempotence | Not executed | Not executed | **Pass / pass** | Not executed |
| Full-site compatibility | **Incompatible** | **Incompatible** | **Not fully qualified** | **Incompatible** |
| Adoption blockers | Expression functions; 25 instance summaries | Abbreviated enums; external Core; authored guides | External Core; authored guides | Abbreviated enums; full source/renderer model; portal/guides/policy |

### Genuine findings and small corrections

1. **Enhancer defect corrected:** the Ada record terminator assumed `end record;`
   and rejected `end record with Convention => C;`. Authentic MEL
   `AMS.MEL.RF.Product_Rx.Complex_I8` supplies the regression. The scanner now
   finds the record boundary and scans the aspect suffix for its semicolon.
2. **Enhancer defect corrected:** raw GNATdoc uses `&lt;>` for unconstrained
   arrays and literal `=>` for defaults. The snippet guard rejected literal
   `>` even though only `<` can open HTML markup. It now permits `>` while
   retaining fail-closed markup checks. Real Geometry
   `Convexity_Defect_Array` and MEL record snippets round-trip unchanged.
3. **Unsupported profile, not missing documentation:** Core's
   `OpenCV.Make_Scalar` is an expression function; GNATdoc renders its callable
   profile without the expression body, while the bootstrap compares the full
   declaration. It fails closed; no signature equivalence shortcut was added.
4. **Renderer serialization limitation:** Imgproc `Color_Conversion` and MEL
   `Cannot_Comply` native signatures contain `…` in large enumerations. Their
   attached literal documentation exists, but the bootstrap cannot safely
   reconcile the abbreviated signature. No fabricated literals or anchors.
5. **Core instances:** all **25** exact Vector/Matrix instances were audited
   against the source-owned upstream instance list. Each has a native package
   page with zero native member sections. The affected packages, source hashes,
   templates and dimensions are in `core-instances.json`. Summary expansion is
   deliberately not implemented and no template/member destination is invented.

### Coverage, warnings and MEL integrity

Original warning comparisons: all pass with zero added/removed. Core, Imgproc
and Geometry each produce zero documentation warnings. MEL produces **73**
warnings with the unchanged baseline/classification; its package-renaming
diagnostic is retained, not mistaken for an error or documentation credit.
Imgproc coverage is **1,512/1,512**, Geometry **452/452**, both zero-gap ratchets
unchanged. Core has no analogous declaration coverage ratchet in this pin.

The selected MEL baseline reports **4,294/4,295**, **99.9767%**, with **1,238
source / 1,237 native sections / one renderer omission**. This differs from the
older bootstrap prose describing a "4,294-element model": the observed selected
consumer denominator is 4,295 including its exception. The exception remains
`AMS.MEL.IR.Health_Status.Metadata.Status` (`package Status renames
AMS.MEL.Status;`), unrendered and undocumented. Its approved integrity checker
passes at the selected revision against baseline
`42648a92eb0cc84b2980d16db6028992c0494ba1`, protecting **1,162 files**, reviewed
native tests in `original` state. The policy and ratchets were not changed.

### Browser versus structural evidence

Actual **Chromium 156.0.8078.4**, local HTTP, nested
`/first/_site/api/index.html`, widths **1280** and **390**, light and dark.
The **34 executed passing assertions** cover theme asset loading and requested
color scheme, package search/clear, bookmark/direct links, Back/Forward,
operation-category native fragment loading, syntax/type-link presence, keyboard
focus/visible outline, outer viewport overflow and no JavaScript errors; native
package navigation also passes with JavaScript disabled at both widths.
`geometry-browser.json` records each assertion separately.

This is not a visual-design, contrast, screen-reader, touch-device or full
declaration-frame overflow audit. Native code-text identity, every local
destination, all category/overload targets and asset bytes are checked
**structurally**, not by clicking every link in Chromium. Browser checks for
the other consumers were **not executed**, because enhancement is blocked.
Their authored guides are still present and hashed in source snapshots, but
portal rendering/compiled examples are **not qualified** by this API-only run.
No cross-repository URL is emitted without an independently verified exact
dependency-revision anchor; unresolved references remain plain text.

## Evidence and CI

Machine-readable evidence lives under
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc002`:

- `*-input.json`: immutable revision, tool identity, package/source lists,
  source and pristine SHA-256 inventories and constructed TOML.
- `*-report.json`: actual full native API qualification, including inventories,
  scanner profiles, explicit failed phase or structural checks and output hashes.
- `*-acquisition.json`: actual warning/coverage observations and native repeat.
- `geometry-browser.json`, `core-instances.json`, `validation.json`:
  browser assertions, affected instances and local validation outcomes.

Hosted workflow retains Python 3.11/3.12/3.13 unit/mutation tests, the original
four synthetic profiles, wheel/sdist clean installation and out-of-tree tests.
It adds explicit authentic Geometry CLI qualification. Extracted fixtures for
all four sources check provenance and known gaps, **not** full-site success.
Required hosted check names/statuses and tested commit SHA are listed in the
PR after push. No hosted full-site compatibility certification is asserted.

## Prioritized follow-up backlog

| Priority | Class | Work / acceptance evidence |
| --- | --- | --- |
| P0 GNATDOC-003 | Unsupported source/native profiles | Independently model expression-function callable profiles and abbreviated enumerations; retain exact overload/default/source identity, use authentic failing excerpts, rerun all four full native sites. No blanket name-only matching. |
| P0 | Missing dependency evidence | Generate/verify Core sites at each actual dependency SHA (0.4.1 and 0.5.0), publish a reviewed exact-anchor manifest; never derive hashed filenames from Ada names. |
| P1 | Intentionally deferred feature | Source/template-qualified 25 Core instance summaries with no fabricated native members; independent destination/shadowing tests. |
| P1 | Consumer adoption evidence | Qualify authored guides, compiled examples, MEL portal and full coverage/source-integrity gates. Obtain policy approval separately before MEL migration. |
| P1 | Unavailable presentation evidence | Execute desktop/mobile/browser cases for Core/Imgproc/MEL after profile support; extend visual/accessibility/frame overflow and unknown-safe-content qualification. |
| P2 | Baseline discrepancy | Correct old model-count prose using selected MEL's 4,295 total / 4,294 documented, without changing consumer ratchets or omission accounting. |
| P2 | CI reproducibility | Consider pinned full-site build cache/artifact job once toolchain/native dependency costs are controlled; continue labeling reduced CI accurately. |

Stop at independent review: the PR remains open, non-draft, unmerged and without
auto-merge. These failures are reviewable qualification results, not production
adoption readiness.
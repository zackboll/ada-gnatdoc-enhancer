# GNATDOC-003 — source-verified declaration profile compatibility

This document records GNATDOC-003's historical result. GNATDOC-004's current
four-site results and narrowly added rules are documented in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/mel-profile-compatibility.md`.
Historical evidence remains unchanged.

## Disposition and proof boundary

**PARTIAL_COMPATIBILITY**. All three original GNATDOC-002 profile blockers are
resolved. Core and Imgproc now pass the full native API structural qualification;
Geometry remains passing. MEL advances to a different inventory rejection. No
consumer is certified for production adoption by this work.

Starting SHA: `619f1ef3fb37bc2d66ba0a73090943c6b87e8dcd` (fetched `origin/main`,
merged GNATDOC-002). The initial tree was clean; **all 90 original tests passed**
on Python 3.13.5. Final tested commit and exact hosted check results are recorded
in the open PR, since a commit cannot contain its own SHA.

The implementation compares **presentation profiles**, not semantic bodies or
full documentation coverage. The complete pinned source and pristine native
output are independent authorities. A source hash does **not** prove that
GNATdoc rendered hidden text. A freshly supplied, unpinned source with different
hidden literals can have the same presentation profile: this is unavoidable
information loss, not evidence of equality of hidden content. Qualification
checks the independent acquisition pins **before** matching; publication
verification checks complete source fingerprints. Both reject hidden-source
mutation even if the projection would still match.

## Supported grammar and reconciliation

The implementation is in
`/home/zboll/git/ada-gnatdoc-enhancer/src/ada_gnatdoc_enhancer/profiles.py`.
The source inventory still owns complete declarations. Exact normalized identity
remains the default, including the pre-existing omission of top-level
`Pre`, `Post`, `Global`, or `Depends` aspects. Aspect boundary detection now masks
comments/literals and tracks parentheses; it cannot cut inside a default string
or nested expression. Other aspects, renamings, and arbitrary suffixes are not
newly authorized.

### Expression functions

The supported projection has this deliberately narrow profile grammar:

```text
[overriding | not overriding] function Identifier
  [(Identifier {, Identifier} : [in | out | in out] Qualified_Type
      [:= Default_Expression] {; ...})]
  return Qualified_Type is (Expression);
```

`Qualified_Type` is an identifier or dotted identifier sequence. The tokenizer
consumes the entire declaration, with comments, doubled-quote strings, character
literals, numeric literals, attributes/operators, and balanced parentheses.
Parameter groups split only at nesting-depth-zero semicolons. Defaults remain
complete tokens and are compared exactly, as are names, modes, types and return
type. There is no implicit-mode equivalence or common-prefix matching.

Only after the complete profile is structurally recognized may `is (` start
the expression body. Its matching closing parenthesis must be followed by the
single terminating semicolon. Nested parentheses, aggregates, calls and
conditional expressions can be structurally scanned. Quoted parentheses,
semicolons and `is` do not act as syntax. Free semicolons, ellipses, declaration
expressions, body/aspect suffixes, anonymous access formals/returns, operator
designators and unsupported lexical forms are rejected by this projection.
It is **not a semantic expression parser or Ada compiler**: body tokens are
lexically/structurally checked, not evaluated or type-checked. Acquired native
output and pinned sources remain prerequisites for real qualification.

The native signature must equal the **entire source-derived callable profile**,
without a body or trailing semicolon, matching the observed renderer output.
GNATdoc documents the callable profile, **not the implementation expression**.
The authentic `OpenCV.Make_Scalar` regression is not a production special case.

### Abbreviated enumerations

Supported source grammar is `type Identifier is (Literal {, Literal});` where
literals are identifiers or single Ada character literals. The entire sequence
must be present, comma-separated, balanced, and unique (case-insensitive for
identifiers; character values retain case). Derived types, discriminants,
aspects and malformed sequences are not authorized by this projection.

For **more than 10 source literals**, the only accepted native form is:

```text
type Same_Identifier is (L1, L2, L3, L4, L5, L6, L7, L8, …, Ln);
```

All nine visible literals and their order must match the source exactly. The
ellipsis is exactly one U+2026 token in the ninth position, not `...`, a count,
an arbitrary wildcard, or an omission in any other declaration kind. Exactly
`n - 9` literals are source-owned but not visibly rendered in the snippet.
`Color_Conversion` has 86 source literals / 77 hidden; the authentic
`Cannot_Comply` has 47 / 38 hidden. Original rendered text is never expanded or
rewritten. This matching grants no additional coverage credit to hidden text.

This rule is established independently by genuine native excerpts **and** the
GNATdoc `v26.0.0` source at commit
`04606c2152636ca2125047e3db701b50ed356cd4`, file
`source/gnatdoc-comments-extractor-code_snippets.adb`, lines 153–275:
`Max_Enum_Literals = 10`, replace the penultimate literal with U+2026, remove
literals 9 through n-2. Callable extraction uses `Spec_Node.Token_Start` through
`Spec_Node.Token_End` in `gnatdoc-comments-extractor.adb`, lines 2620–2648.
The source identity, SHA-256 hashes and relevant excerpts are recorded in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc003/provenance.json`.
Other GNATdoc versions or abbreviation patterns are not qualified.

### Identity and failure conditions

Every accepted declaration must have exactly one matching section under its
source-owned package and name, and exactly one observed real anchor. A single
section cannot satisfy two source declarations. Duplicate native IDs, duplicate
equivalent sections, conflicting overloads, altered defaults/types/visible
literals, missing anchors, and unsupported forms fail closed. Native hashed
filenames are observed, never derived. Type-link resolution and visibility
rules are unchanged; no hidden enumeration literal anchors or body links are
invented. The bounded reconciliation cache keys both complete input strings.

## Reproduced baseline and before/after matrix

The genuine GNATDOC-002 acquisition snapshots and pristine GNATdoc 26.0.0
trees were reused **without regeneration**. Every pinned source file and the
entire native file-hash inventory were verified before each qualification.
The immutable identities below refer to the complete hash maps in the historical
`*-input.json` files and the new `*-report.json` files, not substitute sites.

| Consumer | Exact source revision | Reproduced GNATDOC-002 inventory result | New accepted projections | GNATDOC-003 full native API result |
| --- | --- | --- | --- | --- |
| Core | `c5545eee815431568495c6c76af83df56cf5c3dd` | Fail: `OpenCV.Make_Scalar`, scanner line 175 | 1 expression function | **Pass**: 195 packages, 1,268 native sections, 2,459 local type links |
| Imgproc | `9ce22ae5ab70008e1147475a9e6d7baef82f1df0` | Fail: `Color_Conversion`, line 660 | 2 abbreviated enums | **Pass**: 1 package, 314 native sections, 326 local type links |
| Geometry | `fa81e5140cbebf2aa41397a40c08ba194a5f6f73` | Pass | 0 | **Pass**: 2 packages, 130 native sections, **171** local type links |
| MEL | `6065129aba5dee89e70b61e05a9e1c9b2c3061c0` | Fail: `AMS.MEL.IR.C2.Metadata.Cannot_Comply`, line 61 | 9 abbreviated enums (complete independent audit) | **Fail closed**: inventory, `AMS.MEL.RF.C2.Add_Job_Intervals`, line 1513 |

All three original blockers are resolved. The scanner inventories
1,262 / 308 / 126 / 1,203 declarations respectively, **not the consumer coverage
model**. Each successful site passes dry-run immutability, isolated enhancement,
independent publication verification, native headings/IDs/signatures/visible text
and link preservation, native CSS preservation, two-directory determinism,
byte-idempotence, and separate anchor/link/asset/source tamper rejection.
MEL subsequent phases are explicitly **not executed**, not counted as passing.

MEL's complete declaration audit records three remaining mismatches:

| Phase | Source declaration | Reason retained for follow-up |
| --- | --- | --- |
| inventory | `AMS.MEL.RF.C2.Add_Job_Intervals` (scanner line 1513) | Native callable profile omits `renames Add_RX_Job_Intervals` |
| inventory | `AMS.MEL.RF.Product_Rx.Complex_I16` (scanner line 336) | Native record omits `with Convention => C` |
| inventory | `AMS.MEL.RF.Product_Rx.Complex_I8` (scanner line 359) | Native record omits `with Convention => C` |

Scanner lines can include preceding comments; complete signatures, source-file
hashes, observed destinations and reasons are in `mel-profiles.json`. Renaming
and record representation aspects are not these expression/enum profile forms,
so they remain rejected instead of silently extending this task's grammar.
**Next recommended task:** independently qualify these narrowly scoped MEL
profile omissions, then rerun the still-blocked full MEL structural phases.

## Consumer gates and adoption blockers

- **Core:** all 195 packages remain accounted for; 25 generic-instance summary
  gaps remain explicit. No summary implementation or fabricated native members.
- **Imgproc:** unchanged consumer check rerun: **1,512/1,512**, no newly
  undocumented items. Historical zero-warning baseline remains unchanged.
  External Core **0.4.1** destinations remain unqualified.
- **Geometry:** unchanged consumer check rerun: **452/452**. Native preservation
  still covers 130 declarations / 171 local type links. Chromium regression
  evidence is recorded separately, not inferred from structural success.
  External Core 0.5.0 destinations and authored guides remain unqualified.
- **MEL:** 29 packages remain accounted for; unchanged consumer coverage check
  rerun: **4,294/4,295**. Health Status `Metadata.Status` is still one uncredited
  renderer omission. The approved source-integrity policy and historical
  73-warning classification are unchanged. Exact input hashes are reverified;
  no consumer repository or native/source input is edited. This task does not
  replace the approved source-integrity guard or full coverage model.

The unchanged approved MEL source-integrity guard was also rerun read-only in
the isolated acquisition checkout at its pinned SHA: **1,162 protected files**,
base `42648a92eb0cc84b2980d16db6028992c0494ba1`, reviewed native tests in the
original state, clean checkout afterward. No consumer repository was touched.

Warnings were not regenerated: this run reuses the exact pristine output and
GNATdoc logs from the reviewed GNATDOC-002 acquisition. All four unchanged
warning ratchets were rerun against those logs: **0 added, 0 removed**. There is no new native
build, consumer workflow migration, Pages change, portal qualification, release,
tag, or production-adoption claim.

## Tests, distribution and evidence

All original 90 tests remain intact, with **44 new tests / 134 total passing**.
Focused regressions use SHA-256-provenanced
authentic `Make_Scalar`, `Color_Conversion`, and `Cannot_Comply` excerpts; all
mutations and reduced HTML test harnesses are explicitly synthetic. They test
profile changes, nested/quoted boundaries, malformed syntax and ellipses,
ambiguity in both directions, pinned hidden-source mutation, publication source
mutation, text preservation, and absence of fabricated links/anchors.
The four original synthetic profiles remain separate from authentic reduced
fixtures and from full-site qualification.

Local qualification uses Python **3.13.5**. Python 3.11/3.12 are hosted CI
checks, not locally available interpreters. The clean installed wheel and the
wheel rebuilt from the extracted sdist each pass all 134 tests out of tree;
installed assets/CLI and four-profile conformance pass. Geometry's current
Chromium run passes **34 assertions**. A successful build emits existing
setuptools license-metadata deprecation warnings; no packaging policy was
changed to suppress them.

New evidence is under
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc003`:

- `baseline.json`: starting identity and reproduced results.
- `provenance.json`: authentic excerpt and upstream renderer identities.
- `*-report.json`: hash-verified full-site runs, including unexecuted phases.
- `*-profiles.json`: complete scanner audit, accepted projections and remaining
  unsupported declarations; hidden ownership is explicit.
- `geometry-browser.json`: independent current Chromium regression checks.
- `validation.json`: local test, installed-wheel, extracted-sdist/rebuilt-wheel,
  consumer coverage and integrity outcomes, with log hashes and limitations.

Reproduce full-site checks using the **original acquisition** (not consumers):

```sh
/absolute/python /home/zboll/git/ada-gnatdoc-enhancer/scripts/qualify_profile_sites.py \
  --acquisition /absolute/gnatdoc002-validated-acquisition \
  --workspace /absolute/new-qualification-workspace \
  --output /absolute/new-evidence-directory
```

Python 3.11/3.12/3.13 hosted CI retains all unit tests, four synthetic profiles,
authentic reduced Geometry CLI qualification and clean distribution checks,
and explicitly reruns focused declaration-profile regressions. It does **not**
certify four full consumer builds. Exact hosted statuses and final tested SHA
belong to the PR; reduced fixtures never stand in for unavailable full phases.
The PR stops open, non-draft, unmerged, with auto-merge disabled at independent
review.
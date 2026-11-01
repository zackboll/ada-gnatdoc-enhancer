# Findings and qualification — GNATDOC-032

## Research decision

**PROTOTYPE_SUCCESS**, narrowly scoped to the required explicit static-call
controls. Compiler identity is independent of Libadalang: exact ALI occurrence
records lead to defining-name coordinates, which are compared against the precise
canonical LAL declaration and source hash. Both wrong-LAL adversaries are detected
despite a successful compile and intact compiler evidence. No approximate/name-
only selection and no guessed anchor is accepted.

Recommend **option 1: separate compiler-verified mapping generator**. Evidence can
be generated once per compilation unit/configuration in a documentation build,
indexed once across units, and queried repeatedly. Generation is not per link.
The measured prototype does not establish whole-codebase scalability or general
Ada-form coverage. A future generator must keep project/toolchain inputs frozen,
reject unsupported forms, and separately qualify source/native provenance before
producing reviewed mappings. Do not add these dependencies to the enhancer.

## Qualification results

| Check | Result |
|---|---|
| Required exact positive identities | **16/16**, explicit GNAT and LAL locations/hashes in `results.json` |
| Wrong LAL fixture overload, valid compiler evidence | `COMPILER_IDENTITY_MISMATCH`, no hyperlink |
| Wrong real Core UMat Clone identity, valid evidence | `COMPILER_IDENTITY_MISMATCH`, no hyperlink |
| Negative compiler/evidence controls | **15/15**, including suppressed xrefs, stale source/project/scenario/external input, missing/truncated/tampered/conflicting evidence |
| Generic instance / renaming / dispatching | **3 explicitly unsupported**, never linked |
| Acquired native evidence without review authorization | Both Core calls rejected, `SOURCE_NATIVE_MISMATCH` |
| Native positive contract simulations | Both Core calls reconcile after compiler agreement, **ephemeral TEST-ONLY authorization**, no real review granted |
| Native profile tampering | Rejected, no hyperlink |
| New unit + authentic integration tests | **18/18** normal, **18/18** `-O`, **18/18** `PYTHONOPTIMIZE=1`; no skips |
| Unchanged predecessor research tests | **23/23**, no skips |
| Preserved invalid/ambiguous compiler negatives | All **three** rejected; raw LAL observations retained; no links |
| Existing production regressions | **703/703**, no skips, 338.209 seconds |
| Wheel comparison to authenticated main | **47/47 members byte-identical**, dependency metadata identical |
| Clean installation | New venv, `--no-deps`; Libadalang unavailable; installed four-profile conformance passes |
| Production/workflow/packaging/031 preservation | No tracked changes outside the new research directory |
| Fresh authenticated native acquisition | Same schema-2 VERIFIED manifest SHA-256 `77e3a4f3627b88adc58bd0e76baf4d301788110530d06fb4b3bbf8a7254a1469`; no approval |

The raw LAL 26 ambiguity defects from GNATDOC-031 remain defects. Their evidence
and disposition are unchanged. Compiler legality and compiler declaration identity
are distinct gates; this prototype adds the latter.

The offline-only test command accurately skips its one opt-in integration test
without private tooling. Final qualified runs set the integration arguments and
skip **nothing**. The existing hosted workflows do **not** acquire the private
GNAT/LAL/Core research environment; local research qualification is not a claim
that hosted CI ran these controls.

## Measured costs

Single retained qualified run on this Linux host, not a benchmark guarantee.
Times include subprocess start-up where applicable. No-change incremental costs
are measured in separate disposable output trees after warm-up; authenticated
original outputs are never overwritten by the timing experiment.

| Measurement | Fixtures (two units) | Authentic Core example (one unit) |
|---|---:|---:|
| Fresh compiler generation | 0.625 s | 0.340 s |
| Complete evidence validation | 0.262 s | 0.341 s |
| ALI parsing/indexing | 0.430 ms | 2.559 ms |
| Median lookup, 10,000 queries | 8.93 µs | 8.67 µs |
| No-change incremental invocation (one unit) | 0.292 s | 0.216 s |
| Fresh compiler peak child RSS, separate lightweight monitor | 42,628 KiB | 52,204 KiB |
| Fresh compiler artifacts | 23,676 bytes | 8,607 bytes |

Combined LAL/qualification/control runner peak RSS: **378,100 KiB** (~369 MiB).
The runner's raw `RUSAGE_CHILDREN` peak is also retained but inherits a large
parent high-water mark for some subprocesses and is **not** used as compiler-only
memory. Separate lightweight-monitor measurements above avoid that confusion.
Compile-only selected-unit generation does not bind, link or run Core or its C++
shim. It proves compiler acceptance and static selection, not runtime behavior.

The parser/CLI core uses Python standard library only. Optional semantic/native
adapter reuses private Libadalang 26 and the unchanged enhancer/031 reconciliation.
Observed pre-existing private footprint: GNAT 16 toolchain **990 MiB**, GPRbuild
**278 MiB**, private installed Ada library closure **245 MiB**, LAL Python venv
**15 MiB** (approximate `du -sh`). No new global package, GNATCOLL.Xref, SQL database,
or production dependency was installed. Cold rebuilding the LAL dependency closure
was not repeated or included in these timings; follow the predecessor private
setup/lock instructions. Existing GPRinspect is used to bind evaluated project
closure and externals; it is **not** the occurrence/declaration resolver.

## Evidence retention and failed attempts

`results.json` is the final complete qualified control report. `evidence/` retains
the exact successful compiler receipts, three authentic ALIs, generated Core
configuration, expected CLI requests, native acquisition metadata/qualification,
test logs, packaging report, and installed conformance output. Compiler invocations,
versions, relevant source and dependency hashes and ALI hashes are in the receipts.
`environment.json` records authenticated base/Core identities and upstream source
investigation. `SHA256SUMS.json` covers retained files, not transient bytecode or
itself. Raw private workspace: `/home/zboll/gnatdoc032-private/`.

Development attempts are not counted as successes:

* The first dispatch fixture put primitives directly in a procedure, which GNAT
  correctly rejected as nondispatching. It was corrected to declare them in a
  package; final compiler evidence emits `R` for the real dispatching occurrence.
* The initial incremental timing reused altered source mtimes and could recompile;
  final measurements warm a **separate** tree and measure a second no-change run.
* Initial wheel builds in the repository's development venv failed because it had
  no setuptools backend. Existing system setuptools 78.1.1/wheel 0.46.1 built both
  baseline/candidate with `--no-build-isolation --no-deps`; no package was added.
* A multi-mode foreground test command hit the tool's 30-second limit after a
  complete normal run and incomplete optimized run. Optimized/environment-mode
  tests were rerun in background and completed; only complete logs count.
* An initial CLI verification used a differently composed `PATH` (duplicate path
  entries removed), correctly returning `COMPILER_EVIDENCE_STALE`. Under the exact
  recorded environment all 14 fixture requests confirm. This strict environment
  pinning is deliberate, including semantically equivalent PATH changes.

See README for unsupported forms and the local trust model. All native positive
links retained here are **test simulations**, not operator-authorized production
maps. No independent review is claimed; no self-approval, deployment or merge.

Delivery remains **HOSTED_CI_PENDING** while required hosted checks are outstanding,
independently of the research disposition. Final commit/tree, PR and hosted status
are reported after push rather than pretending a file can contain its own hash.
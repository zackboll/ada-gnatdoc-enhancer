# GNATDOC-031 decision report

## Disposition: PROTOTYPE_DEFECT

Both real Core expressions resolve and match verified native anchors, and the
**compiler-gated** prototype produces zero incorrect hyperlinks in the tested
controls. Nevertheless, the required negative controls demonstrate incorrect
raw semantic resolution by Libadalang 26.0.0. Per the requested disposition
definition, this is **PROTOTYPE_DEFECT**, not an unqualified success. It is not
an environment blocker: a real Python/native environment works.

## Eight explicit answers

1. **Does Libadalang correctly resolve Core's `Create`? Yes.** `CallExpr`,
   `/home/zboll/gnatdoc031-core-dbdb410c/docs/example.adb:5:28–5:74`
   (Libadalang end position is exclusive). The selected canonical `SubpDecl`
   in `src/opencv-core.ads:1130:4–1132:72` has profile
   `function Create (Rows, Columns : Natural; Element_Type : Mat_Type) return Mat`
   and the actual source precondition. Owning package: `OpenCV.Core`.
2. **Does it correctly resolve `Image.Clone`? Yes.** The expression at
   `docs/example.adb:6:28–6:39` is **`DottedName`, not `CallExpr`**. It selects
   `src/opencv-core.ads:1242:4–1242:43`,
   `function Clone (Self : Mat) return Mat;`. It does **not** select the UMat
   declaration at line 512. `p_expression_type` is `OpenCV.Core.Mat` for both
   real expressions.
3. **Can both match exact native anchors? Yes.** Complete profiles reconcile
   uniquely with the observed native page and sections below. No ordinal or
   filename hash was synthesized. Zero competing public declarations match.
4. **How many representative Markdown examples are reliably resolvable? Six
   of all 38 Ada fences** in the five guides. They are unchanged complete
   compilation units, resolve as whole units and independently compile under
   GNAT 16. No author-created semantic mappings or object declarations are
   needed. Thirty other fences need missing declarations/visibility; two are
   generic declaration outlines requiring synthesized context. No fragment is
   counted authoritative. The interop guide contains **zero** Ada fences.
5. **Were incorrect declarations or hyperlinks produced?** Incorrect **raw
   declarations: yes**, for two compiler-rejected ambiguous controls; incorrect
   **authoritative hyperlinks: zero** in the exercised controls. The raw defect
   is material and explicitly retained, not reclassified as success after
   adding a compiler guard.
6. **Installation/performance/CI costs?** See measurements below: approximately
   17.5 minutes for the two-job private native build, 245 MiB installed prefix,
   793 MiB build tree, native GNAT 15 ABI/runtime plus the shared-library
   closure, and Python 3.13. Cold-process import ~41–46 ms; project load
   ~156–177 ms; first real semantic query ~tens of ms. Mandatory independent
   compilation adds ~239 ms for this example. No existing CI was changed.
7. **Backend, separate generator, or no integration?** Do **not** integrate
   Libadalang alone as an authoritative semantic backend. If pursued, prefer a
   separate opt-in **compiler-validated, reviewed, content-hash-bound mapping
   generator** for complete, authentic units. This research does not implement
   production consumption of such a mapping.
8. **Are reviewed explicit mappings more practical for incomplete fragments?
   Yes.** Fragment-local missing object types, callbacks, enclosing procedures,
   generics, and visibility are authored meaning. A plausible synthetic wrapper
   is not evidence that it is the guide author's intended context.

## Verified relative links

* Create:
  `api/6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html#9453fef18922c567cef4a785986626da5ded5225eecc2276f7b7ab8de77d92c6`
* Mat Clone:
  `api/6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html#f0d347c5f5d28b39c4b977115b9879f00e12c48a5e95816c85142ade1ea40af1`

These are candidate build-time relative hyperlinks into the **verified pinned
native snapshot**, not a promise about any future deployment. The page SHA-256
is `4bfea5661e76a96fb4a8db02d2c9579e2372e7707552e94bebb5ad528898c4bb`.
The UMat Clone is a different observed section
`81309973708df2cef5edea90e47614862e050c128229a2757dbcb11d6f5afbc1`.

## Source/environment qualification

Fresh authenticated remote main checks matched enhancer
`2200eb0e95e769a70d3d38a6c8b7facce8205924` and Core
`dbdb410c0d86b640271733d7b999ede5a5f92267`. The original enhancer release
worktree and existing older Core checkout were left unchanged. Research lives
in `/home/zboll/gnatdoc031-enhancer`; the independent pinned Core checkout is
`/home/zboll/gnatdoc031-core-dbdb410c`; generated Core config, compiler outputs,
Python venv and libraries live under `/home/zboll/gnatdoc031-private`.
All four requested files and the 392 Ada source files in the export match the
clean pinned checkout. The unchanged example compiled, linked, and ran with
GNAT 16.1.0 / GPRBUILD 26.0.0 (2026-04-15), Alire release 26.0.1.

Initial inventory: system GNAT 14.2; downloaded GNAT 13/15/16 and GPRbuild
22/26; only Python 3.13 discovered; no system-importable Libadalang and no
Libadalang shared object; a cached static 26.0.0 build was present. The
GNAT Studio path on PATH did not exist. The private Alire dependency sandbox
and generated Python binding use native 26.0.0 built with GNAT 15.3.0 (Alire
toolchain 15.3.1). Python package metadata misleadingly calls the binding
`Libadalang 0.1`; it is not a different native release. Actual API/property
signatures were inspected in the installed 26 binding.

Recursive `gprinstall` alone omitted XMLAda's aggregate members, causing a real
`OSError: libxmlada_schema.so.18.0w` import failure. Explicit recursive XMLAda
installation into the same private prefix fixed it. Successful import, context
creation, parsing and a real expression type query are recorded in
`environment.json`. All `ldd` dependencies then resolved. No global pip,
system package installation, or Core toolchain configuration changes occurred.

Native evidence: authenticated workflow run
`https://github.com/zackboll/opencv_core_ada/actions/runs/41245425725`, artifact
`13059359370`, `gnatdoc-diagnostics-dbdb410c0d86b640271733d7b999ede5a5f92267`.
Fresh `gh api` metadata tied it to the exact commit and successful run. Retained
ZIP SHA-256 equals GitHub's
`2537dae628887231dfdd2a16159457bb5be4a25f7a840923458fc2a896870dbd`.
The archive's commit/tree identities matched; only its 197 pristine
`obj/docs/native/` files were extracted. Nothing was republished or regenerated
in deployed documentation. Qualification binds every source and native member.

## Semantic mechanism and critical counterexamples

For both real nodes the installed API provides:

* `GPRProject(...).create_context(event_handler=...)`
* `context.get_from_file(...)`
* `p_referenced_decl(imprecise_fallback=False)`
* `p_called_subp_spec` (property)
* `p_expression_type` (property)
* `p_referenced_defining_name(imprecise_fallback=False)`
* `decl.p_canonical_part(imprecise_fallback=False)` (method)

Whole-unit xref-entry-point preflight, project errors, parse diagnostics,
semantic diagnostics and missing-unit callbacks were empty for Core. Reusing
the same context returns the same parsed unit and memoized semantic answers.

However, `fixtures/ambiguous.adb` defines two `Pick` overloads on distinct
integer types. GNAT rejects `Pick (1)` as ambiguous. Libadalang's precise
queries select **the Second overload at line 5**, return a spec and defining
name, and report successful preflight with empty diagnostics. Similarly,
`default_ambiguous.adb` is compiler-ambiguous between one formal and an overload
with a defaulted second formal, but Libadalang selects the latter at line 3.
No imprecise fallback was enabled. Thus an AST selection is not proof of Ada
legality or uniqueness. Raw evidence and independent compiler output are in
`results.json`; do not use raw `selected_declaration` as authority.

The prototype was hardened: an explicit qualified GPRbuild must force a
compile-only check in a temporary relocated build tree before any authoritative
link is emitted. Missing compiler, compiler rejection, project errors,
unsupported local/generic/renaming declarations, source mismatch or non-unique
native destination remain unlinked. A reviewed qualification input is a trust
boundary, not self-authenticating arbitrary JSON. Compiler/project config and
qualification/native/source hashes must be reviewed together. A compile-only
gate is not a proof of runtime behavior or dependency bodies' correctness.

## Control outcomes

Seven research unittest methods pass with the actual native binding (no skips).
They cover parameter types/counts; named argument order; defaults; return type
context; Mat versus UMat prefixed Clone; qualification; multiple use clauses;
local shadowing; generic instance and renaming observation; missing project
dependency; invalid/ambiguous/default-ambiguous calls; absent compiler;
modified native hashes; and rehashed wrong full-profile destinations.
Valid fixtures independently compile/link/run with assertions enabled. All
three invalid/ambiguous controls independently fail compilation.

Generic instantiation yields the generic formal profile and instance identity;
renaming yields its renaming declaration. These are correctly observed in the
valid fixture, but mapping instantiated/substituted or renamed public identity
to native sections is deliberately unsupported. Local shadowing resolves to
the local expression function, not the unrelated public overload. No negative
control is allowed an authoritative hyperlink.

Guide counts: operations 10; ownership 17; typed-access 2; interop 0;
sparse/persistence 9. Reliable ownership fence numbers: **4, 5, 6, 9, 10, 11**.
One fence contains a complete callback procedure followed by a loose call:
the whole fence is a fragment, not a complete compilation unit. Original text,
source lines, added wrapper bytes, compiler results and semantic outcomes are
preserved per fence. Experimental wrapper success, if any, never grants
authority to an original fragment.

## Measured costs and limits

Three fresh processes (warm OS filesystem cache, no cache dropping):

| Phase | Measured range |
|---|---:|
| Import | 41.2–45.6 ms |
| Standalone context initialization | 4.6–5.7 ms |
| GPR project load + project context | 156.5–177.3 ms |
| Parse real example | 0.223–0.289 ms |
| First precise queries | approximately 20–45 ms per expression |
| Memoized four-property query bundle | approximately 42–54 microseconds |
| Reuse parsed unit | approximately 57–78 microseconds |
| Native reconciliation (uncached broad page/source scan) | 0.51–0.56 s per call |
| Independent example compiler gate | 0.239 s |
| Full guarded Core probe | 1.62 s |
| Peak RSS, semantic measurement | 118–119 MiB |

Preflight cost (~66 ms) is separate from subsequent memoized query time.
The private build took 1048.41 s with two jobs on a loaded shared workstation;
these are observations, not CI latency guarantees. Individual compiler RSS was
observed in the multi-GiB range; no complete build peak was instrumented.
Private prefix ~245 MiB including headers/ALI files; main `libadalang.so` ~61
MiB unstripped. Shared dependencies include GPR2, GPR, GNATCOLL core/minimal/
projects/GMP/iconv, Langkit Support, AdaSAT, Prettier Ada, VSS text/GNAT,
XMLAda schema/DOM/SAX/input/unicode, GNAT/GNARL 15 runtimes, GMP, GCC runtime,
libc/libm/loader. Exact paths/hashes and `ldd` are in `environment.json`.
The Python binding itself imports only standard-library modules; building its
package uses setuptools. Core analysis used GNAT 16 on process-local PATH
while the native shared library used GNAT 15 runtime ABI successfully.

A future optional CI job would need a cached, qualified native closure and a
compiler, separate process-local environment, dependency/config resolution,
hash-bound inputs, independent compiler validity, review, and fail-closed
negative controls. Context and destination indexes could be reused within one
process to reduce cost; no production optimization/integration was attempted.

## Isolation qualification

Production `src`, packaging metadata, scripts and existing workflows remain
byte-identical to pinned main. The wheel has 47 members, no research or
Libadalang members, unchanged package bytes, and only the existing optional
guide dependencies. A fresh `--no-deps` installation without Libadalang passed
enhancer conformance. Source conformance passed. The established test
environment passed **703 tests**. An initial run under bare system Python
failed 43 tests because the optional guide parser was absent; this was an
environment failure, not silently counted as a pass, and the established
environment rerun passed. No unnecessary release/browser/deployment campaign
was run. The original checkout and deployed/public artifacts were not changed.
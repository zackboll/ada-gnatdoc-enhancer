# GNATDOC-031 — isolated Libadalang Python research

Nothing here is imported by, or a dependency of, the released enhancer. This
directory is a separate build-time experiment, not an integration proposal.
Read `findings.md`, `environment.json`, and `results.json` for the measured
outcome and limitations. Do not interpret an experimental fragment result as
an authoritative link.

## Source identities

Authenticated `git ls-remote` checks must return:

* enhancer main: `2200eb0e95e769a70d3d38a6c8b7facce8205924`
* Core main: `dbdb410c0d86b640271733d7b999ede5a5f92267`

Recorded disposition: **PROTOTYPE_DEFECT** (raw Libadalang 26 incorrectly selects
declarations for compiler-ambiguous Ada). The guarded prototype is functional
and preserves zero incorrect hyperlinks in the exercised controls, but this
must not be presented as unqualified Libadalang semantic correctness.

Use an independent clean Core checkout at that exact commit. Do not reset an
existing checkout. Build only a disposable `git archive` export of it. The
original four requested files and all Ada sources must remain byte-identical.
Core's regular configuration generation in the export is necessary: the Git
snapshot does not contain the generated `config/*.gpr` files.

## Private native/Python setup

Prerequisites: Alire 2.1.1, downloaded GNAT FSF toolchain, GPRbuild 26, Python
3.13 with venv, system GMP already available. No `sudo`, global pip, global
toolchain selection, or Core environment changes are needed.

Run `sh setup_private.sh /absolute/new/private/workspace` from this directory.
This sandboxes dependencies (`dependencies.shared=false` locally), builds the
**entire** library closure with `-XLIBRARY_TYPE=relocatable`, recursively
installs under the private prefix, and installs the generated Python package
only into its private venv. The PyPI metadata in the shipped binding says
`Libadalang 0.1`; the native/source release is **26.0.0**, not 0.1.
The retained `alire.lock` records the exact measured dependency solution and
is copied into the private crate before configuration/build.
The smoke check must actually import the native library and execute a type
query. A static build or successful pip installation alone is insufficient.
XMLAda's aggregate requires its own recursive installation; recursive
Libadalang installation alone left `libxmlada_schema.so.18.0w` unavailable.

Source the generated `/absolute/new/private/workspace/runtime.env` only in the
analysis subprocess. Use a process-local PATH with the qualified GNAT 16.1.0
and GPRbuild 26 binaries when analyzing Core; no modification to Core's normal
environment is required. `environment.json` records actual compiler/runtime
selection and all discovered library dependencies.

## Core build and native evidence

### R1 trust contract (supersedes the original schema-1 results)

Acquisition, automated verification, and independent review are distinct:

1. **Acquired:** authenticated `gh api` returned evidence.
2. **Verified:** unconditional checks passed; acquisition writes a schema-2
   `VERIFIED` manifest with complete source/native inventories and retained
   authenticated metadata. It never writes `reviewed: true` or an approval.
3. **Reviewed:** an independent human explicitly reviews the exact inputs and
   separately records approval. The consumer must independently choose the
   authorized reviewer; the record cannot authorize its own reviewer identity.

After actual independent review, that reviewer may run the separate program:

```sh
python3 /absolute/enhancer/research/gnatdoc031/review_authorization.py \
  --qualification /absolute/qualified-native/qualification.json \
  --source-root /absolute/core-export --native-site /absolute/qualified-native/native \
  --reviewer '<independently trusted reviewer identity>' \
  --reason '<review record reference and rationale>' --approve-exact-inputs \
  --output /absolute/private/review-authorization.json
```

This hashes the exact manifest bytes and immutable provenance, authenticated
metadata, and inventories. Missing approval, an operator-untrusted reviewer,
another manifest, stale binding, or changed/extra/missing evidence fails closed.
Schema 1 and its `reviewed` boolean are no longer accepted.

**Trust limitation:** this is an editable local review record, not a signature,
identity authentication, or cryptographic attestation of independent review.
Anyone able to edit the record and operator trust policy can forge approval.
Protect both out of band; never infer human review from a boolean or a record
created by acquisition. Use an operator-controlled private parent directory;
concurrent hostile filesystem mutation is outside this local tool's model.
Tests create only ephemeral `TEST-ONLY-reviewer` records to exercise the
contract; they do not grant approval to PR #26 or to its acquired evidence.

Export the pinned checkout to a new directory, then in that **export**:

```sh
alr -n toolchain --select --local gnat_native=16.1.0 gprbuild=26.0.1
alr -n build -- -j2
alr -n exec -- gprbuild -P docs/example.gpr -p
./obj/docs-example/example
```

Reuse only qualified **pristine** GNATdoc, not the enhanced/deployed HTML.
`qualify_native.py` freshly authenticates GitHub metadata for the exact source
run, verifies the retained ZIP against GitHub's SHA-256, checks the archived
Git commit/tree, and extracts only `obj/docs/native/` to a **new** directory.
If `--zip` does not exist, it downloads the authenticated artifact into the
private extraction root as `artifact.zip` (never to the supplied missing path).
All archive entries are preflighted, including unextracted members; unsafe
paths/types, duplicate/alias destinations, CRC errors, and symlink destinations
are rejected. Output must be new, absolute, and have an existing private parent.
Failure does not leave a usable manifest. All checks remain active with `-O`.
If GitHub
retention has expired, retained bytes with the verified digest remain useful;
fresh acquisition or reviewed retained authenticated metadata is necessary.

```sh
python3 qualify_native.py \
  --core-checkout /absolute/pinned/core-checkout \
  --zip /absolute/retained-or-new/gnatdoc-diagnostics.zip \
  --output-directory /absolute/new/qualified-native
```

The qualification file is verified evidence, **not review authorization**.
Do not manufacture it for arbitrary HTML. Runtime
checks reject missing/extra/changed source and native inventory members. The
mapping itself independently checks public ownership, a precise canonical Ada
declaration, the complete profile, a unique observed section, and competitors.
No filename hash or overload ordinal is calculated or guessed.

## Probe invocation

Use absolute paths throughout. `PYTHONPATH` points to the unchanged enhancer
`src` solely to reuse its existing read-only profile reconciliation helpers.

```sh
PYTHONPATH=/absolute/enhancer/src /absolute/private/venv/bin/python \
  /absolute/enhancer/research/gnatdoc031/probe.py \
  --project /absolute/core-export/docs/example.gpr \
  --source /absolute/core-export/docs/example.adb \
  --source-root /absolute/core-export \
  --native-site /absolute/qualified-native/native \
  --qualification /absolute/qualified-native/qualification.json \
  --review-authorization /absolute/private/review-authorization.json \
  --authorized-reviewer '<independently trusted reviewer identity>' \
  --compiler /absolute/qualified/toolchain/bin/gprbuild \
  --expression 'Create (2, 3, (Depth => UInt8, Channels => 1))' \
  --expression 'Image.Clone' --output /absolute/results.json
```

`--source` and `--expression` can be repeated. Omitting expressions enumerates
names for which the installed binding's `p_is_call` is true. Exact-text
selection retains all matching nodes, never an arbitrary first candidate.
Each source must belong to the project. Whole-unit entry-point preflight and
lazy missing-unit/parse diagnostics invalidate the batch's authority.

**Critical finding:** Libadalang 26 can return an apparently precise declaration
and empty semantic diagnostics for compiler-ambiguous calls. `--compiler` is
therefore mandatory before *any* hyperlink is authoritative. It forces a
compile-only check of the unchanged unit into a temporary relocated build tree;
failure or omission prevents linking. This is not a claim that Libadalang alone
validates Ada. Raw counterexamples are retained in `results.json`.
Compiler acceptance does **not** independently establish exact overload
identity. GNATDOC-032 owns investigation of compiler-backed declaration identity;
R1 does not expand that scope or change **PROTOTYPE_DEFECT**.

Only `RESOLVED_AND_MATCHED` carries `hyperlink`. Other statuses are
`SEMANTICALLY_UNRESOLVED`, `AMBIGUOUS`, `SOURCE_NATIVE_MISMATCH`,
`MISSING_CONTEXT`, and `ANALYSIS_ERROR`. A semantically resolved call without
qualified native evidence has `semantic_resolved=true`, but deliberately no
hyperlink. Do not infer an ambiguity classification from an arbitrary exception
string: invalid/ambiguous semantic controls can conservatively be unresolved.

## Controls

```sh
PYTHONPATH=/absolute/enhancer/src /absolute/private/venv/bin/python \
  -m unittest discover -s /absolute/enhancer/research/gnatdoc031/tests -v
```

Set `GNATDOC031_CORE` (configured export), `GNATDOC031_NATIVE` (pristine site),
and `GNATDOC031_QUALIFICATION` to enable real Core/native tampering controls.
Without Libadalang only the offline qualification tests run; skipped tests
are **not** semantic successes.
Run the independent offline security suite in both execution modes:

```sh
python3 -m unittest discover -s /absolute/enhancer/research/gnatdoc031/tests -p test_security.py -v
python3 -O -m unittest discover -s /absolute/enhancer/research/gnatdoc031/tests -p test_security.py -v
PYTHONOPTIMIZE=1 python3 -m unittest discover -s /absolute/enhancer/research/gnatdoc031/tests -p test_security.py -v
```

The existing seven research tests use only ephemeral test authorization
records for positive Core controls. Successful real acquisition without a
record is separately checked to produce no authoritative links. Optional
`GNATDOC031_CONTROL_OUTPUT` saves those positive/negative control reports.

Copy `fixtures/` to a disposable directory. Independently build and run
`valid.adb` with GNAT 16 / `fixtures.gpr`; compile-only `invalid.adb`,
`ambiguous.adb`, and `default_ambiguous.adb` must fail. Semantic expectations
use fixed independent declaration locations and types, not resolver output.
Generic instances and renamings are observed but deliberately not mapped to
public native anchors by this narrow prototype.

`guides.py --core /absolute/core-export --workspace /absolute/new/fences
--compiler /absolute/qualified/toolchain/bin/gprbuild
--output /absolute/guides.json` preserves all original Ada fences and records
every wrapper prefix/suffix. No invented object declarations are added. A
complete unit is a candidate for reliable resolution only if its whole semantic
preflight succeeds. Independently compile complete-unit candidates before
counting them as reliable. The interop guide has no Ada fences; do not invent
one to make coverage appear uniform.

## Isolation and interpretation

Build a wheel into a private output directory. Inspect every member and
metadata dependency, compare package bytes to the pinned main, install it with
`--no-deps` in a clean venv without Libadalang, and run enhancer conformance.
No existing CI changes or release/publication campaign are required.

Results bind source, project configuration, native, and qualification hashes.
Such a reviewed file could be the output of a future separate mapping process,
but the normal enhancer does not consume this research schema. Complete build
configuration and generated dependencies are semantic inputs, not incidental
paths. Review and requalify after any input or toolchain change.
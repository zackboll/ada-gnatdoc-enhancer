# GNATDOC-032 — compiler-backed overload identity prototype

**Research disposition: PROTOTYPE_SUCCESS** for the required explicit static-call
controls. **Delivery status: HOSTED_CI_PENDING** while required hosted checks are
outstanding. This is not general Ada coverage, independent review approval, or
production integration. No production code, packaging, workflow, deployed site,
or GNATDOC-031 evidence is changed.

## Decision and result

Recommend **a separate compiler-verified mapping generator**. Generate compiler
evidence once for each documented compilation unit under one frozen project
configuration, validate it once, index all ALIs once, and reuse that index for
multiple occurrences. Libadalang and any future GNATCOLL backend remain private,
optional build-time dependencies. The enhancer remains usable without either.

GNAT acceptance alone is not the check. For each occurrence the prototype reads
the exact `s` reference in GNAT's ALI, resolves its entity's **defining-name file,
line, and column**, and compares these and the source SHA-256 against
Libadalang's precise canonical declaration. Only unique agreement permits
subsequent native profile reconciliation. Names are diagnostic text only.

`results.json` records **16 exact agreements**, **15 negative controls**, **three
explicitly unsupported forms**, three preserved predecessor compiler negatives,
and five native-authority controls. The critical adversary preserves a successful
multi-overload compile and its original ALI but substitutes the other overload's
Libadalang identity. It returns `COMPILER_IDENTITY_MISMATCH`, without a link.
The same attack with Core's real UMat `Clone` is rejected too.

### Exact positive identities

Occurrence columns identify the callee token, **not** the beginning of a prefixed
expression. Declaration columns identify the defining name, **not** `function`.
All positions below are one-based; complete identities/hashes and both selections
are retained separately in `results.json`.

| Occurrence | GNAT and canonical Libadalang declaration | Control |
|---|---|---|
| `valid.adb:6:18` | `overloads.ads:4:13` | Mat prefixed Clone |
| `valid.adb:7:19` | `overloads.ads:5:13` | UMat prefixed Clone |
| `valid.adb:8:19` | `overloads.ads:6:13` | Integer Pick |
| `valid.adb:9:19` | `overloads.ads:7:13` | String Pick |
| `valid.adb:10:19` | `overloads.ads:8:13` | one parameter |
| `valid.adb:11:19` | `overloads.ads:9:13` | two parameters |
| `valid.adb:12:19` | `overloads.ads:10:13` | reordered named parameters |
| `valid.adb:13:19` | `overloads.ads:11:13` | reversed parameter types |
| `valid.adb:14:19` | `overloads.ads:12:13` | defaulted parameter |
| `valid.adb:15:19` | `overloads.ads:14:13` | Integer return context |
| `valid.adb:16:18` | `overloads.ads:15:13` | String return context |
| `valid.adb:17:29` | `overloads.ads:6:13` | qualified visibility, distinct position |
| `valid.adb:18:19` | `other.ads:2:13` | use-visible Boolean Pick |
| `valid.adb:25:29` | `valid.adb:24:16` | local shadowing |
| `docs/example.adb:5:28` | `src/opencv-core.ads:1130:13` | `Create (2, 3, ...)` returning Mat |
| `docs/example.adb:6:34` | `src/opencv-core.ads:1242:13` | `Image.Clone`, Mat not UMat |

## Phase 1: mechanism selection

Inventory was performed **before selecting the implementation**:

1. **GNATCOLL.Xref / gnatinspect.** Neither the Xref library/spec/project nor
   `gnatinspect` is installed in the inspected system, Alire toolchains, GNATdoc
   installation, or private dependency prefix. Installed GNATCOLL **core/projects**
   libraries are not Xref. Source investigation of `AdaCore/gnatcoll-db` shows
   `Get_Entity(Name, File, Project, Line, Column,
   Approximate_Search_Fallback => False)` and `Declaration(...).Location` can
   express exact occurrence-to-declaration queries. `Is_Fuzzy_Match` must be
   rejected. CLI command `decl name:file:line:column` exists, but its implementation
   uses the default approximate fallback and can print `fuzzy match for the
   entity` and still return an entity. Neither an approximate result nor an
   unqualified CLI run can be authority. This backend was **source-investigated,
   not installed, built, or runtime-qualified**; SQL/SQLite plus GNATCOLL project
   dependencies add setup cost. No global package installation was attempted.
2. **gnatxref / gnatfind.** Not installed in the system or qualified GNAT 16
   toolchain (nor discovered alternate Alire installations). No execution or
   compatibility claim is made. Their historical source-position query capability
   does not qualify a nonexistent binary for GNAT 16.
3. **Direct ALI.** Selected because no installed maintained query interface could
   be qualified. GCC's documented `Lib.Xref` format explicitly makes `s` a static
   call reference to the selected subprogram specification. `D` table indices are
   one-based; `X` gives the declaration file; entity rows give the defining name
   position; each reference gives occurrence position and a stateful dependency
   index. Continuation rows are parsed; no regex search by entity name is used.
   An unknown row/reference grammar rejects the whole index. Fresh GNAT 16 ALIs
   for the authentic Core example contain:

   ```text
   1130V13*Create{463R9} 11|5s28
   1242V13*Clone{463R9} 11|6s34
   ```

Pinned upstream source references and inspected content hashes are recorded in
`environment.json`. The format source is not itself a compatibility promise:
runtime qualification here is limited to the observed **GNAT 16.1.0** outputs.

## Inputs, provenance, and fail-closed contract

`verifier.py generate` takes an exact snapshot root, project, list of Ada body
files, explicit GPRbuild, scenarios, and a **new** build directory outside the
snapshot. It compiles authentic bytes with `-c -u -f -v`, relocates outputs, checks
successful exit, fresh `.o` companions and GNAT-v16 cross-reference records, and
rejects suppression/source-rewriting options. A legal `-gnatx` compilation is
explicitly tested and rejected for missing xrefs.

The receipt binds the complete ordinary-file snapshot (including non-Ada inputs),
project closure and evaluated variables/switches from recursive GPRinspect, tool
binary hashes and versions, process-local project environment, scenarios, full
compiler command/output, source/runtime dependency hashes, and every build
artifact hash. Source remapping, tabs/non-ASCII coordinates, symlinks, external
project/source dependencies, and ambiguous basenames are outside the qualified
subset and fail closed. Core's generated configuration files are inventoried;
all original tracked Core bytes are checked against the pinned checkout.

`generate` returns a receipt SHA-256. The **operator must retain this digest
separately**; `verify --receipt-sha256` does not trust a digest read from the same
mutable receipt. Missing files, source/configuration/project/scenario/environment
changes, extra/conflicting ALIs, truncated/tampered ALIs, and rewritten receipts
are rejected. A separate parser-boundary conflict control tests syntactically
valid competing declarations at one occurrence and returns `AMBIGUOUS`.

This is a **local trusted-builder / immutable-batch** model, not an attestation
system. A hostile operator able to replace the verifier, binaries, snapshot and
out-of-band digest can forge local evidence. Concurrent mutation during a batch,
arbitrary compiler wrappers/plugins, preprocessing, hostile build actions, custom
runtimes, cross targets, and arbitrary external build dependencies have not been
qualified. The `Evidence` object validates once; inputs must remain immutable
until the batch ends. Open a new session to revalidate after any changes. Do not
reuse a Python object as a persistent trusted cache.

The comparer emits exactly the requested status vocabulary:

* `COMPILER_IDENTITY_CONFIRMED`: unique exact static declaration agreement.
  **Not by itself permission to link.**
* `COMPILER_IDENTITY_MISMATCH`: GNAT and supplied LAL identities differ.
* `COMPILER_EVIDENCE_MISSING`: no exact occurrence, receipt, artifact or xrefs.
* `COMPILER_EVIDENCE_STALE`: artifact/source/configuration/tool/input binding changed.
* `AMBIGUOUS`: multiple incompatible records or nonunique occurrence file.
* `UNSUPPORTED`: forms/grammar outside the qualified subset.
* `SOURCE_NATIVE_MISMATCH`: native qualification/review/profile/node binding fails.
* `ANALYSIS_ERROR`: compile/analysis/malformed request failure.

Only confirmed results **after** independent source/native qualification,
operator-authorized review, canonical-node binding and unique complete native
profile reconciliation may contain `hyperlink`. Identity-only CLI output has no
link. `native_link` reuses GNATDOC-031's read-only qualification and presentation
reconciliation, never its compiler-acceptance-only identity gate. It never guesses
an anchor. The real acquired native site has **no independent review authorization
granted by this work**. Retained positive link results are explicitly labelled
ephemeral `TEST-ONLY` contract simulations, not approved mappings for publication.

## Unsupported findings

* **Generic instance:** the fixture instance has an ALI `[file|line]` origin and
  Libadalang `GenericSubpInstantiation`. Generic mappings can collapse to template
  entities and omit instance columns. No exact public-instance mapping is claimed.
  Generic suffix references reject an index rather than silently losing state.
* **Renaming:** ALI `=line:column` identifies a renaming reference, while LAL
  returns a renaming declaration. No alias-chain/public-destination policy is
  invented; rejected before native lookup.
* **Dispatching:** a successful authentic tagged-type fixture emits `R`, not `s`.
  LAL selects the root primitive; ALI denotes the root specification, **not** the
  runtime target. No unique runtime target/native mapping is claimed.
* Operator/quoted names, inherited/implicit/overriding entities, access-to-
  subprogram calls, entries, generic nested reference grammars, remapped source,
  external or duplicate-basename declarations, Unicode/tab coordinates, and other
  untested forms are unsupported, not silently name-matched.
* Local expression functions can have compiler identity confirmed, but have no
  qualified public native destination. No local native link is emitted.

GNATDOC-031's **PROTOTYPE_DEFECT** disposition and raw compiler-ambiguous LAL
counterexamples remain unchanged. This research adds an independent identity
check; it does not retroactively correct or reclassify predecessor findings.

## Reproduction (absolute paths; no global environment changes)

Measured repository base: `847e0b1bbe67ee14ed78d5ecc84fb61dde121381`, tree
`8ac01ed492cabcf7dd96e737570894b8054eba5f`. Authenticated fetch and `ls-remote`
agreed before branch creation; main had **not moved** from the supplied identity.
Core commit: `dbdb410c0d86b640271733d7b999ede5a5f92267`, tree
`5bcbe86967fea4f718aab96a348fcaef5e8cfe8a`. Use a clean independent checkout at
that commit; only disposable exports are built. Never reset an existing checkout.

The following are the actual paths on the qualification host. On another host,
substitute absolute private paths. Obtain GNAT 16.1.0 and GPRbuild Alire package
26.0.1 (binary reports 26.0.0); use GNATDOC-031's documented private setup and
retained lock for Libadalang 26. Its Python package metadata `0.1` is not the
native library release. The existing measured private installation was reused;
no additional research package was installed globally or into the enhancer.

```sh
export PATH=/home/zboll/.local/share/alire/toolchains/gnat_native_16.1.0_9f74f58a/bin:/home/zboll/.local/share/alire/toolchains/gprbuild_26.0.1_e3f27f25/bin:$PATH
. /home/zboll/gnatdoc031-private/runtime.env
export PYTHONPATH=/home/zboll/git/ada-gnatdoc-enhancer/src

# Fresh authenticated native acquisition, verification only (not review).
python3 /home/zboll/git/ada-gnatdoc-enhancer/research/gnatdoc031/qualify_native.py \
  --core-checkout /home/zboll/gnatdoc031-core-dbdb410c \
  --zip /home/zboll/gnatdoc031-private/r1/qualified-native/artifact.zip \
  --output-directory /home/zboll/gnatdoc032-private/new-native

# Required inputs include Core's normal generated config directory. The measured
# directory was generated in a disposable 031 export with:
# alr -n toolchain --select --local gnat_native=16.1.0 gprbuild=26.0.1
# alr -n build --stop-after=pre-build
# No original checkout or original tracked source is modified.
# For byte-identical replay on this host, --core-config can instead point to
# /home/zboll/git/ada-gnatdoc-enhancer/research/gnatdoc032/evidence/core-config
# (retained generated config; environment-specific, not portable defaults).
/home/zboll/gnatdoc031-private/venv/bin/python \
  /home/zboll/git/ada-gnatdoc-enhancer/research/gnatdoc032/controls.py \
  --workspace /home/zboll/gnatdoc032-private/new-run \
  --compiler /home/zboll/.local/share/alire/toolchains/gprbuild_26.0.1_e3f27f25/bin/gprbuild \
  --core-checkout /home/zboll/gnatdoc031-core-dbdb410c \
  --core-config /home/zboll/gnatdoc031-private/core-build/config \
  --native-site /home/zboll/gnatdoc032-private/new-native/native \
  --qualification /home/zboll/gnatdoc032-private/new-native/qualification.json
```

The runner checks all original tracked Core bytes, complete native inventories,
and fixed expected declaration locations independent of both resolver outputs.
It creates fresh isolated builds and temporary adversarial mutations, restores
inputs, and verifies the original receipts again at the end. It never modifies
the predecessor fixture directory, clean Core checkout, or original native site.

For compiler-only use, copy the predecessor fixtures to a **new private snapshot**
and call `verifier.py generate --root ABS --project ABS --source ABS --compiler ABS
--build ABS`. Retain the printed receipt digest out-of-band. Request JSON is a list:

```json
[
  {
    "occurrence": {"file": "valid.adb", "line": 8, "column": 19},
    "selected": {
      "file": "overloads.ads", "line": 6, "column": 13,
      "sha256": "02fb564b2ec6c948ceedd772cb76e367037e1d484603f3c537082c9097d5654a",
      "kind": "SubpDecl"
    }
  }
]
```

`selected` must originate from precise canonical Libadalang analysis of that
snapshot (the optional `lal_select` adapter demonstrates the exact API). It is
intentionally a separate input to the compiler verifier, permitting wrong-LAL
adversarial controls. Invoke `verifier.py verify --root ABS --project ABS --receipt
ABS --receipt-sha256 DIGEST --requests ABS`, with the same `-X` scenarios. All
results go to JSON stdout; any nonconfirmed call exits nonzero. Optional
`--native-site`, `--qualification`, `--review-authorization`, and separately chosen
`--authorized-reviewer` enable the further native gate; native CLI use also needs
the private LAL runtime and enhancer source/import environment.

Offline tests (17 parser/authority controls, one accurately skipped integration):

```sh
python3 -m unittest discover -s /home/zboll/git/ada-gnatdoc-enhancer/research/gnatdoc032/tests -v
```

For **all 18 with no skips**, set `GNATDOC032_INTEGRATION_ARGS` to a JSON array
containing the six option/value pairs shown for `controls.py` above, excluding
`--workspace`. Run with the private Python, both normally and with `-O`.
`PYTHONOPTIMIZE=1` is also qualified. The integration test uses a fresh temporary
workspace and exercises the entire real compiler/Core/native control runner.

## Performance and qualification evidence

See `findings.md` for measured costs and qualification totals, `results.json` for
full identities/negative controls/provenance/timings, and `evidence/` for the exact
receipts, ALIs, generated configuration, logs, packaging comparison and inventory.
`SHA256SUMS.json` binds every retained research file except itself and bytecode.
Receipts contain original absolute host paths; retained copies are forensic
evidence, **not portable build receipts**. Reproduce to create valid local receipts.

This prototype compiles selected units for xrefs, not the full C++/Ada application
or a runtime target test. Compiler memory/time measures compilation only; LAL
batch RSS includes native libraries and semantic analysis. Hosted workflows remain
unchanged and do not install this research toolchain, so local compiler-control
qualification and hosted enhancer checks are distinct. No self-approval or merge.
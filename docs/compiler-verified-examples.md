# Compiler-verified Ada example links (GNATDOC-033)

This optional feature extends the existing example resolver, highlighter and HTML
renderer. The installed enhancer **does not import GNAT, Libadalang, or ALI files**.
There are no new wheel dependencies or default output changes.

## Generate in a qualified build environment

Use a source checkout of this repository, Python with the existing enhancer
dependencies, Libadalang 26, GNAT 16.1.0 and GPRbuild 26. Other compiler/ALI grammars
are deliberately unqualified. First build your authentic project in that same
environment. Generate native GNATdoc 26 public documentation using your existing
comment style. Freeze the source tree, its recursive project/configuration closure,
and native snapshot; do not include output/build directories in the source tree.

```sh
python /absolute/enhancer/scripts/generate_verified_examples.py \
  --root /absolute/project-snapshot \
  --project /absolute/project-snapshot/docs/example.gpr \
  --source /absolute/project-snapshot/docs/example.adb \
  --compiler /qualified/gprbuild/bin/gprbuild \
  --build /absolute/new-build-directory \
  --config docs/enhancer.toml \
  --native-site /absolute/native-snapshot \
  --output /absolute/new-mapping.json
```

Repeat `--source` for compilation units and `-X NAME=VALUE` for scenarios. The
build and output must be fresh and outside the frozen source snapshot. Public
publishing exports can be separate: `--presentation-root /absolute/public-export`
changes where `--config` is read. Selected public exports must have the **same
basename and full SHA-256** as the compiler-selected source; they are not semantic
substitutes. This supports projects whose `src` also contains internal packages
outside the enhancer's supported inventory. It does not invent semantic context.

The generator reuses GNATDOC-032's verifier: fresh compilation once per unit,
one validated ALI index, exact call-token coordinates, unique static `s` references,
and equality with precise canonical Libadalang declaration file/line/column/hash.
A single Libadalang project context is reused across occurrences. Native selection
then reuses the enhancer's complete public-profile reconciliation. Names, argument
counts, declaration order and compilation success **never select an overload**.

Generation returns a JSON summary (mapping digest and accepted/skipped counts).
Compiler/setup failures exit nonzero without writing a mapping. Individual
unsupported/nonpublic occurrences are recorded in `skipped`, not linked. Keep the
local `BUILD.receipt.json` and build artifacts for forensic evidence. The local
receipt includes tool binaries, evaluated project closure, semantic environment,
dependency hashes, commands, outputs and timings. It is not a portable receipt.

## Publish with explicit project configuration

Copy the mapping and its bound source/project inputs into your project-owned
publishing snapshot. Preserve their relative paths and bytes. Obtain the mapping
pin using `sha256sum`; do not copy a pin from mutable output metadata.

```toml
[guides]
mode = "authored-markdown"
# Existing authored manifest and pin remain required.
manifest = "docs/authored.json"
sha256 = "<existing authored manifest SHA-256>"
ada_example_highlighting = true
ada_example_api_links = true

[guides.verified_examples]
mapping = "docs/verified-examples.json"
sha256 = "<mapping file SHA-256>"
```

The authored manifest must use `exact-examples`: every published Ada fence is
byte-exactly one complete authoritative source file, covered by the existing
example-build contract. Incomplete fragments receive no compiler links. Landing
examples are not enabled by this initial mapping interface. Unrelated lexical
links retain their existing conservative behavior. Verified spans override only
overlapping lexical links; generated anchors never nest or overlap.

There is **no new human approval workflow**. Explicit project configuration and
its pin choose the trusted compiler output. Pinning is **not a cryptographic
attestation of human review**, nor proof against someone who can rewrite both
configuration and evidence. Review/access control of project-owned inputs is an
operator responsibility, just as for public sources and native snapshots.

## Portable schema 1

All paths are relative, all coordinates are one-based, and token `start`/`end`
offsets are zero-based ASCII byte offsets with exclusive `end`. Tabs, non-ASCII
Ada, source remapping and CRLF examples are not qualified. Output uses sorted JSON
keys, sorted source/occurrence order, no timestamps or host paths. The same frozen
inputs/toolchain produce identical output across fresh builds (including `-O`).

Top-level fields:

* `schema_version = 1`;
* `inputs`: SHA-256 for compiler source dependencies, example units and project/
  configuration inputs (the full frozen snapshot is also fingerprinted);
* `native_sha256`: fingerprint of observed package pages and their complete
  declaration names/profiles/anchors;
* `provenance`: `compiler`, `libadalang`, `project`, `evidence`, `ali` SHA-256
  fingerprints. The project fingerprint includes evaluated configuration and
  scenarios; local receipt paths are normalized in the portable fingerprint;
* `mappings`: accepted records;
* `skipped`: source, line, column, explicit status and reason for other indexed
  subprogram occurrences. This is not a census of every Ada expression.

Each accepted record contains its own schema version, authoritative `source`
path/hash, exact `occurrence` line/column/token offsets/text, both `selected`
(canonical LAL, including kind) and `compiler_selected` file/line/column/hash,
canonical qualified `identity`, complete source `profile`,
`classification = "explicit-static-subprogram-call"`, and `evidence_sha256` binding
the provenance. **No URL grants authority**. The consumer reconstructs a unique
destination from current public source and observed native profile/anchor, checking
all input hashes, both declaration identities and exact complete example bytes.

Missing, malformed, duplicate, conflicting, stale, incomplete or unsupported
configured mappings abort enhancement before publication. Editing a mapping
requires updating its project pin; that alone cannot bypass source/native checks.
Changing sources/projects/native evidence requires fresh generation. Disabled
configuration never reads mappings and preserves previous output bytes.

Portable ALI fingerprints bind the verifier's parsed cross-reference evidence,
not timestamp-bearing raw ALI/object bytes. Exact raw artifact hashes remain in
the retained local receipt. Copying byte-identical sources with different mtimes
does not change the portable mapping.

## Validated scope and reproduction

Retained source-backed controls under `tests/verified-fixtures` contain **16
verified call sites**, four in authentic Core (`Create`, Mat `Clone`, `Rows`,
`Columns`) and twelve in the GNATDOC-032-derived static overload fixture (Mat/UMat,
Integer/String, named/defaulted and contextual return overloads). Rendering adds
sixteen compiler links, plus two unchanged lexical Mat type marks in the Core
fence. This does not claim coverage of existing production guide fragments.

```sh
python -m unittest discover -s tests -p test_verified_examples.py -v
python -O -m unittest discover -s tests -p test_verified_examples.py -v
python scripts/check_verified_examples_browser.py --workspace /new/browser-check
# In the qualified private GNAT/LAL environment:
GNATDOC033_COMPILER=/qualified/bin/gprbuild \
  python -m unittest discover -s research/gnatdoc033 -v
```

Generics/instantiations, renamings, dispatching calls, implicit/inherited or local
declarations, nested/generic public scopes, operators and unsupported ALI syntax
remain unlinked. No arbitrary incomplete-fragment inference, dynamic dispatch
resolution, general Ada semantic analyzer, deployment or release is included.
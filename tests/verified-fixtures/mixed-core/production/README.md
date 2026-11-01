# opencv_core_ada

[![OpenCV Compatibility](https://github.com/zackboll/opencv_core_ada/actions/workflows/opencv-compatibility.yml/badge.svg)](https://github.com/zackboll/opencv_core_ada/actions/workflows/opencv-compatibility.yml)

A thick, idiomatic Ada 2022 binding for the **OpenCV Core** module.
Controlled resources, strong types, typed access and Ada exceptions keep the
C++ ABI out of normal application code.

**Documentation**

- [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html)
- [Documentation Home](https://zackboll.github.io/opencv_core_ada/)
- [Published Developer Guides](https://zackboll.github.io/opencv_core_ada/#developer-guides)
- [Building and Contributing](docs/documentation.md)
- [Practical Core roadmap and current status](docs/core-roadmap-reconciliation.md)
- [Native runtime version and build information](docs/native-runtime-identity.md)

The documentation site publishes styled HTML versions of the five developer
guides. Repository-relative guide links below remain links to their authoritative
Markdown sources on GitHub.

> **Current crate version:** `0.5.2` (`alire.toml`). The existing
> [`0.5.2` source tag](https://github.com/zackboll/opencv_core_ada/tree/0.5.2)
> predates merged FIN-02; see the [current reconciliation](docs/core-roadmap-reconciliation.md)
> and historical [release preparation record](docs/release-0.5.2-preparation.md).
> **Earlier source release:** [`0.5.1`](https://github.com/zackboll/opencv_core_ada/tree/0.5.1)
> (immutable source tag; no separate GitHub Release object).
> **Latest indexed release:** [`0.5.0`](https://github.com/alire-project/alire-index/blob/stable-1.4.0/index/op/opencv_core/opencv_core-0.5.0.toml).
> The separate [0.5.1 Alire submission, PR #2243](https://github.com/alire-project/alire-index/pull/2243),
> remains pending. No new index submission or release is made by this reconciliation.
> `alr with opencv_core` selects an indexed release, not current main.
>
> **Compatibility:** OpenCV **4.1 through 5.0**, inclusive, with one public Ada
> API. Not every intermediate release is explicitly tested.
>
> **Status:** active, pre-1.0 API. Merged CORE-FIN-02 qualification:
> **2,052 successful registered AUnit tests on each of OpenCV 4.1, 4.6, 4.10 and 5.0**,
> zero failed assertions or unexpected errors. See [exact-source evidence and
> remaining limits](docs/core-roadmap-reconciliation.md#qualification-and-provenance-boundaries).
> FIN-01's 2,037-test campaign remains historical; neither is whole-Core qualification.
>
> **Scope:** Core only. Image processing, codecs, GUI, video, feature detection,
> calibration and neural-network modules belong in separate dependent crates.

## Features

- Runtime-typed, controlled `Mat` and `UMat`, shallow assignment and explicit
  deep copies; 2-D and N-D construction and shared regions/slices.
- `Sparse_Mat` with typed stored-node access and dense/sparse conversion.
- Scalar and Vec2/Vec3/Vec4 access for all eight public depths, including exact
  binary16 storage access; copied rows and scoped zero-copy rows/buffers.
- Packed and strided callback-scoped views over caller-owned Ada storage.
- Arithmetic and reusable destinations, masks, channels, reductions, statistics,
  linear algebra, decompositions, spectral transforms, RNG and clustering.
- Bounded Mat/scalar arithmetic (including reverse subtraction/division) and
  single-channel scalar comparison, with allocating and reusable destinations.
- XML/YAML/JSON persistence on disk and in memory, including nested structures.
- Callback-scoped interoperability for cooperating OpenCV module bindings.

## Project names

Several related names appear in the repository:

| Purpose | Name |
| --- | --- |
| GitHub repository | `opencv_core_ada` |
| Alire crate | `opencv_core` |
| GPR project | `OpenCV_Core` |
| Ada API root | `OpenCV` |
| Core Mat API | `OpenCV.Core` |
| Built library name | `opencv_core_ada` |

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Ownership, views, and zero-copy access](#ownership-views-and-zero-copy-access)
- [Typed access matrix](#typed-access-matrix)
- [Public API overview](#public-api-overview)
- [Sparse matrices](#sparse-matrices) and [persistence](#persistence)
- [OpenCV compatibility](#opencv-compatibility) and [known limitations](#known-limitations)
- [Running the tests](#running-the-tests) and [contributing](#contributing)
- [License](#license)

## Installation

Development API addition: [numerical norms and binary descriptor distances](docs/numerical-norms.md)
documents `Difference_Norm`, direct squared-L2 reductions and native
Hamming/Hamming2, with explicit portable depth and count limits.

The Alire crate name is **`opencv_core`**, not `opencv_core_ada`:

```sh
alr with opencv_core
```

This selects an indexed release. Examples and advanced guides in this checkout
describe the development API; consult the matching release specifications when
using a published version. Install the native OpenCV development library first.
On Debian/Ubuntu, the native prerequisites can be installed with:

```sh
sudo apt-get install build-essential libopencv-dev pkg-config
```

For an explicit AArch64 GNAT Pro / Yocto SDK, use the opt-in
[`scripts/cross_install_core.sh` workflow](docs/cross-install-core.md).
It bootstraps GPRconfig, builds in isolation and recursively installs Core plus
the C++ shim, retaining a configuration for external cross-consumers. It accepts
clean Git or unpacked candidate sources; native Alire behavior is unchanged.

## Requirements

A normal build requires:

- an Ada toolchain supported by Alire;
- **Alire**;
- a C++17 compiler;
- **pkg-config**;
- OpenCV development headers and libraries in the supported 4.1-5.0 range;
- the OpenCV Core library (`opencv_core`).

The project links against:

```text
opencv_core
libstdc++   (Linux)
libc++      (macOS)
```

On macOS the C++ shim is compiled with Apple `clang++` and linked against
`libc++` so it matches Homebrew OpenCV. Ada remains on the GNAT toolchain.
Linux continues to compile C++ with `g++` and link `libstdc++`.

The compatibility containers currently use Alire 2.1.1, GNAT 16.1.0, and
GPRbuild 26.0.1. Those pinned versions make CI reproducible; they are not a
claim that every local build must use exactly those versions.

OpenCV include and library paths are discovered by:

```text
scripts/configure_opencv.sh
```

The script accepts pkg-config metadata under `opencv5`, `opencv4`, or `opencv`.

---

## Building

Clone and build:

```sh
git clone https://github.com/zackboll/opencv_core_ada.git
cd opencv_core_ada
alr build
```

The Alire pre-build action runs `scripts/configure_opencv.sh`, which creates the
local OpenCV GPR configuration from pkg-config metadata.

If configuration fails, first check what OpenCV pkg-config name is available:

```sh
pkg-config --modversion opencv5 || \
pkg-config --modversion opencv4 || \
pkg-config --modversion opencv
```

The GPR project supports the standard library kinds through
`OPENCV_CORE_LIBRARY_TYPE` (falling back to `LIBRARY_TYPE`):

```text
static-pic    (default)
static
relocatable
```

For example:

```sh
OPENCV_CORE_LIBRARY_TYPE=relocatable alr build
```

Both Ada and C++ are compiled with warnings promoted to errors. C++ is compiled
as C++17 with `-Wall -Wextra -Wpedantic -Werror`.

---

## Quick start

### Create and access a matrix

```ada
with Ada.Text_IO;
with OpenCV;
with OpenCV.Core;
with OpenCV.Core.UInt8_Access;

procedure Example is
   use OpenCV.Core;

   Image : Mat :=
     Create
       (Rows         => 480,
        Columns      => 640,
        Element_Type => (Depth => UInt8, Channels => 1));

   Value : OpenCV.UInt8_Value;
begin
   OpenCV.Core.UInt8_Access.Set
     (Image, Row => 10, Column => 20, Value => 255);

   Value :=
     OpenCV.Core.UInt8_Access.Get
       (Image, Row => 10, Column => 20);

   Ada.Text_IO.Put_Line (OpenCV.UInt8_Value'Image (Value));
end Example;
```

`Create` follows native `cv::Mat` allocation semantics: newly allocated element
storage is **not automatically zero-filled**. Initialize explicitly when a
known initial value is required:

```ada
Image.Set_To (OpenCV.Make_Scalar (0.0));
```

### Clone and check the shape

The repository's complete [qualified example](docs/example.adb) demonstrates
deep copying and shape inspection:

```ada
with OpenCV.Core;

procedure Example is
   use OpenCV.Core;
   Image : constant Mat := Create (2, 3, (Depth => UInt8, Channels => 1));
   Copy  : constant Mat := Image.Clone;
begin
   pragma Assert (Copy.Rows = 2 and then Copy.Columns = 3);
end Example;
```

Build and execute it from the checkout root using the supported Alire environment:

```sh
alr build
alr exec -- gprbuild -P docs/example.gpr
obj/docs-example/example
```

`Copy : Mat := Image;` would instead share storage. `Clone` allocates independent
storage; it does not initialize previously unwritten elements. The element-access
example above writes the element before reading it.

## Documentation

| Resource | What to find there |
| --- | --- |
| [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) | Complete public package index, declaration profiles, exceptions and contracts |
| [Documentation Home](https://zackboll.github.io/opencv_core_ada/) | Published Pages entry point and basic usage |
| [Ownership and views](docs/ownership-and-views.md) | Shallow/deep copies, ROI geometry, borrowed rows/buffers, external and selected views, UMat |
| [Typed access guide](docs/typed-access-guide.md) | Shared values, depth/channel support matrix, scalar/vector families and Float16 details |
| [Core operations guide](docs/core-operations-guide.md) | Destination reuse and overlap rules, numerical caveats, masks, algebra, transforms and clustering |
| [Sparse matrices and persistence](docs/sparse-and-persistence-guide.md) | Sparse nodes, dense conversion, nested FileStorage examples and type policy |
| [Interoperability and compatibility](docs/interop-and-compatibility.md) | Module bridge, version/platform policy, full limitations, architecture, build and contributor details |
| [Non-Alire GPR consumers](docs/non-alire-gpr-consumers.md) | Installed Core, direct GPRbuild, Debian 12 qualification, mixed Ada/C++ linkage and relocation |
| [Building and Contributing](docs/documentation.md) | Reproducing GNATdoc, comment policy, comparator and Pages review gate |
| [Changelog](CHANGELOG.md) | Release history and unreleased changes |

The Markdown guides live in the **GitHub repository**, not inside the generated
GNATdoc site. Navigate generated package pages through the API index: their
hashed filenames are not stable handwritten links.

## Ownership, views, and zero-copy access

- Ordinary `Mat` and `UMat` assignment creates a distinct native header but
  shares reference-counted storage. Writes through an alias affect shared pixels.
  Finalization destroys that header; storage survives while another owner holds it.
- `Clone` is the explicit independent deep copy. Use it when later writes must
  not affect the source.
- `Region` and N-D `Slice` share storage and retain the allocation. Each header
  has its own geometry. A Region can be non-contiguous.
- Row callbacks overlay one logical row, including rows of gapped 2-D Regions.
  Whole-buffer callbacks require continuous storage and expose complete elements
  in final-dimension-fastest order, not individual channels.
- Borrowed references/addresses are valid **only during the callback**. A shallow
  lease keeps OpenCV-owned storage alive; it is not a lock or concurrency guarantee.
- External Mat views instead refer to **caller-owned** `aliased` Ada buffers.
  OpenCV neither copies nor frees those buffers. The caller must keep them alive
  throughout the callback; a lease cannot extend their lifetime.
- Temporary external/selected Mat views cannot escape through assignment or
  general no-copy views and cannot be general output destinations. Supported
  typed writes are immediate; `Clone` is the independent escape path.
- UMat is not a guarantee of GPU execution. Explicit transfers in
  `OpenCV.Core.Transfers` create independent copies, not mapped Mat views.

See [Ownership and views](docs/ownership-and-views.md) for complete examples,
read-only restrictions, strided-buffer formulas, retained ROI geometry and UMat
behavior. Operations have distinct overlap contracts: do not infer that all
shared-storage destinations are safe from ordinary assignment semantics.

## Shared value types

`OpenCV` owns shared numeric values, points, sizes, rectangles, `Scalar`,
`Border_Kind` and `Angle_Unit`. `OpenCV.Core` owns matrix-specific types.
There are no Core compatibility aliases for relocated root types.
See [Shared value types](docs/typed-access-guide.md#shared-value-types) for the
migration table and 3-D value families included in the indexed `0.5.0` release.

## Typed access matrix

`Mat` remains runtime-typed, not generic. Separate typed packages validate the
runtime depth and channel count before accessing data. All eight public depths
have C1 scalar and C2/C3/C4 vector element, row, buffer and external-view families.
Float16 storage access preserves the exact binary16 encoding; arithmetic has
different numerical guarantees.

See the [full typed access matrix](docs/typed-access-guide.md#typed-access-matrix)
for package spellings, bit-preservation policy and representation details.

## Public API overview

Use the [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html)
for exact declarations and per-overload restrictions. The
[Core operations guide](docs/core-operations-guide.md#public-api-overview)
groups the operation families and preserves destination examples, numerical
formulas, alias restrictions and version-specific behavior.

### Conversion and element-wise mathematics

Conversion and reusable destinations can preserve compatible storage or detach
a header after layout changes. Empty metadata and precision can vary by native
version. See [conversion semantics](docs/core-operations-guide.md#conversion-and-element-wise-mathematics).

## Reusable paired polar destinations

`Cart_To_Polar` and `Polar_To_Cart` provide allocation-returning functions and
paired caller-owned destination procedures for Mat and UMat. Their two-output
identity and overlap rules are stricter than single-output reuse. See
[paired polar examples and restrictions](docs/core-operations-guide.md#reusable-paired-polar-destinations).

## Sparse matrices

`OpenCV.Core.Sparse.Sparse_Mat` is a controlled N-D sparse object, not a dense
Mat view. Assignment shares sparse storage; `Clone` is independent. Missing
typed reads return zero without insertion; writing zero can retain a stored node.
See [Sparse matrices](docs/sparse-and-persistence-guide.md#sparse-matrices) for
typed access, iteration, conversion and stored-node semantics.

## Linear algebra and decomposition

Determinant, solve/invert, GEMM, covariance, eigen decomposition, PCA, LDA and
SVD use OpenCV algorithms. LU and SVD failure/rank policies differ; see
[Linear algebra and decomposition](docs/core-operations-guide.md#linear-algebra-and-decomposition).

## Spectral transforms

DFT/DCT, inverse transforms and spectral multiplication include packed CCS and
row-wise forms. Consult [Spectral transforms](docs/core-operations-guide.md#spectral-transforms)
for layout, scaling, size and channel constraints.

## Random numbers, clustering, and nearest neighbors

Default and caller-owned RNG workflows, fills, shuffle, K-means and batch
distance are described in [Random numbers, clustering, and nearest neighbors](docs/core-operations-guide.md#random-numbers-clustering-and-nearest-neighbors).

## Persistence

`OpenCV.Core.Persistence.File_Storage` is limited controlled and exclusively
owns its native storage. XML/YAML/JSON disk and memory backends support nested
maps/sequences without exposing `FileNode` lifetimes. Missing nodes raise
`OpenCV_Error`; node types are not silently coerced to arbitrary requested types.
See [Persistence](docs/sparse-and-persistence-guide.md#persistence) for complete
examples, format distinctions, integer limits and embedded-NUL restrictions.

## UMat and the Transparent API baseline

UMat has shallow assignment, deep `Clone`, native operations and independent
host transfers. Mixed Mat/UMat inputs or masks and direct mapped typed UMat access
are not supported. OpenCL is optional. See the
[UMat baseline](docs/ownership-and-views.md#umat-and-the-transparent-api-baseline).

## OpenCV compatibility

The supported compatibility range is **OpenCV 4.1 through 5.0**. One public Ada
API is used across the range; callers do not select version-specific Ada
packages or conditional APIs.

GitHub Actions currently tests these representative targets:

| OpenCV target | CI environment | OpenCV installation |
| --- | --- | --- |
| `4.1.0` | Debian 12 | Core-focused source build |
| `4.6` | Debian 12 | Distribution development package |
| `4.10` | Debian 13 | Distribution development package |
| `5.0.0` | Debian 13 | Core-focused source build |

These are **validation points, not an exhaustive list of supported releases**.
Intermediate releases within the supported range are not all individually run
in CI.

Version discovery probes `opencv5`, `opencv4`, then `opencv`. Native Ubuntu
24.04 ARM64 is an additional architecture validation point. Windows MSYS2 and
macOS MacPorts jobs that are skipped are **not passes**. Detailed platform,
constructor and compatibility information is in
[OpenCV compatibility](docs/interop-and-compatibility.md#opencv-compatibility).

### GNAT 12 and AArch64 qualification

Historical Debian 12 native GCC/GNAT **12.2.0**, its matching runtime, and
OpenCV 4.6 qualification covered the production binding and **2,025 AUnit tests** with
release-profile production, and installed/relocated Ada-only and mixed Ada/C++
consumers. Select the compiler explicitly; GNAT 12 and GNAT 16 ALIs/runtimes
are not interchangeable. See the [GNAT 12 integration record](docs/gnat12-completion.md#native-gnat-12-and-consumers).

The local generic Linux AArch64 qualification uses public Debian GCC/GNAT/G++
12.2.0 and a target OpenCV 4.6 sysroot. The entire library and shim compile,
install, and cross-link independent Ada and mixed consumers; ELF inspection
confirms AArch64 objects and target dependencies. **Target executables were
not run in that historical Debian campaign**. See the [cross qualification record](docs/gnat12-completion.md#full-aarch64-cross-qualification)
and [generic cross-build inputs](docs/generic-aarch64-cross-build.md).

Separately, [GNAT Pro 25.2 / Scarthgap qualification](docs/adacore25-scarthgap-core-aunit.md)
records AArch64 QEMU execution with GCC 13.3.1, the Scarthgap 5.0 sysroot and
OpenCV **4.9.0**: all **2,025 AUnit tests**, the instrumented all-family suite
and additional safety controls passed. This is not a fifth hosted OpenCV
matrix entry and does not imply hardware qualification. **Target hardware is
NOT TESTED.** Later scalar-mode QEMU/sanitizer evidence is recorded separately
in [CORE-FIN-01-R3](docs/core-fin-01-r3-target-sanitizers.md). Neither campaign
is the user's GNAT Pro **25.0w / GCC 12.3.1** profile: that profile's automatic
cross-install and external-consumer cross-link qualification carries forward
only for identical implementation inputs, as documented in the
[0.5.2 preparation record](docs/release-0.5.2-preparation.md).

Alire's default root development profile enables `-gnatVa`, which rejects IEEE
NaN/infinity in eight existing tests. Release-profile production passes those
tests without weakening their checks. On fresh sources, root `alr test` passes: its
second action builds Core as a release-profile dependency of the checked tests
crate, after the first action's development build. Explicitly forcing Core's
development profile during test execution still fails those eight IEEE tests,
and a saved override can also make subsequent root test actions fail. Use a
fresh deployment for publication qualification, not a diagnostic workspace.
See [release preflight](docs/release-0.5.2-preparation.md).

## Known limitations

- Many algorithms remain 2-D even though N-D storage, access, slices and views
  are available. OpenCV 4.x supports up to 32 dimensions; OpenCV 5.0's native
  MatShape capacity limits Mat/UMat construction and related views to 10.
- Whole-buffer borrowing requires continuity; selected views must retain the
  final dimension and are callback-scoped. External buffers must include the
  required native span, including outer padding for strided N-D views.
- Typed/zero-copy C1–C4 coverage does not imply every depth/channel combination
  is supported by every Core algorithm. Float16 algorithm coverage is deliberately
  qualified and version-dependent.
- Partial storage overlap is not generally supported. Reusable destinations
  have operation-specific alias rules; post-native failure rollback is not
  generally promised.
- UMat does not guarantee GPU execution, expose OpenCL contexts/queues or offer
  direct mapped typed access. Mat/UMat APIs are not completely symmetric.
- Persistence has native format constraints, a restricted signed integer write
  range, and embedded-NUL restrictions. Numerical results can depend on native
  version, backend and SIMD dispatch.
- The API is pre-1.0, Core-only, and does not claim exhaustive C++ symbol coverage
  or a formal proof of native ownership/numerical behavior.

The [complete known limitations](docs/interop-and-compatibility.md#known-limitations)
remain available; consult them before selecting an advanced API.

## Running the tests

Tests live in a separate Alire crate under `tests/`:

```sh
alr -C tests build
alr -C tests run
```

The crate also defines root test actions:

```sh
alr test
```

Both the root actions and the separate release-profile suite are qualified;
their profiles differ from explicitly forcing development-profile production.
Release qualification explicitly uses
`alr build --release` in the root and
`alr -C tests build --profiles=opencv_core=release`, followed by
`alr -C tests run`; the checked test harness is retained. Publication-profile
checks are tracked separately in the [release preflight](docs/release-0.5.2-preparation.md).

The test crate carries development-only dependencies such as AUnit, GNATprove,
and GNATcov. They are intentionally not dependencies of the public library
crate.

Merged FIN-02 qualification records **2052 registered AUnit tests**; see the
[current evidence and limits](docs/core-roadmap-reconciliation.md#qualification-and-provenance-boundaries).
Coverage includes ordinary behavior, invalid input, shape/depth/channel
compatibility, empty Mats, non-contiguous Regions, shallow-versus-independent
ownership, callback lifetimes, arbitrary Ada array lower bounds, failure
atomicity, persistence, numerical boundary behavior, and version compatibility.

The `OpenCV Compatibility` GitHub Actions workflow runs the same test suite
against all four compatibility targets listed above, and on native Ubuntu 24.04
ARM64. `fail-fast` is disabled so a failure on one target does not hide the
state of the others.


## Goals and scope

The goal is portable user-facing Core coverage with an idiomatic Ada design,
not a mechanical C++ header translation. See the
[design principles](docs/interop-and-compatibility.md#goals-and-scope).

## Architecture

Dependencies flow downward: thick public Ada API → private thin C interop →
C++ shim → OpenCV Core. C++ ABI details and exceptions do not cross into the
normal application API. See [Architecture](docs/interop-and-compatibility.md#architecture).

## Cross-module interoperability

Applications use the public module packages. Cooperating module implementations
use callback-scoped capabilities and the installed Core bridge, without taking
ownership of borrowed native objects. See
[Cross-module interoperability](docs/interop-and-compatibility.md#cross-module-interoperability)
and the [installed consumer qualification](docs/windows-external-shim-install.md).

## Safety and validation boundary

The thick Ada layer owns public semantic validation. The C++ shim protects ABI
and memory safety and translates native exceptions into explicit errors;
the public layer normally raises `OpenCV_Error`. Mathematical result types may
represent ordinary algorithm failure explicitly. See
[Safety and validation boundary](docs/interop-and-compatibility.md#safety-and-validation-boundary).

## SPARK and GNATprove

Proof is scoped to small pure-Ada arithmetic/conversion helpers, not the foreign
library. GNATprove and GNATcov belong to the separate tests crate. See
[SPARK and GNATprove](docs/interop-and-compatibility.md#spark-and-gnatprove).

## Project layout

Public specifications/bodies are under `src/`, private interop under
`src/internal/`, the native shim under `cpp/`, and AUnit tests under `tests/`.
`docs/` holds repository guides and the Pages landing-page source; generated
`_site/` HTML is transient and must not be committed. See the
[full project layout](docs/interop-and-compatibility.md#project-layout).

## Development approach

Develop vertically: inspect upstream semantics, design the Ada operation, add
only the required shim/thin surface, add focused public-API tests, format, build
and qualify the exact branch head. See
[Development approach](docs/interop-and-compatibility.md#development-approach).

## Contributing

New work starts on a feature branch, or on a corrective branch for focused
repairs. A larger cohesive vertical bundle is acceptable when its public API,
ABI, ownership, tests, and documentation are reviewed together; unrelated
speculative batches and broad rewrites remain prohibited.

Complete local formatting, builds, and tests before final submission. Cline
then commits and pushes the source branch and opens a real pull request against
`main`. Pull requests remain open and unmerged pending review, with auto-merge
disabled. Corrective review work continues on the same pull-request branch and
must be revalidated at its new head. Completion reports identify the exact
locally tested and pushed source SHA rather than relying only on a PR merge-ref
result.

Contributions should preserve the central abstraction boundary:

```text
idiomatic Ada
    |
    v
thin fixed C ABI
    |
    v
C++ shim
    |
    v
OpenCV Core
```

Please avoid:

- exposing `Interfaces.C`, status codes, raw handles, or raw pointers in the
  normal public API;
- passing C++ objects through Ada;
- leaking OpenCV-version conditionals into the public Ada API when the shim can
  absorb them;
- mechanically reproducing C++ overloads without considering Ada ergonomics;
- exposing raw OpenCV integer flags when a strong Ada type is suitable;
- silently changing shallow/deep ownership semantics;
- adding test/proof/coverage tooling to the public crate merely for development
  convenience;
- manually reimplementing an OpenCV algorithm when a corresponding Core
  primitive exists and is available across the compatibility strategy;
- suppressing warnings simply to make a build pass;
- broad unrelated cleanup in otherwise focused feature changes.

Small, vertically complete features with focused tests are preferred over large
partially integrated batches.

## Versioning

The current manifest is `0.5.2`; its existing source tag predates FIN-02 on main.
This reconciliation is not a new release or publication claim. The latest accepted
Alire release is `opencv_core=0.5.0`, with 0.5.1 pending separately in PR #2243.
Unlike the tooling-only 0.5.1 patch, 0.5.2 includes fourteen additive public
scalar overloads already merged into main. Existing declarations and ownership
semantics are preserved, but Ada overload resolution in unusual client code
may need explicit qualification. This user-selected pre-1.0 patch number is not
a claim of a frozen, stable-API SemVer patch policy. See the
[versioning review](docs/release-0.5.2-preparation.md#versioning-and-compatibility-review).
A Git tag alone is not evidence of Alire publication.
See [CHANGELOG.md](CHANGELOG.md) for UMat additions in 0.4.0, typed Mat/SparseMat
additions in 0.3.0, the source-breaking shared-value relocation in 0.2.0, and
the 0.5.0/0.5.1 releases and historical 0.5.2 preparation notes. The API remains experimental until 1.0.

## License

`opencv_core_ada` is licensed under the **Apache License 2.0**.

See [LICENSE](LICENSE) for the full license text.

OpenCV is a separate project with its own license and copyright holders.

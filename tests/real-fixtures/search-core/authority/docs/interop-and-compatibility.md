# Interoperability, compatibility and contributor architecture

[README](../README.md) · [GNATdoc API Reference](https://zackboll.github.io/opencv_core_ada/api/index.html) · [Building and Contributing](documentation.md)

This guide is published as HTML on the documentation site and maintained as
Markdown in the source repository. The public Ada specifications are authoritative for exact profiles
and per-overload restrictions. Examples below include both complete programs
and fragments intended for the surrounding application.

## Contents

- [Goals and scope](#goals-and-scope)
- [Cross-module interoperability](#cross-module-interoperability)
- [OpenCV compatibility](#opencv-compatibility)
- [Architecture](#architecture)
- [Requirements](#requirements), [building](#building) and [tests](#running-the-tests)
- [Safety and validation boundary](#safety-and-validation-boundary)
- [SPARK and GNATprove](#spark-and-gnatprove)
- [Known limitations](#known-limitations)
- [Project layout](#project-layout) and [installed consumer](#installed-core-mat-consumer)
- [Development approach](#development-approach) and [contributing](#contributing)

## Goals and scope

The project is designed around the following principles:

- Provide an **idiomatic Ada API** rather than reproducing C++ syntax.
- Keep C++ implementation details behind a stable **`extern "C"` ABI**.
- Never expose `cv::Mat`, C++ references, templates, STL containers,
  `std::string`, C++ exceptions, raw C status codes, or `Interfaces.C` types in
  the normal public Ada API.
- Represent OpenCV resources with Ada controlled types and preserve OpenCV's
  reference-counted ownership semantics where that is the correct model.
- Prefer strong Ada enums, records, subtypes, discriminated result types,
  generics, overloads, and exceptions over integer flags and output-parameter
  conventions.
- Preserve important OpenCV behavior such as saturation, rounding,
  non-contiguous Regions, multi-channel layouts, floating-point edge cases,
  and version-specific numerical behavior where it affects correctness or
  safety.
- Keep compatibility handling below the public Ada layer whenever practical.
- Keep AUnit, GNATprove, GNATcov, formatting tools, and other development-only
  dependencies out of the public crate.
- Use SPARK selectively for small pure-Ada safety properties where formal proof
  gives a concrete guarantee.
- Inspect authoritative OpenCV declarations and source when exact behavior or
  safety differs from a high-level API description.

Features are built vertically:

```text
public Ada API
     -> thin private Ada C interop
     -> stable C ABI / C++ shim
     -> OpenCV Core
     -> focused AUnit coverage
```

Literal symbol-for-symbol coverage of every internal OpenCV Core implementation
surface is not a goal. The target is broad coverage of portable, user-facing
Core functionality with a coherent Ada design.

---

## Cross-module interoperability

Module crates such as `opencv_imgproc`, `opencv_imgcodecs`,
`opencv_highgui`, `opencv_videoio`, `opencv_features2d`, and
`opencv_calib3d` depend on `opencv_core`. Application code continues to use
the public Core types such as `OpenCV.Core.Mat`, `OpenCV.Core.UMat`, and
`OpenCV.Core.Sparse.Sparse_Mat`; no public raw-pointer API is introduced.

`OpenCV.Core.Module_Interop` is a deliberately low-level binding
implementation interface for those crates. Its callback-scoped input and
output handles are passed only to a module's private Ada/C++ interop. Core
provides the installed `opencv_core_module_bridge.hpp` header for the module
shim. The header is installed in the dependent project's `include` artifact
directory by the Core GPR project, rather than being found through a
repository-relative path.

The bridge does not copy pixel data. Core remains the sole creator, owner, and
destroyer of Core `cv::Mat` headers and opaque wrappers. A cooperating module
shim may borrow the native header only for its callback/call scope, must never
store or delete it, and must be compiled against the same compatible OpenCV ABI
and installation as Core. Input handles permit inspection, including temporary
external-buffer views. Output handles expose the actual Core header so an
OutputArray operation can allocate or rebind it; temporary external-buffer
views are rejected for output because rebinding would violate their no-escape
ownership contract.

UMat capabilities in `OpenCV.Core.Module_Interop` likewise borrow the actual
Core-owned header through callback-scoped `Input_UMat_Handle` and
`Output_UMat_Handle`. The installed typed C++ bridge performs no Mat transfer
or mapping. Output operations may rebind that header, including ordinary UMat
Regions. Core retains ownership; modules must neither retain nor delete the
borrowed header and must use the same compatible OpenCV ABI and installation.
This is module implementation infrastructure, not an application raw-handle API.

`OpenCV.Core.Sparse.Module_Interop` is the same kind of implementation
interface for `Sparse_Mat`. OpenCV 4.1.0, 4.10.0, and 5.0.0 Imgproc all
declare `calcHist` with a mutable `SparseMat&` output and `calcBackProject`
and `compareHist` with `const SparseMat&` inputs. The installed bridge
therefore exposes callback-scoped input and output resolvers. Core remains
the sole owner of the opaque wrapper and the native `cv::SparseMat` header.
A module shim borrows that header only during the callback, must neither
delete nor retain it, and does not copy node storage. Output resolution
returns the actual Core header so `SparseMat::create` can replace its shape
in place. SparseMat has no temporary external-buffer view, so output
resolution does not apply the Mat external-view rejection. Imgproc histogram
operations themselves are not part of this Core crate.

---

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

Row-strided external views use the longstanding
`cv::Mat(rows, cols, type, data, step)` constructor. The OpenCV 4.1.0 and 5.0.0
headers both declare this overload with `size_t step`; both document `step` in
bytes, including row-end padding, and state that data is neither copied nor
automatically deallocated. The binding uses the same ABI path across the
supported range.

GitHub Actions also runs the same public test path natively on Ubuntu 24.04
ARM64 against the distribution OpenCV packages. That job is for architecture
portability, not another OpenCV-version matrix entry.

Version differences are isolated in the configuration and C++ shim layers.
Depending on the linked OpenCV release, the shim may use a native API, a
compatible older signature, or a behavior-preserving fallback. This includes
older Core APIs whose signatures or availability changed over the lifetime of
OpenCV 4.x and empty-`Mat` behavior that changed in OpenCV 5.

OpenCV discovery is intentionally version-tolerant. `scripts/configure_opencv.sh`
probes the following pkg-config package names in order:

```text
opencv5
opencv4
opencv
```

It also handles the legacy include-directory variable used by early supported
4.x pkg-config files.

---

## Architecture

The binding is deliberately layered:

```text
Ada application
     |
     v
+-------------------------------------------+
| Thick Ada API                             |
| OpenCV shared values / OpenCV.Core        |
| controlled types, strong enums, records   |
| exceptions, generics, scoped callbacks    |
+-------------------------------------------+
     |
     v
+-------------------------------------------+
| Thin private Ada interop                  |
| OpenCV.Internal.C_API                     |
| fixed-width C ABI types                   |
+-------------------------------------------+
     |
     v
+-------------------------------------------+
| C++ shim / stable C ABI                   |
| extern "C"                                |
| opaque handles, exception containment     |
| OpenCV-version compatibility handling     |
+-------------------------------------------+
     |
     v
+-------------------------------------------+
| OpenCV Core                               |
| cv::Mat / cv::FileStorage / cv::*         |
+-------------------------------------------+
```

### Thick Ada layer

The public layer is Ada-shaped:

- `Mat` is a tagged controlled type.
- ordinary `Mat` assignment is shallow, matching `cv::Mat` header semantics;
- `Clone` is the explicit deep-copy operation;
- `File_Storage` is a limited controlled type with exclusive ownership;
- normal failures raise `OpenCV_Error`, while mathematically meaningful
  success/failure states use discriminated result types where appropriate;
- multi-result OpenCV operations return Ada records instead of exposing output
  parameters;
- typed data access is exposed through dedicated child packages rather than raw
  pointers.

### Thin Ada interop

`OpenCV.Internal.C_API` defines the fixed C ABI used by the thick layer. It is
an implementation detail, not the normal application interface.

### C++ shim

The shim:

- exports only C-compatible functions;
- uses opaque handles for C++ objects;
- uses fixed-width integers and simple C-compatible records;
- validates raw ABI and memory-safety conditions;
- contains OpenCV-version-specific compatibility code;
- initializes caller-visible outputs before work that may fail;
- catches OpenCV, standard C++, and unknown exceptions;
- converts failures into stable status codes and diagnostic text;
- never allows a C++ exception or C++ object lifetime to cross directly into
  Ada.

---

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

## Running the tests

Tests live in a separate Alire crate under `tests/`:

```sh
alr -C tests build
alr -C tests run
```

The crate also defines a root test action, which is the release
entry-point gate:

```sh
alr test
```

The test crate carries development-only dependencies such as AUnit, GNATprove,
and GNATcov. They are intentionally not dependencies of the public library
crate.

At the time of this README update, the full suite contains **2025 AUnit tests**.
Coverage includes ordinary behavior, invalid input, shape/depth/channel
compatibility, empty Mats, non-contiguous Regions, shallow-versus-independent
ownership, callback lifetimes, arbitrary Ada array lower bounds, failure
atomicity, persistence, numerical boundary behavior, and version compatibility.

The `OpenCV Compatibility` GitHub Actions workflow runs the same test suite
against all four compatibility targets listed above, and on native Ubuntu 24.04
ARM64. `fail-fast` is disabled so a failure on one target does not hide the
state of the others.

---

## Safety and validation boundary

The project separates **public semantic validation** from **raw ABI safety**.

### Ada layer

The thick API normally validates caller-facing rules such as:

- shape compatibility;
- depth and channel restrictions;
- index and Region bounds;
- continuity requirements for whole-buffer borrowing;
- legal enum/mode combinations;
- non-empty requirements;
- exact caller-buffer shape/stride requirements for external views;
- string restrictions that cannot safely cross the underlying native
  interface.

### C++ shim

The shim defensively validates conditions a raw C caller could violate and
conditions needed to keep the C++ call safe:

- null handles and output pointers;
- fixed ABI enum decoding;
- pointer/count and byte-count relationships;
- signed arithmetic before OpenCV receives arguments;
- pointer alignment and row-step arithmetic for external Mat storage;
- failure-atomic handle publication;
- C++ exception containment.

### Source-backed safety boundaries

Where a supported OpenCV implementation contains signed intermediate arithmetic
or other source-level hazards, the binding establishes an Ada/C-ABI boundary
before the native call instead of relying on undefined behavior.

Examples in the current codebase include:

- signed product guards around SVD/pseudoinverse and related workspaces;
- eigensolver and decomposition size guards;
- DFT/DCT dimension and work-buffer arithmetic checks;
- persistence integer and embedded-NUL restrictions;
- exact external-buffer byte-count, stride, and alignment checks;
- prevention of shallow aliases escaping callback-scoped external-buffer Mats.

Compatibility code follows the same rule: version-dependent details belong in
the configuration/C++ boundary rather than leaking into the thick Ada API.

---

## SPARK and GNATprove

Formal verification is focused on small pure-Ada safety helpers rather than
foreign-resource ownership or OpenCV numerical algorithms.

The current proof island is:

```text
OpenCV.Internal.Safe_Arithmetic
```

with `SPARK_Mode => On`.

It currently contains proved contracts for:

- `Product_Exceeds_Signed_Int32`
- `Fits_Signed_Int32`
- `To_Signed_Int32`

This supports safe dimensional and ABI conversions without trying to prove the
C++ library itself.

GNATprove is supplied by the separate `tests` Alire environment.

---

## Known limitations

The current limitations are intentional and help keep the public API coherent:

1. **The dense public `Mat` model is primarily 2-D.**
   N-dimensional construction, UInt8/Int8/UInt16/Int16/Int32/Float16/Float32/Float64 C1
   Get/Set, UInt8/UInt16/Int16/Int32/Float16/Float32/Float64 C2 Vec2,
   UInt8/UInt16/Int16/Int32/Float16/Float32/Float64 C3 Vec3, and
   UInt8/UInt16/Int16/Int32/Float16/Float32/Float64 C4 Vec4 Get/Set, `Slice` views, `Shape`, and
   Shape-based N-D reshape are available. Callback-scoped whole-buffer
   borrowing is provided for continuous N-D Mats of every typed layout.
   Packed and strided (gapped) caller-owned external views support genuine
   N-D shapes for every typed layout. Callback-scoped dimension-dropping
   selected views (`With_Selected_View`) are available: any non-final
   dimensions may be fixed to one index and dropped while the others keep
   half-open ranges. The final source dimension must remain, because OpenCV
   always uses the element size as a Mat's last step, and at least two result
   dimensions must remain; there is no 1-D or scalar selected Mat
   representation yet. This is not a general NumPy-style indexing model:
   there is no step slicing, axis reordering, broadcasting, or
   dimension-dropping shallow `Mat` returned outside a callback. N-D row APIs
   are not provided because a row is a 2-D concept. OpenCV 5.0's native Mat
   shape capacity remains 10 dimensions.

2. **SparseMat and UMat are not complete native APIs.**
   UMat has no direct mapped typed access, public OpenCL controls or raw OpenCL
   handles, masked Set_To, mixed Mat/UMat operands, reshape, DFT/DCT overloads,
   or downstream Imgproc UMat overloads. Its arithmetic, bitwise/mask, and math
   subset and callback-scoped module bridge are available as described above.
   Direct typed node access and read-only stored-node traversal cover all eight
   depths in C1/C2/C3/C4 (32 layouts). One vector is one complete element.
   Explicit all-zero vectors remain stored nodes; missing reads return zero and
   do not create a node. Float16 components keep exact binary16 bits.
   `Convert_To` and numeric `To_Dense` cover stored-node scaling and
   sparse-to-dense scale/offset conversion for every depth except Float16,
   which OpenCV 4.1 through 5.0 does not implement in the sparse conversion
   tables. `Norm` and `Normalize` are restricted to Float32 and Float64 with
   exactly one channel; only stored nodes participate, and `Min_Max`
   normalization is unavailable. Broader sparse arithmetic, C5+ typed layouts,
   and native 1-D SparseMat are not wrapped. Native 1-D
   SparseMat is deliberately omitted because the dense interoperability model
   begins at 2-D.

3. **Typed direct/zero-copy access covers C1/C2/C3/C4 only.**
   Every supported depth — UInt8, Int8, UInt16, Int16, Int32, Float16,
   Float32, and Float64 — has complete C1/C2/C3/C4 typed and zero-copy
   coverage (32 layouts). UInt8, Int8, UInt16, Int16 and Int32 C1/C2/C3/C4 have 2-D and N-D Get/Set, copied and borrowed
   2-D rows, continuous whole-buffer borrowing, and packed or row-strided
   2-D caller-buffer views. Int8 preserves the exact signed domain `-128 .. 127`
   without unsigned or floating-point intermediates. Float16 C1 has 2-D and N-D Get/Set that
   preserve the exact binary16 encoding, plus copied and borrowed 2-D row
   access, continuous 2-D/N-D whole-buffer borrowing, and packed or row-strided
   2-D caller-buffer views. Float16 C2, C3, and C4 have 2-D and N-D
   Vec2/Vec3/Vec4 Get/Set, copied and borrowed 2-D rows, continuous 2-D/N-D
   whole-buffer borrowing, and packed or strided 2-D/N-D caller-buffer views
   that preserve exact binary16 encodings per channel, so Float16 has complete
   C1/C2/C3/C4 coverage. UInt8, UInt16, Int16, Int32, Float32, and Float64 C3
   likewise have 2-D and N-D Vec3 Get/Set. No C1–C4 typed-layout gap remains;
   the deliberate typed-layout limitation is C5+.
   One vector remains one complete three-channel element; neither N-D access
   nor N-D buffer borrowing flattens channels into scalar indices. Rows
   remain 2-D concepts; packed and strided external views accept N-D shapes,
   with strides counted in complete vectors.
   Float64 C1 has 2-D and N-D Get/Set, classification, 2-D row access,
   continuous 2-D/N-D whole-buffer borrowing, and packed or row-strided 2-D
   caller-buffer views. Every packed caller-buffer view listed in this item
   also accepts an N-D `Shape`, and every strided view an N-D `Shape` with
   per-dimension `Strides` (see item 4). Other OpenCV
   depths are available to general Mat operations but do not yet have the same
   typed access families. Float16 now has an exact 16-bit public value
   representation, IEEE-754 classification helpers, numeric
   Float32 <-> Float16 conversion, scalar C1 2-D/N-D Get/Set, copied and
   borrowed row access, continuous buffer borrowing, packed or strided
   external caller-buffer Mat views, and C2/C3/C4 2-D and N-D vector Get/Set
   plus 2-D rows, continuous buffer borrowing, and packed or strided external
   caller-buffer Mat views. All eight supported depths have complete
   C1/C2/C3/C4 typed coverage; C5+ typed families remain unavailable. N-D row
   APIs remain unavailable.

4. **External caller-buffer views are callback-scoped.**
   Packed 2-D and packed N-D (`Shape`, 2 .. 32 dimensions on OpenCV 4.x;
   at most 10 on OpenCV 5.0) views are available
   for UInt8, Int8, UInt16, Int16, Int32, Float16, Float32, and Float64 C1,
   UInt8/Int8/UInt16/Int16/Int32/Float16/Float32/Float64 C2,
   UInt8/Int8/UInt16/Int16/Int32/Float16/Float32/Float64 C3, and
   UInt8/Int8/UInt16/Int16/Int32/Float16/Float32/Float64 C4. Packed views require exact logical
   capacity: `Data'Length` equals
   `Rows * Columns` or `product (Shape)`.
   Strided storage is exposed for the same layouts both as 2-D row strides
   and as N-D per-dimension strides (`Dimension_Stride_Array`). C2, C3, and C4
   strides count complete vectors, not scalar channels. N-D strides require a
   final stride of `1` and non-overlapping nesting. Strided backing storage
   must contain the complete outer extent (`Rows * Row_Stride` or
   `Shape (first) * Strides (first)` elements), including padding after the
   final logical row or outer block. Both read-only and writable scoped views
   exist; read-only is an Ada mode/capability restriction, not page protection.
   C5+ typed external layouts are not available.

5. **Whole-buffer borrowing requires continuous storage.**
   Genuine continuous N-D Mats and continuous N-D Slices are supported, in
   OpenCV element order with the final dimension varying fastest. A typed
   empty Mat invokes the callback with an empty array. Use row borrowing for
   non-contiguous 2-D Regions or row-strided Mats. A non-contiguous N-D Slice
   has no row-based alternative; use `Clone` to obtain continuous storage.

6. **Scalar-valued APIs represent at most four components.**
   Operations returning `Scalar` validate channel limits rather than silently
   discarding channels.

7. **Arithmetic overloads are intentionally conservative.**
   The public API does not mirror the full C++ Mat/Scalar, masked, mixed-depth,
   and expression-template overload matrix.

8. **`Invert` and ordinary `Solve` are LU-specific.**
   Least-squares, SVD back-substitution, null-space solving, pseudoinverse, and
   condition-number behavior are exposed as separate explicit APIs.

9. **No general public `cv::MatExpr` equivalent.**
   The Ada interface favors explicit operations and explicit ownership.

10. **No raw public pixel pointers or `System.Address` API.**
    Zero-copy use cases are expressed through callback-scoped typed views.

11. **No public raw OpenCV integer mode flags.**
    Wrapped modes use strong Ada types or deliberately narrower operations.

12. **Persistence hides `FileNode`.**
    Nested maps and sequences are supported, but public FileNode objects or iterators,
    file append mode, Base64, comments, gzip controls, FLOW
    formatting, and raw persistence APIs are not part of the current slice.

13. **The spectral API is deliberately focused.**
    Full-complex and packed CCS DFT/DCT workflows, including `DFT_ROWS` and
    `DCT_ROWS` forms, are supported. Packed-spectrum division, CCS-bin
    accessors, packed/full representation conversion, and in-place transforms
    are not yet exposed.

14. **The supported OpenCV range is not exhaustively tested release-by-release.**
    CI validates four representative OpenCV-version targets across 4.1-5.0, plus
    native Ubuntu 24.04 ARM64 against distribution OpenCV. Compatibility
    fixes are kept below the public Ada API, but an untested intermediate
    release may still expose an undiscovered upstream difference.

15. **The API is pre-1.0.**
    Names and overloads may still evolve as N-D matrices, broader typed access,
    additional strided layouts, persistence features, and future cross-module
    integration are designed.

---

## Project layout

```text
opencv_core_ada/
├── .github/
│   └── workflows/
│       └── opencv-compatibility.yml
├── .clinerules/
├── alire.toml
├── opencv_core.gpr
├── LICENSE
├── README.md
├── containers/
│   └── ... compatibility container definitions ...
├── cpp/
│   ├── opencv_core_shim.cpp
│   └── opencv_core_shim.h
├── scripts/
│   └── configure_opencv.sh
├── src/
│   ├── opencv.ads
│   ├── opencv-core.ads
│   ├── opencv-core.adb
│   ├── opencv-core-persistence.ads
│   ├── opencv-core-persistence.adb
│   ├── opencv-core-*_access.*
│   ├── opencv-core-*_row_access.*
│   ├── opencv-core-*_buffer_access.*
│   ├── opencv-core-*_mat_view.*
│   ├── opencv-core-*_vec3*
│   ├── opencv-core-vectors.ads
│   ├── opencv-core-fixed_matrices.ads
│   ├── opencv-core-float32_matx3x3*
│   └── internal/
└── tests/
    ├── alire.toml
    ├── tests.gpr
    └── src/
        ├── tests.adb
        ├── mat_tests.*
        ├── mat_*_tests.*
        ├── persistence_tests.*
        ├── cubic_tests.*
        ├── polynomial_tests.*
        ├── k_means_tests.*
        ├── k_nearest_neighbor_tests.*
        ├── random_tests.*
        └── linear_discriminant_analysis_tests.*
```

`config/opencv_core_install.gpr` is generated locally by
`scripts/configure_opencv.sh` and is not a hand-maintained public interface.

### Installed Core Mat consumer

After native prerequisites and the Alire toolchain are available, run directly:

```sh
sh scripts/validate_installed_mat_consumer.sh
alr -n exec -- python3 -m unittest discover -s tests -p test_external_shim_install.py -v
```

The first command recursively installs real Core projects with GPRinstall, checks
the authoritative exported bridge, then compiles/links/runs a fresh public Mat
consumer against prefix-only project lookup. It moves prefix A to a longer B,
verifies A is absent, and repeats with new consumer objects. On Windows it also
checks installed DLL/import-archive byte equality and PE imports, using the
external MSYS2 compiler/runtime and static Ada runtime isolation. It does not
manually copy shim artifacts. Evidence and build logs remain in the reported
temporary directory. Linux and macOS retain their existing shim build modes.

The Python tests are separate GPRinstall configuration/helper evidence, not
native Core algorithm coverage. They reproduce the language-less external
project failure, demonstrate that declaring only C++ loses the library, and
exercise library/required-artifact installation plus missing-archive rejection.
See [the corrective qualification record](windows-external-shim-install.md).

---

## Development approach

New vertically integrated features generally follow this sequence:

1. Inspect authoritative OpenCV declarations, implementation source, and tests
   for the target operation and supported-version differences.
2. Inspect existing repository conventions and nearby Ada abstractions.
3. Design the public thick Ada API and its deliberate restrictions.
4. Separate public semantic validation from raw C ABI/memory-safety validation.
5. Add only the C ABI surface actually required.
6. Implement the C++ shim with exception containment, compatibility handling,
   and failure-atomic output publication.
7. Add/update the thin Ada import.
8. Implement the thick Ada operation.
9. Add focused AUnit coverage, including non-contiguous Regions and ownership
   cases where relevant.
10. Build the public crate with warnings as errors.
11. Build and run the complete tests crate.
12. Let the compatibility workflow exercise all CI OpenCV targets.
13. Run targeted GNATprove when a SPARK proof boundary changes.
14. Inspect the final diff and keep the change vertically focused.

For typed zero-copy work, additional rules apply:

- prove the Ada element representation before overlaying native storage;
- keep raw addresses internal;
- use callback-scoped lifetimes;
- retain OpenCV storage with a controlled lease while borrowed;
- require explicit `aliased` formals where caller-owned Ada storage is passed
  directly to native code;
- validate row strides and byte-step arithmetic before constructing external
  native headers;
- prohibit shallow escape from temporary external-buffer Mats;
- never silently fall back to copying when an API is documented as zero-copy.

---

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

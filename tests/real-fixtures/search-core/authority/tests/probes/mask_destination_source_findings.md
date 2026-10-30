# Task 051: mask destinations — preliminary safety findings

The user authorized narrow shared-helper Float16 rejection on OpenCV 4.x after
the isolated native crash investigation below. This is a safety correction,
not a test skip or numeric compatibility conversion.

## Starting gate

- Fetched `origin/main`: `c3997aab521fa9de77dd15a79a2d48df5ccaa57f`.
- Original worktree clean, on `corrective/windows-external-shim-install`.
- Open PR #52 concerns Windows installation, not mask destinations. Its
  README/CHANGELOG changes overlap documentation files only.
- Isolated worktree: `/tmp/task051-core`.
- Branch: `feature/051-mask-destination`, based on the fetched main.
- Host OpenCV 4.10.0 baseline: 1875 registered/executed/passed, zero failed
  assertions and unexpected errors. Logs: `/tmp/task051-baseline-build.log`
  and `/tmp/task051-baseline.log`.
- Baseline logged an OpenCL compiler/cache diagnostic. Passing UMat tests do
  not establish successful GPU kernel execution.

## Reconfirmed exact source identities

Remote annotated-tag peeling and local source checkout HEADs agree:

| Tag | Peeled SHA |
| --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` |

## Float16 blocker

The initial isolated probe includes `cpp/opencv_core_shim.cpp` and calls the
actual unchanged `dense_compare` and `dense_in_range_scalar` helpers. Each
combination runs in its own process. Direct-native calls use identical inputs.
Nonempty sources contain 257 Float16 elements equal to 2; Compare uses Equal,
and In_Range uses inclusive bounds 1 and 3. Destination starts as UInt8 C1.
OpenCL is explicitly disabled; all processes report enabled=0.

| Exact version | Compare Mat and UMat | In_Range Mat and UMat |
| --- | --- | --- |
| 4.1.0 | helper and native SIGSEGV (exit 139) | helper and native SIGSEGV (exit 139) |
| 4.6.0 | helper and native throw `cv::Exception` | helper and native SIGSEGV (exit 139) |
| 4.10.0 | helper and native throw `cv::Exception` | helper and native SIGSEGV (exit 139) |
| 5.0.0 | helper and native succeed | helper and native succeed |

All successful 5.0 cases have UInt8 C1 output and all 257 bytes equal 255.
The host 4.10 probe independently reproduces In_Range SIGSEGV and Compare's
unsupported-depth exception. A caught native exception is reported as such by
the diagnostic probe; its process exits zero, not because the operation succeeds.

Source evidence in `modules/core/src/arithm.cpp`:

- 4.1 `getCmpFunc`: 1063-1074 has a null Float16 slot; Compare's fast path
  calls it without checking at 1237.
- 4.6 Compare explicitly rejects Float16 at 1221-1223; 4.10 at 1355-1357.
- 4.1/4.6 `getInRangeFunc`: 1589-1598 has a null Float16 slot. Output is
  created at 1762, function selected at 1764, and called unchecked afterward.
- 4.10 `getInRangeFunc`: 1723 onward also has a null Float16 slot. Output
  creation/selection are 1896-1898; unchecked invocation is 1960.
- 5.0 Compare's table includes `cmp16f` at 1450; In_Range's table includes
  `inRange16f` at 2156.

These are native null function-pointer calls, not exceptions that the shim can
catch. Both shared helpers now reject Float16 under `CV_VERSION_MAJOR < 5`
before native output creation or OpenCL admission. Functions, procedures,
Mat/UMat and raw ABI callers all use those helpers. The guard raises a native
unsupported-format exception translated through the existing error boundary.
No conversion/staging was introduced. OpenCL half availability cannot make an
unsafe CPU fallback portable. Native execution is otherwise unchanged.

Fetched exact tags 4.11.0, 4.12.0, 4.13.0 and 4.14.0 and inspected both tables
with `git show`: each still has a null Float16 entry. Peeled identities:
`31b0eeea0b44b370fd0712312df4214d4ae1b158`,
`49486f61fb25722cbcf586b7f4320921d46fb38e`,
`fe38fc608f6acb8b68953438a62305d8318f4fcd`,
`0654a42e19215ef25b1d367d822f3c630447e7c7`, respectively.

Logs:

- `/tmp/task051-f16-4.1.log`
- `/tmp/task051-f16-4.6-corrected.log`
- `/tmp/task051-f16-4.10-corrected.log`
- `/tmp/task051-f16-5.0.log`

The initial 4.6/4.10 container compilation used an incorrect hard-coded include
directory. The corrected runs use each image's pkg-config flags; only corrected
logs are evidence for those versions. Probe compilation passes C++17 with
Wall/Wextra/Wpedantic/Werror on the host and all four images.

## Exact native source audit

Declarations inspected in `modules/core/include/opencv2/core.hpp`: compare is
InputArray/InputArray/OutputArray/op; inRange is InputArray/lower/upper/output.
Only existing array Compare and Scalar-bounded In_Range are exposed here.
All paths in the tables below are relative to `modules/core/src`.

| Tag | arithm.cpp Compare table/OpenCL/export | In_Range table/OpenCL/export |
| --- | --- | --- |
| 4.1 | 1063 / 1091 / 1187 | 1589 / 1603 / 1721 |
| 4.6 | 1053 / 1081 / 1177 | 1589 / 1603 / 1721 |
| 4.10 | 1187 / 1215 / 1311 | 1723 / 1737 / 1855 |
| 5.0 | 1439 / 1483 / 1579 | 2145 / 2170 / 2288 |

Compare releases output on both-empty input before normal execution. Nonempty
CPU paths acquire Mat headers, create UInt8 output with source channel count,
then select comparison kernels using source depth. Public C1 restriction makes
the binding mask C1. SIMD/HAL dispatch in `arithm.simd.hpp` takes typed source
pointers and byte output, not an old-output-depth extended selector. All six
modes have strict/non-strict scalar/vector paths. `opencl/arithm.cl` OP_CMP
(4.x:343-350, 5.0:350-357) stores 255/0 and uses UInt8 output definitions.

In_Range rejects source emptiness before normal output creation. CPU paths
retain source Mat headers, create source-shape CV_8UC1, select by source depth,
convert/unroll Scalar bounds and iterate NAryMatIterator planes. The elementary
predicate is `lower <= source && source <= upper`; `inRangeReduce` ANDs channel
bytes into one mask element. Integer scalar conversion uses native rounding
and saturation/invalid-bound handling; witnesses 1.2/2.8 become 1/3. This is not
ceil(lower)/floor(upper). OpenCL admission is dimension/device dependent and
can fall back. General N-D CPU iteration is native, not binding host staging.

OpenCV 5 In_Range HAL calls at 2374-2383 occur **after** output creation. Their
`dst.depth()` therefore describes newly created UInt8 output, not old storage.
UInt8/Float32 scalar HALs may preempt generic CPU iteration. No binding semantic
normalization is added for platform HAL differences; different channel bounds
and width-257 expectations deliberately test the public native semantics.

OutputArray delegation/create/release and Mat/UMat allocation were inspected:

| Tag | matrix_wrap.cpp create / release | matrix.cpp create / release | umatrix.cpp create / release |
| --- | --- | --- | --- |
| 4.1 | 1189-1342 / 1657-1673 | 318-375 / mat.inl.hpp:848 | 403-461 / mat.inl.hpp:3774 |
| 4.6 / 4.10 | 1160-1339 / 1665-1681 | 659-718 / 547-565 | 653-717 / 378-385 |
| 5.0 | 1466-1663 / 2042-2058 | 1085-1144 / 1010-1021 | 601-671 / 384-391 |

Compatible nonempty shape/type returns without releasing storage, including
Regions. Mismatch releases only that header and preserves old shallow aliases.
Release retains type but differs in metadata: reused 2-D output on 4.x retains
rank 2 with zero extents; 5.0 clears rank/shape. A fresh Compare function result
starts as native default output, so its empty rank is 0, UInt8 C1. It must not
be compared blindly to reused old-output metadata.

## Old-Destination hazard conclusion

Neither operation has a Subtract/Multiply-style selector keyed by old output
depth. Compare OpenCL vector-width prediction can inspect old destination
layout, but emitted type remains UInt8 and creation precedes output access.
Scalar In_Range uses channel count rather than array-bound vector prediction.
Whole/Region/type/shape/channel mismatch probes show no old-output write-width
hazard. No preallocation is justified. Helper changes are the authorized
Float16 gate and narrow exact UMat object-alias safety preflights; ordinary
native calls remain unchanged.

## Source/Destination alias audit

CPU Compare acquires both Mat headers before create. OpenCL Compare acquires
Left UMat before create but acquires Right UMat afterward (4.1:1129/1131/1172;
4.6:1119/1121/1162; 4.10:1253/1255/1296; 5.0:1521/1523/1564).
Mat exact Left/Right and distinct same-layout shallow source aliases pass the
UInt8/Int16/Float32 actual-helper/direct probes. UMat UInt8 C1 exact aliases and
distinct same-layout shallow aliases pass exercised paths. Historical native
type-changing exact UMat aliases are unsafe: CPU into Left produces `u->refcount == 0`
deallocation assertion on all four versions; host OpenCL-requested into Right
can produce wrong bytes. Before correction, actual-helper and direct-native
findings agreed. The helper now rejects an exact aliased UMat operand whose
depth is not UInt8, before native output creation. UInt8 exact aliases remain
supported, including raw multichannel UInt8 Compare (no C1 guard is added).
Mat exact aliases and distinct UMat shallow headers are not rejected. No hidden
copies or binding overlap machinery is added.

OpenCL In_Range creates `_dst` before acquiring source UMat state (4.1/4.6:
1655-1656; 4.10:1789-1790; 5.0:2222-2223). CPU Mat/UMat alias probes pass, but
host OpenCL-requested exact aliases differ, and UInt8 C1 shallow aliases can
also differ. Exact UMat Self/Destination alias is now rejected for ABI safety,
independent of OpenCL state, before native execution. Other shared-storage
In_Range aliases remain outside the supported contract. Mat In_Range behavior
and contract are unchanged; no Mat alias rejection/promotion is introduced.
Arbitrary partial overlap is unsupported
for both operations. OpenCL requested/enabled is recorded, **not** a claim that
any specific GPU kernel executed. Container devices do not establish GPU
coverage. Disabled coverage is exception-safe and restores the prior state.

## Floating mask observations

Finite/equal/adjacent and exact typed Int32 extrema expectations are independent.
Nonfinite Compare uses same-build function/native parity with exact byte checks.
Host CPU Float32/Float64 NaN Not_Equal can produce 0 in SIMD lanes but 255 at the
scalar tail (width 257); ordered/equal modes produce 0. No non-native NaN policy
is imposed. Infinity and signed-zero cases are also recorded by the probe.

## Public dimensional and capability policy

Both Compare validators query Rows/Columns, which raise OpenCV_Error on genuine
N-D inputs. In_Range validates only the up-to-four-channel Scalar restriction.
Public tests pin genuine N-D Compare rejection before Destination mutation and
N-D In_Range success for UInt8/Float32 C1/C2/C3, plus Float16 on 5.0. Results are
checked by Dimension_Count/Shape, not Rows/Columns. C1 volume values 0..4 test
both inclusive limits and failures; multichannel volumes test conjunction.

Temporary external/selected Mat inputs remain legal. Temporary Destination is
rejected independently in Ada and C++, for compatible and mismatched layout.
The C++ comment identifies header rebinding as severing callback-scoped backing
storage capability. Raw nulls and invalid enum reject pre-native with unchanged
metadata/pixels/Region Parent/external padding. Float16 rejection preserves
ordinary/Region output and aliases. No arbitrary post-native atomicity claim.

Validation-boundary review: no C1/shape/depth matching/channel-count/N-D/bound
semantic policy is duplicated in the shim. Retained semantic-looking conditions
are (1) Float16 under OpenCV 4.x, to prevent null native dispatch, and
(2) temporary Mat Destination, to prevent capability-severing header rebinding,
(3) exact non-UInt8 UMat Compare operand/Destination identity, to prevent mapped
ownership invalidation or late OpenCL source mutation during output creation,
and (4) exact UMat In_Range identity, whose CPU/OpenCL source acquisition order
is not portable. All have concrete ABI-safety comments. Nulls and enum decoding
are ABI checks. The alias preflights compare only actual cv::UMat object
addresses; they do not inspect UMatData, refcounts, storage overlap or OpenCL
state. Shared helper invocation protects procedures, raw exports and direct
private-helper callers without duplicate export/Ada policy.

## PR #53 exact-alias corrective

Corrective starts from `7bdea9f3747d9282f068fbc666cb4960772f607a` on the same
feature branch, with a clean worktree. Fetched main is now
`7897ecb869580c0a6396792dee88d817f87aebf6` after PR #52; PR #53 is mergeable.
No merge/rebase of main is needed or performed. A new normal commit preserves
the existing Float16 correction exactly.

Public tests reject Compare exact Left/Right for Int16/Float32/Float64/Float16
and In_Range exact Self for UInt8 C1/C3, Int16/Float32/Float16. Every source and
retained alias is checked for rank, shape, depth, channels and all pixel values.
Ordinary and exception-safe OpenCL-disabled coverage both reject. Raw exports
return translated OpenCV errors and preserve source/aliases. Positive existing
Mat exact/shallow and UMat UInt8 exact/distinct shallow Compare cases remain.
Raw UInt8 C3 exact Compare positive tests demonstrate that the new guard is
depth/object-identity based, not duplicate public C1 validation.

The `exact-guards` probe checks every source byte (including Float16 encodings)
and retained aliases under requested/disabled OpenCL. Actual-helper alias probes
assert guarded rejection/preservation; `native-aliases` remains a separate
research-only direct-native observation of the original unsafe behavior.
No GPU success is inferred from a request/enabled flag.

## Verification status

The original feature head passed 1899/1899; the corrective adds two focused
registrations. Exact corrective-head totals are recorded in PR review evidence.
Final exact-head matrix, shared link/format gates and PR handoff are recorded in
the final review report; development logs are not evidence for a different SHA.
No SPARK-compatible computation was changed, so GNATprove is not applicable.
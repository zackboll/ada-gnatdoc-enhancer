# CORE-FIN-01 focused native evidence

> R1 correction: the historical checkpoint blockers below are superseded where
> explicitly resolved in [the corrective qualification log](../../docs/core-fin-01-r1-qualification.md).
> All integer result depths now reject zero denominators before mutation,
> including raw-ABI conversion-safety protection. The real Ubuntu ARM64
> mismatch was reproduced and independently identified as a Convert_To oracle
> rounding error. Corrected validation has exactly main's eight baseline
> failures, with no additional unexpected errors. Remaining qualification must
> still be checked on the final source head; this is not a readiness claim.

Official sources inspected at exact commits (no audit snapshot imported):

| Tag | Commit | Scalar implementation |
| --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | [arithm.cpp](https://github.com/opencv/opencv/blob/371bba8f54560b374fbcd47e7e02f015ac4969ad/modules/core/src/arithm.cpp#L602) |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | [arithm.cpp](https://github.com/opencv/opencv/blob/b0dc474160e389b9c9045da5db49d03ae17c6a6b/modules/core/src/arithm.cpp#L588) |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | [arithm.cpp](https://github.com/opencv/opencv/blob/71d3237a093b60a27601c20e9ee6c3e52154e8b1/modules/core/src/arithm.cpp#L593) |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | [arithm.cpp](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/core/src/arithm.cpp#L623) |

Declarations are the add/subtract/multiply/divide/compare InputArray families
in each tag's `modules/core/include/opencv2/core.hpp`. Source detects Scalar
inputs, swaps reversed subtraction/division, unrolls the channel coefficients,
and selects native working-depth conversion. It is not equivalent to converting
the Scalar to the integer element type before calculation. Output depth is
passed explicitly to avoid the existing OLD-destination-depth subtraction
dispatch hazard documented by the matrix/matrix destination feature.

Native `scalar_modes_probe.cpp` passed on locally installed 4.1.0, 4.6.0,
4.10.0 and 5.0.0: seven depths, C1..C4, six directions, 257-element SIMD-tail
cases, non-contiguous input/output Regions, compatible storage reuse, exact
and same-layout shallow aliases, mismatched Float32-to-byte output detachment,
and six fractional/out-of-range scalar comparisons. The alias data pointer is
checked, not merely function/procedure value equality. Parent guards and old
allocation retention are checked. This does not establish arbitrary partial
overlap safety; public Ada conservatively rejects possible byte-span overlap
unless layout is identical. Compare permits that case only for UInt8 C1.

The overlap query reports storage observations, not public policy; Ada applies
the policy. Byte spans can conservatively include row padding/other regions of
the same allocation, so some disjoint-looking Regions may be rejected.

## Numerical boundaries and unresolved qualification

- `actualScalarDepth` invokes `cvRound(double)` before determining work depth.
  Add/subtract/reverse-subtract active coefficients are finite and bounded by
  absolute INT32_MAX. Integer multiply/divide coefficients use that bound too.
  Floating multiply/divide allow NaN/Inf; add/subtract accept nonfinite *source
  pixels*, but not nonfinite coefficients. Inactive components are not repeated.
- Scalar Compare takes double without premature narrowing. Native implementation
  checks finite out-of-integer-range values and handles fractions through relation
  adjustment; Ada rejects nonfinite comparison coefficients. Native source
  pixel special values remain version/backend dependent.
- UInt8/UInt16 saturation and well-defined Int32 boundary cases are tested.
  Int32 overflow has no portable mathematical guarantee. Tests must not
  deliberately trigger undefined signed-overflow native paths.
- **Important research finding:** array/scalar integer division by zero does
  not follow the generic array/array “zero produces zero” description on the
  observed x86_64 builds. An exploratory standalone probe produced unsigned 0
  but signed minimum values on all four versions. This is *not* promoted to a
  portable signed result guarantee or included as a sanitizer success case.
  The feature still needs a final reviewed safe zero/conversion policy before
  it can be considered fully qualified.
- `scalar_modes_shim_probe.cpp` passed ASan/UBSan against locally instrumented
  native libraries for all four versions, covering null/selector/output reset,
  owned result publication, default destination, temporary destination,
  Float16 dispatch rejection and contained native C5 exception. This focused
  probe is not proof that all arithmetic overflow/zero/nonfinite cases are safe.

Raw pointers must be null or live shim-owned handles; arbitrary forged/dangling
addresses cannot be validated by this opaque ABI. No new handle registry is
introduced and no existing C signature/layout is changed.

The AUnit suite is currently 2,037 tests (2,025 baseline plus 12 scalar tests).
Final hosted/version/sanitizer/installed/documentation and Scarthgap results
must be reported separately for the final source HEAD; no ready claim is made
by this research note.

## Checkpoint disposition: IMPLEMENTATION_BLOCKED

The normal-profile 2,037-test suite passed locally against 4.1.0, 4.6.0,
4.10.0 and 5.0.0 before the final raw-half negative assertion was added. That
assertion passed on the final normal 4.10.0 run. Final-head hosted compatibility
qualification is still required; earlier results are not a final-head claim.
Native-only alias probes passed all four; actual-shim ASan/UBSan probes passed
all four locally instrumented native libraries. The public example compiled
and ran. GNATdoc generation passed unchanged warning-baseline checks and
validated 195 packages / 202 HTML pages.

An additional validation-profile run executed 2,037 tests: 2,028 successful,
zero failed assertions, **nine unexpected Constraint_Error exceptions** in
nonfinite typed-access paths (eight existing suites plus the new IEEE test).
No typed-access implementation or validation/test policy was weakened to hide
this. The release profile was restored afterwards. Baseline isolation and a
focused resolution are still required before qualification.

Remaining feature work: resolve safe scalar integer zero/nonfinite/conversion
policy across architectures without silently replacing OpenCV numerics;
complete negative/numerical/alias coverage (especially comparison reusable ROIs,
all invalid operation forms, rounding tails and float32 special-value parity),
complete final guard review and full compatibility/installed/mixed/native
qualification on final HEAD. The optional preserved GNAT Pro 25.2 / Scarthgap
4.9 workspace and network-none container were found intact, **but this changed
production checkpoint has NOT TESTED Scarthgap/QEMU qualification**. No SDK or
compiler installation was modified or private artifact uploaded.

Validation-boundary review at this checkpoint retains: Float16 dispatch guard
(legacy null kernel), row count multiplication bound (signed overflow), scalar
finite/range guards (legacy cvRound/integer conversion), and temporary-output
guard (callback capability destroyed by header rebind). Those ABI-safety reasons
are commented in C++. Public shape/channel/alias policy stays in Ada. No final
feature-readiness claim is made while the numerical policy remains unresolved.
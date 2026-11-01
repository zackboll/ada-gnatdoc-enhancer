# Native runtime identity

## Public API

The development API in `OpenCV.Core` provides:

```ada
function Native_Version_String return String;
function Native_Build_Information return String;
```

Each call obtains text from the **actually linked native OpenCV library** by
calling `cv::getVersionString()` or `cv::getBuildInformation()`. Neither the
Ada crate's unchanged `0.5.2` manifest version nor the consumer's compile-time
OpenCV headers supply the result. The binding does not cache either result.
With dynamic linking, this describes the library resolved by the runtime loader;
with static linking, it describes the native implementation linked into the
program. It is not a claim about every other OpenCV module loaded by a process.

```ada
with Ada.Text_IO;
with OpenCV.Core;

procedure Runtime_Report is
   Version : constant String := OpenCV.Core.Native_Version_String;
   Build   : constant String := OpenCV.Core.Native_Build_Information;
begin
   Ada.Text_IO.Put_Line ("Native OpenCV: " & Version);
   Ada.Text_IO.Put_Line (Build);
end Runtime_Report;
```

Both results are ordinary, independently owned Ada Strings, without the ABI's
terminating NUL. They remain usable after repeated or interleaved queries,
unrelated OpenCV calls, and finalization of unrelated native objects. No native
pointer, reference, or string object escapes. The implementation allocates Ada
storage directly for the copy; there is no new native ownership framework.

Build information is multiline, build-specific, architecture-dependent text.
All payload bytes (including non-ASCII bytes and newlines) are preserved without
encoding conversion or parsing. Do not depend on a fixed layout, list of fields,
trailing newline, or equality across separately configured native builds. The
native version may contain development/vendor suffixes.

## Provenance and four-version source review

Independently inspected pinned upstream files (not just the historical runtime
observations in `core-portable-evidence.json`):

| Native version | Commit | Header declaration lines | Implementation lines |
| --- | --- | --- | --- |
| 4.1.0 | `371bba8f54560b374fbcd47e7e02f015ac4969ad` | 262, 270 | 806–814 |
| 4.6.0 | `b0dc474160e389b9c9045da5db49d03ae17c6a6b` | 242, 250 | 998–1006 |
| 4.10.0 | `71d3237a093b60a27601c20e9ee6c3e52154e8b1` | 242, 250 | 1031–1039 |
| 5.0.0 | `40738fb16ceddb5fb3fea747585f7ce6abb0605b` | 298, 306 | 1099–1107 |

Header: `modules/core/include/opencv2/core/utility.hpp`.
Implementation: `modules/core/src/system.cpp`.
Pinned source links:

- [4.1 header](https://github.com/opencv/opencv/blob/371bba8f54560b374fbcd47e7e02f015ac4969ad/modules/core/include/opencv2/core/utility.hpp#L253), [implementation](https://github.com/opencv/opencv/blob/371bba8f54560b374fbcd47e7e02f015ac4969ad/modules/core/src/system.cpp#L806).
- [4.6 header](https://github.com/opencv/opencv/blob/b0dc474160e389b9c9045da5db49d03ae17c6a6b/modules/core/include/opencv2/core/utility.hpp#L233), [implementation](https://github.com/opencv/opencv/blob/b0dc474160e389b9c9045da5db49d03ae17c6a6b/modules/core/src/system.cpp#L998).
- [4.10 header](https://github.com/opencv/opencv/blob/71d3237a093b60a27601c20e9ee6c3e52154e8b1/modules/core/include/opencv2/core/utility.hpp#L233), [implementation](https://github.com/opencv/opencv/blob/71d3237a093b60a27601c20e9ee6c3e52154e8b1/modules/core/src/system.cpp#L1031).
- [5.0 header](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/core/include/opencv2/core/utility.hpp#L289), [implementation](https://github.com/opencv/opencv/blob/40738fb16ceddb5fb3fea747585f7ce6abb0605b/modules/core/src/system.cpp#L1099).

All four declare `String getVersionString()` by value and
`const String& getBuildInformation()` by reference, neither `noexcept`.
All four implement the version function as `return String(CV_VERSION);` **inside
the native library**, and return a function-local `static String build_info`
initialized from generated `version_string.inc`. The latter reference remains
native-owned for the static object's lifetime; the binding only reads it during
the call and copies its bytes. Version construction and first build-string
initialization may allocate and throw (for example `std::bad_alloc`); no empty
success fallback is supplied. There is no relevant semantic difference among
these four implementations; generated configuration contents naturally differ.

## Native caller-buffer contract and errors

The internal C ABI exports `opencv_core_native_version_string` and
`opencv_core_native_build_information`. Each accepts a caller-owned `char *`,
`uint64_t capacity`, and distinct mandatory `uint64_t *required`, `*written`.
The public Ada API does not expose this protocol.

- Counts exclude the terminating NUL. Both valid count outputs are cleared
  before validation; aliased count outputs are rejected.
- A null buffer with zero capacity queries the payload size and writes zero
  to `written`. Null/nonzero and nonnull/zero combinations are invalid.
- Copy requires at least `required + 1` bytes. Success copies the exact payload
  then one NUL and reports the payload length in both outputs. Extra capacity
  is untouched. An empty native payload still requires one byte for copy.
- Insufficient capacity reports the required payload size, returns
  `ERROR_INVALID_ARGUMENT`, writes zero to `written`, and leaves the buffer
  untouched. No prefix is returned as successful text.
- Capacity must fit both `size_t` and `PTRDIFF_MAX`; payload length must be
  strictly smaller than their minimum (and fit `uint64_t`), reserving NUL
  without unchecked addition. These are ABI/memory-safety checks, not duplicated
  public semantic policy. Callers must supply valid nonoverlapping objects
  covering the declared capacities; C cannot discover arbitrary pointer extent.
- Native exceptions are contained using the existing OpenCV/standard/unknown
  status categories and thread-local diagnostic mechanism. Allocation failure
  is a failure, not successful empty text. Data is never returned in that
  diagnostic buffer.

The thick Ada implementation checks query counts before conversion/allocation,
rejects payloads larger than `Natural'Last - 1`, and validates the copy's
required/written counts and final NUL before returning a payload String.
Failures raise the established `OpenCV_Error`. Ada allocation failure may raise
`Storage_Error`; it is not suppressed. Changed native text between query and
copy fails safely rather than publishing a partially initialized String.

## Qualification and platform boundaries

`Runtime_Identity_Tests` runs in the registered Core AUnit suite and compares
both complete Ada Strings with an independent direct-native query in the
existing test-only module probe. No `CV_VERSION` oracle is used. The installed
Mat consumer exercises both functions through installed GPR projects before and
after prefix relocation, outside the original source tree.

`sh scripts/run_runtime_identity_probes.sh` exercises the actual production shim
with native parity, raw ABI failures, exact/short capacities, count initialization,
bounded overflow controls, all exception categories (including allocation
failure), and synthetic multiline/non-ASCII/embedded-NUL payloads. The same
controls run under ASan/UBSan, with Linux leak detection. Test-only providers
exercise the exact private helper without adding exported fault-injection hooks.
The existing four-version and ARM64 CI jobs run the public parity tests and
actual-shim probes. GNAT 12 and installed-consumer jobs retain their controls.
On GNU-linker configurations, `tests/probes/runtime_identity_controls.gpr`
additionally injects oversized query counts, nonzero query-written counts,
native failures, changed copy lengths, short-written counts, and missing NULs.
Both public functions must raise `OpenCV_Error` and never publish a partial
String; real calls must succeed after those failures. These controls retain
Ada validity checking and do not modify the production ABI.

Apple's sanitizer runtime does not support LeakSanitizer; ASan/UBSan remain
enabled with the existing qualified TBB allocator lifetime dependency. Windows
and MacPorts policy skips are not qualification passes. Cross-configuration is
not physical-target execution, and no Scarthgap or physical AArch64 target
qualification is claimed. Exact run results belong in the FIN-03 qualification
record and PR checks, not inferred from the source-version compatibility table.

## Status reconciliation

This is a development-branch addition, not a release. The crate remains `0.5.2`.
`docs/core-current-status.json` intentionally retains FIN-03 as
`PLANNED_REQUIRED` until merge. A separate post-merge reconciliation must cite
the merge and exact source-head qualification before changing main's status or
roadmap summary. Historical audits, roadmap evidence, and forensic findings are
not rewritten by this feature.
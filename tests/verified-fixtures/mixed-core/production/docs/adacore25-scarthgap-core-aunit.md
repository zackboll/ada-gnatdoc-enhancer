# CORE-POST-003: GNAT Pro 25.2 / Scarthgap Core AUnit qualification

## Scope and source identities

Executed 2026-10-17 in the preserved, rootless Podman qualification container
(UID/GID 1000, network `none`). No prerequisites were downloaded or rebuilt.
This is **AArch64 Linux QEMU qualification, not hardware qualification**.

Remote identities were refreshed before execution:

| Input | Exact identity |
|---|---|
| Qualified Core production and test sources / main | `a9029026315411f8c228254438ffc8cfad4c876d` |
| Immutable Core 0.5.0, peeled commit | `f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f` |
| Annotated Core 0.5.0 tag object | `8f962690b3b25eafcb6c7e7363a6d097a3c22366` |
| Geometry main, merged PR #46 | `00752b8a90f1dcc4d025fb136f0b6d8a8b1560ff` |
| OpenCV 4.9.0 source | `dad8af6b17f8e60d7b95a1203a1b4d22f56574cf` |
| Poky 5.0 / Scarthgap metadata | `fb91a49387cfb0c8d48303bb3354325ba2a05587` |

There were no intervening Core main changes requiring a new production-source
decision. The review branch changes test tooling, CI controls and this report;
production `src/`, `cpp/`, public API, C ABI and production projects are unchanged.
The campaign records the exact tooling commit separately from the production
commit. Neither immutable release sources nor tags were modified.

## Compiler, runtime and SDK

* AdaCore GNAT Pro **25.2**, GNATLS `20250603-133`; Ada and C++ GCC
  **13.3.1 20240927 (for GNAT Pro 25.2 20250603)**.
* Target `aarch64-linux-gnu`, using the supplied absolute Ada/C++ drivers,
  GPRbuild, binder, archiver and matching `rts-native` runtime.
* Actual fresh compiler-generated ALI record: **`V "GNAT Lib v25"`**.
  This is not inferred from GCC major 13. Every campaign ALI is compared with
  the fresh compilation and all 885 supplied runtime ALIs agree.
* Established Core preflight resolves the real sibling GNATLS search paths
  when GCC returns the unresolved literal `adalib`. The target CGPR specifies
  the supplied drivers and actual runtime; additional controls use a separately
  generated CGPR adding the supplied C driver.
* Preserved official Poky minimal qemuarm64 extensible SDK 5.0, metadata
  timestamp `20240418161421`, prepared offline; development sysroot
  `sdk/scarthgap-official/tmp/sysroots/qemuarm64` relative to the private
  workspace. This is the already qualified eSDK-derived environment, **not** a
  claim that the separate custom `populate_sdk` source-build path completed.
* Target glibc 2.39, `libstdc++.so.6.0.32`, loader
  `/lib/ld-linux-aarch64.so.1`; existing OpenCV 4.9.0 target headers/libraries.
* AUnit 26.0.0 from the preserved `aunit-v26.0.0.zip`; archive SHA-512:
  `b882e96a4b2cbc2d0d3838e14f2c7b6e576d6d7ccf88fe3562b1fbca61a2ebfd4e8b3379dd5c3fb3140949cda69526c8696fe3b7a6c6748fe93f116213276b39`.
  Its upstream `version_information` file says `0.0`; that file alone is not
  the release identity. The verified distribution/archive provenance is used.

Measured SHA-256 identities (hashes, not proprietary binaries):

| Artifact | SHA-256 |
|---|---|
| Supplied Ada driver | `dd71f5d100fdc091ae3975d41525436b74d2e125adca4cffd0014e579fb17e2a` |
| Supplied C++ driver | `eafef42da4df0326dd4ba58f662e5c664624a6b099bcc1370ecee2234e425ea0` |
| GPRbuild | `ba9a43b06b7bc304573fcad7acdad3b96739fee036dc4c14d57a7b4c8d8010a4` |
| Runtime `libgnat.a` | `768f0261d9b6e85196ae08a07aab78b013477469e97b99c0c4fcb100d1f41a2a` |
| Target `libopencv_core.so.4.9.0` | `7601b57881fb39e36bde08f09d439a888d6b11e94cb726a9cd5c30158d58aee0` |

## Actual Core test configuration

The existing `tests/tests.gpr`, `Mat_Tests.Suite` and registration are retained.
This is not a copy of Geometry's 542-test runner. In static-PIC mode GPRbuild
compiles the native C++ test sources, including module bridge, UMat header and
OpenCL probes. The pre-build helper separately builds the borrow-lifetime/UMat
archive. All use the supplied target C++ compiler and sysroot, C++17,
`-Wall -Wextra -Wpedantic -Werror`; the production shim remains unchanged.

The small helper correction forwards its existing `Cxx_Sysroot` setting to
both external static-PIC compilations and obtains the archiver from that
compiler. Native GNU configurations have an empty setting and retain the
existing compiler arguments and `ar` path. Focused invocation controls cover
both compilations, quoted sysroot arguments, native behavior and unavailable
target archivers.

Profiles are deliberately explicit:

| Component | Configuration |
|---|---|
| Preserved qualified Core production | `release`; `-gnatwa -gnatwe`, project `-Werror`, local typed-access Ada 2022 selection; no added optimization/validity override |
| Authoritative AUnit harness | `adacore25-release`; `-O0 -gnatwa -gnatwe`, project `-Werror`, normal runtime checks |
| AUnit framework | Upstream default `Install`: `-O2 -gnatp -gnatn -gnatwa.X`; unchanged dependency policy |
| Additional layout controls O0 | Existing `-O0` policy |
| Additional layout controls O2 | Existing `-O2 -gnatp` policy, restricted to those controls |

No `-gnatVa` is added: Core's existing GNAT 12 report documents its conflict
with intentional IEEE NaN/infinity tests. No test registration, runtime checks,
assertion switches, numerical tolerances or exception handling were weakened.
The dependency's upstream switches are not silently applied to the checked
test harness. The first exploratory O3 harness also passed, but is not the
authoritative O0 qualification.

`OPENCV_CORE_CI=1` enables the existing concise reporter. Its first counting
filter executes no tests; the running filter then activates **every** test.
The qualification requires every numbered `RUN 1/2025` through `RUN 2025/2025`
exactly in order, the complete success summary and executable exit status 0.
Persistence tests use the container's normal temporary-directory environment.
No selection/filter or host-wide binfmt registration is used.

## Execution results

**Core production:** previously qualified full build/install reused and
reverified, including 424 ALIs / 216 objects-or-archives in its build tree and
211 ALIs / two archives in the relocated installed prefix. The previously
qualified Ada.Text_IO probe executed successfully again under QEMU.

**Core AUnit:** full checked target cross-build without warnings, then explicit
`qemu-aarch64 -L SYSROOT EXECUTABLE`, QEMU
`6.2.0 (Debian 1:6.2+dfsg-2ubuntu6.31)`:

```text
Registered tests: 2025
Total Tests Run:   2025
Successful Tests:  2025
Failed Assertions: 0
Unexpected Errors: 0
QEMU exit status: 0
```

**Additional controls are independent gates**, not assumed from that pass:

| Control | Result |
|---|---|
| K-means attempt/default forwarding, four intercepted calls | PASS |
| All-family constructor/lease instrumentation, complete 2,025-test suite | PASS; no live views/leases, balanced destruction |
| O0 layout guard and wrong-object-size controls | PASS |
| O2 layout guard and wrong-object-size controls | PASS |
| Float16 boundary controls, O0 and O2 | PASS |
| Production negative controls, O0 and O2 | PASS |
| Public scalar/Vec representation measurements, O0 and O2 | PASS |
| C ABI record representation assertions / real source-unit compiler controls | PASS; unchanged compile-time assertions, five source-unit controls |
| Actual hardware | NOT RUN / NOT TESTED |

The preserved native Debian 12 runner also passes completely: GNAT/GCC 12.2.0,
OpenCV 4.6.0, 2,025/2,025, all additional programs, installation and relocated
consumers. Its GNAT 12 configurations and policy remain byte-for-byte unchanged.
Synthetic checks are separately labeled: 45 existing cross-preflight controls,
three helper invocation controls and seven evidence-verifier controls.

## ELF, runtime and dependency qualification

Every built runtime executable (AUnit plus 12 additional-control binaries) is
ELF64, little-endian AArch64 with the target interpreter. Every inventoried
object/archive is checked for target architecture and actual compiler `.comment`
identity; every ALI agrees with fresh compiler-generated GNAT Lib v25.

The checked AUnit campaign inventory has **364 objects, five archives, 591
ALIs**, including copied production artifacts and installed ALI duplicates.
These are inventory counts, not counts of unique compilation units. Its verbose
trace contains 150 supplied compiler/linker invocations; the binder explicitly
selects the supplied GNAT toolchain and runtime archives. Additional-control
inventories are cumulative per build directory and recorded separately.

The AUnit dependency closure contains nine target ELFs with 65 satisfied
symbol-version requirements. K-means and each layout executable check 58;
all-family checks 65. Resolution uses only contained sysroot libraries.
GNAT runtime archives are linked statically as shown by the actual link trace;
this is not a claim of dynamically loading a host GNAT runtime. No host x86_64
objects or host OpenCV, foreign ALIs, executable RPATH/RUNPATH, or unrelated
installed/source project imports were accepted. The existing SDK OpenCV
library's `/usr/lib` RPATH is explicitly qualified as **target-root** `/usr/lib`,
never host `/usr/lib`; other unqualified library paths are rejected.

## Reproduction and evidence

All new local evidence is under the private workspace's
`evidence/core-post003/`. Prior POST-001/POST-002 evidence is unchanged. Build
traces, complete QEMU logs, compiler/runtime hashes, object/archive/ALI
inventories, dependency closures, symbol versions and individual exit records
are retained. Tooling source revisions are recorded in each final campaign.
Do not publish the workspace wholesale: it contains licensed toolchains and SDK
inputs. This report and public scripts contain no licensed binaries or secrets.

Use a clean checkout of the tooling commit, the preserved clean production
workspace, pristine AUnit sources and the existing supplied cross profile:

```sh
# Inside the existing offline qualification container; all paths absolute.
# First source the reviewed explicit cross-toolchain/sysroot profile.
export QUALIFY_CORE_COMMIT=a9029026315411f8c228254438ffc8cfad4c876d
# Set QUALIFY_PRODUCTION_WORK, QUALIFY_AUNIT_ROOT and QUALIFY_EMULATOR.
# Set every OPENCV_CROSS_* / ENV_PREFIX input required by Core preflight.
sh "$CORE_ROOT/tests/adacore25/qualify_aunit.sh" "$NEW_AUNIT_EVIDENCE"
# For controls use the reviewed CGPR containing supplied Ada/C/C++ drivers.
bash "$CORE_ROOT/tests/adacore25/qualify_controls.sh" \
    "$NEW_AUNIT_EVIDENCE" "$NEW_CONTROLS_EVIDENCE"
```

The scripts never install prerequisites, change the sysroot, select an Alire
compiler, alter native GNAT 12 policy or register binfmt. GNATformat 25.2 was
attempted for the new GPR fragment but does not parse GPR syntax; no Ada source
was changed. GPRbuild validates the fragment. Shell syntax, ShellCheck and
focused Python regressions validate the tooling. SPARK algorithms were not
changed; no new proof or coverage claim is made.

Preserved unsuccessful setup/verification attempts are distinguishable from
runtime failures: an overbroad freshness guard rejected the existing qualified
production toolchain fixture; a first synthetic invocation inherited target
pkg-config variables; and the new verifier initially rejected the already
qualified OpenCV target `/usr/lib` RPATH. Each was diagnosed and corrected
without changing target libraries, tests or algorithms. **No Core AUnit runtime
failure was observed.**

## Disposition and release policy

| Acceptance state | Result |
|---|---|
| `ADACORE_GNAT_PRO_25_2_VERIFIED` | PASS |
| `SCARTHGAP_CORE_SYSROOT_VERIFIED` | PASS |
| `CORE_AARCH64_PRODUCTION_BUILD_PASS` | PASS, reused and reverified |
| `CORE_AARCH64_AUNIT_BUILD_PASS` | PASS |
| `CORE_AARCH64_AUNIT_2025_QEMU_PASS` | PASS |
| `CORE_AARCH64_ABI_CHECKS_PASS` | PASS |
| `CORE_AARCH64_ADDITIONAL_CONTROLS_PASS` | PASS |
| `CORE_AARCH64_HARDWARE_NOT_TESTED` | CONFIRMED |

Independent review is still required. This task creates no tag/release and
does not authorize merging. Core 0.5.1 cross-tooling stabilization and Geometry
0.3.1 GNAT Pro tooling are technically ready for separately scoped release
preparation **after review and final hosted CI**, not released by this task.
Existing Alire consumer dependencies and production API/ABI are unchanged.

No public semantic validation is duplicated in the C++ shim.
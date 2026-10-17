# Windows externally built Core shim installation correction

## Predecessor failure and scope

Features Task 008 is paused at Gate 0. Task 007 merge
`4a12eca349df6d53abd54b4711aabfcd884f8667`, Windows run `37257812725`, job
`111598536513`, passed the 67-case native suite (zero assertions/errors), DLL
inspection and source consumer on OpenCV 5.0/features. Recursive installation
against pinned Core `7956981a7881ce9121115f8cb65909aeb9edc439` failed:

```text
gprinstall -f -p -r --prefix=... -P .../opencv_core.gpr
Install project OpenCV_Core_Shim
gprinstall: cannot find toolchain for the project OpenCV_Core_Shim, no language found, aborting
```

Starting current Core main: `c01e3e90ea99e26e8bbf0d524acb5d5e1c4df6bf`.
Branch: `corrective/windows-external-shim-install`. Core remains `0.5.0-dev`;
no Features manifests/pins, release versions, public APIs or native ABI change.
This correction does not establish Features/Core minimum-version compatibility.

## Reproduction and root cause

GPRinstall 26.0.0/GPRbuild 26.0.1 reproduces the exact failure on Linux when
the real shim project is evaluated with `External_Relocatable`. Both the old
pin and current main declared no languages and no sources for this branch.
GPRinstall needs a language when generating the installed project.

The language-only experiment is also insufficient: GPRinstall succeeds but
generates an **abstract project** and installs no library. Declaring C++ plus
the actual `cpp/` sources makes it recognize a library and install the prebuilt
shared object. `Externally_Built = True` remains: GPRbuild must not compile it.
Linux reproduction uses a real locally linked shared Core shim, not a Windows
DLL; actual Windows artifact behavior requires the separate Windows CI run.

## Corrective contract

Only the Windows external branch changes its language/source metadata. Linux
Static_PIC and macOS Relocatable branches are unchanged. The external builder
still invokes the configured matching MSYS2 MinGW64 g++, never GNAT g++.

GPRinstall installs the shim DLL as a library, including runtime bin placement.
`Install.Required_Artifacts` explicitly installs the externally produced
`libopencv_core_shim.dll.a` into `lib/opencv_core_shim`, alongside the DLL. A
missing import archive is an error, not a successful incomplete installation.
No manual artifact copying or custom substitute installed project is used.

## Qualification evidence

The three helper regressions passed locally on Linux/OpenCV 4.10.0 with GNAT
16.1.0, GPRbuild 26.0.1/GPRinstall 26.0.0 and system g++ 14.2.0. They reproduce
the old diagnostic, reject the language-only conclusion, compare installed
library/artifact bytes, and require missing-archive failure. The Linux archive
fixture tests artifact copying only; it is not a Windows import-library proof.

Actual recursive Core installation and fresh prefix-A/prefix-B Mat/clone
consumers passed locally. Each compiles and links independently with warnings
as errors, uses installed projects/libraries, and prints
`opencv_core installed Mat consumer ok`. Prefix A is removed before the second
compile. Production/test builds, forced fresh development-profile direct AUnit
and `alr test` passed: **1858 registered / 1858 executed / 1858 passed**, zero
failed assertions/errors. Release-profile direct AUnit also passed 1858/1858.
The existing root-value source consumer/exported-header validator passed.
GNATformat check, shell syntax checks and diff whitespace checks passed.

The first run reusing pre-existing local build state had six validity-check
`Constraint_Error` errors in nonfinite floating tests (1852 passed, zero failed
assertions). An isolated unchanged-main campaign passed 1858/1858; forcing a
complete development rebuild of the corrective tree also passed 1858/1858.
This identifies reused build/profile state as the failure context, not evidence
of a GPR installation regression. No numerical tests, validity switches or
production code were altered. The host also emits OpenCL compiler-header
diagnostics and falls back internally; no working GPU execution is claimed.

Remote CI results are reported at the exact PR review head;
pending/unexecuted runs must not be described as passing.

Initial remote qualification exposed validator failures before completing the
installation campaign: macOS normalized a double slash in TMPDIR, breaking
literal trace comparison (fixed by physical evidence-path normalization with
explicit diagnostics). Windows PE output contained the required probe export
but `printf | grep -q` under `pipefail` reported it missing. Probe-dump checks
now consume all input, retaining every existing symbol/import requirement.
These are validator corrections, not native algorithm or ABI changes.

Windows run `37260190823` on `7c70c7e` passed 1858/1858 native cases and
recursive installation, including installed DLL/import-archive byte equality
and PE imports. Its fresh consumer build then rejected legacy `-vP2` in the
Windows GPRbuild. The validator uses portable `gprbuild -v` plus `gprls -v -U`
source/ALI resolution and the actual verbose library link instead. Installed/
relocated runtime success still requires the final corrected Windows campaign.

Existing Core Windows CI remains main/manual only. Its new consumer stage must
verify DLL/import-archive byte equality, DLL PE imports, prefix-only fresh links
and both runs. Existing native tests and external-object/compiler checks remain
mandatory. Features Task 007 still needs a separately authorized pin/follow-up
decision and a successful Windows installed/relocated proof after Core review.
Neither repository is merged or released by this corrective task.
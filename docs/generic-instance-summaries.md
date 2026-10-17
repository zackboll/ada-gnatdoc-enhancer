# Source-verified generic-instance summaries (GNATDOC-006)

This is **verified presentation, not compiler generic expansion**. The feature
is disabled by default. It does not give instances native member declarations,
does not authorize new dependency anchors, and does not migrate any consumer.

## Trust and supported grammar

An opt-in project configuration supplies a reviewed, SHA-256-bound qualification
record, relative to the project root:

```toml
[generic_instances]
qualification = "generic-qualification.json"
sha256 = "<SHA-256 of the reviewed qualification record>"
```

The record has exactly `schema_version = 1`, `instances`, `source_sha256`, and
`native_sha256`. Source hashes cover the complete configured public specification
set; native hashes cover the pristine API index, stylesheet and every package
page. Instance entries contain the qualified package, template, element name,
source-owned element owner and dimensions. This is an **input permission**, not
an output-side self-authorizing manifest. Changing a reviewed input requires
independent requalification and an explicitly updated trusted configuration.

Only complete compilation units of this form are accepted (Ada identifiers are
case-insensitive; comments and whitespace do not change semantic token identity):

```ada
with OpenCV.Core.Vectors;
package Qualified_Instance is new OpenCV.Core.Vectors
  (Element_Type => UInt8_Value, Length => 2);
```

The second supported template is `OpenCV.Core.Fixed_Matrices`, with exactly
`Element_Type`, `Row_Count`, and `Column_Count`. Named association order is
irrelevant; each formal must occur exactly once. Dimensions must be canonical
positive decimal literals (`[1-9][0-9]*`), not expressions, qualified constants,
signed numbers or positional arguments. The entire unit is consumed: additional
context clauses, use clauses, aliases, renamings, nested/generic contexts,
pragmas, trailing declarations and string syntax are rejected for these units.
Other families are reported as unsupported, not expanded.

Both complete template declarations must match their verified generic formals
and zero-based index/array definitions. Supported actual types are UInt8, Int8,
UInt16, Int16, Int32, Float16, Float32 and Float64 `_Value` declarations. The
first, second, third, fourth, fifth, seventh and eighth are owned by `OpenCV`;
**Float16_Value is owned by OpenCV.Core**, with a public private-type declaration
and private binary16 representation. Owner declarations, ancestor visibility,
potential public/private shadowing, and unsupported ancestor scopes are checked.
This deliberately does not implement arbitrary Ada overload or scope resolution.

## Native evidence and rendering

Every page filename comes from the observed native package heading/navigation.
Every member/type fragment comes from a genuine source-reconciled GNATdoc `h4`
declaration section. Vector links point to `Component_Index` and `Vector` on the
template page; Matrix links point to `Row_Index`, `Column_Index` and `Matrix` on
its template page. The matrix additionally verifies the separate conversion
package and both conversion function profiles. Missing evidence fails closed.

For the pinned GNATdoc 26.0.0 serialization, each empty instance page is
independently reconstructed from its source-owned plain-text introductory comment
and exact native layout. The section is inserted **before Description**, before
the native unclosed introductory paragraphs. Native introductions, descriptions,
anchors and declaration snippets are preserved. Unknown layouts are rejected.

The only injected ID is `instance-members-summary`, explicitly presentation-only.
It cannot satisfy `verified_types`, dependency manifests or native declarations.
The summary contains actual arguments, zero-based ranges and fixed-size array
meanings; ordinary Ada array assignment is distinguished from Mat ownership.
Float16 explains storage encodings versus numerical conversion; the matrix's
conversion package copies rather than sharing native storage.

Publication verification rechecks the qualification record, source/native hashes,
complete declarations, destinations and exact reconstructed summary bytes. Native
visible-text preservation removes **only that exact reconstructed section**, and
only when trusted source and pristine evidence are provided. It does not ignore
arbitrary section markup. Staging, file inventory, link, fragment, executable
content, symlink and publication-byte checks remain mandatory.

## Demonstrated qualification

Starting main: `478d0bbff0be1b9141b5ad39f07a71f0386d86e9`.
Core source pin: `c5545eee815431568495c6c76af83df56cf5c3dd`.

| Pinned site | Packages | Native sections | Local type links | Offline external links | Generic summaries |
|---|---:|---:|---:|---:|---:|
| Core | 195 | 1,268 | 2,459 | 0 | 25 |
| Imgproc | 1 | 314 | 326 | 549 | 0 |
| Geometry | 2 | 130 | 171 | 95 | 0 |
| MEL | 29 | 1,237 | 1,418 | 0 | 0 |

Core's 24 Vector and one Matrix summaries have **102 separately counted actual
hyperlinks**: 25 template-package, 51 template-member, 25 actual-type and one
conversion-package link. They add 25 presentation anchors and **zero native
instance-member declarations**. Two-copy determinism, byte-idempotence, native
visible-text preservation, source/native hash checks and publication reconstruction
are full-site checks, not inferred from reduced hosted fixtures.

The original pinned upstream instance enhancer was executed in isolation,
including its own `--check`. Its 25-instance coverage, actual arguments, ranges,
member meanings, conversion/Float16 ownership prose and all 102 hyperlink
destinations are compared independently. Differences are classified per instance:
explicit qualified instance identity and an added Ada-assignment/Mat-ownership
distinction are intentional improvements; theme differences are presentation.
The multiplication sign is an ASCII HTML character reference: Chromium caught
misdecoding of raw UTF-8 under charset-less HTTP, which this serialization fixes.
This does not claim execution of the entire consumer publication pipeline.

Six historical GNATDOC-002 inventory entries for UInt8/UInt16 vectors attributed
the source file/hash to sparse-access units. Actual package declarations and the
original acquisition hashes establish the correct ownership. New discrepancy
evidence records each correction; historical evidence is unchanged.

Consumer coverage remains Imgproc 1,512/1,512; Geometry 452/452; MEL 4,294/4,295.
MEL's Health Status metadata renderer omission remains uncredited. Its original
73 warnings remain private-part warnings, and the approved foundation integrity
policy remains unchanged. Historical Core 0.4.1/0.5.0 dependency inventories retain
their original source/native identities and never gain explanatory anchors.

## Reproduction and evidence

Full-site qualification requires the original GNATDOC-002 acquisition plus the
GNATDOC-005 dependency bundle; neither is silently replaced by synthetic data.
Run the driver with new absolute workspace/output paths:

```text
python /home/zboll/git/ada-gnatdoc-enhancer/scripts/qualify_generic_instances.py --help
python /home/zboll/git/ada-gnatdoc-enhancer/scripts/check_real_browser.py --help
```

Machine-readable results are under
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc006/`.
The authentic reduced fixture includes five representative instances, complete
original source/native package pages, hashes and provenance. Its index is an
explicitly reduced native compilation-unit/tagged-type list, **not** a claimed
original full-site index. Hosted CI runs these regressions on Python 3.11–3.13,
synthetic conformance and wheel/sdist tests, not four full native sites.

Chromium qualification records individual desktop/390px, light/dark,
JavaScript-enabled/disabled assertions, all representative summary destinations,
bookmarks, Back/Forward, keyboard focus and overflow. This is not full accessibility
certification or production external HTTPS qualification.

Production adoption, reviewed consumer configuration/policy authorization,
authored guides and version-stable external publication remain outside scope.
No consumer source, documentation script, warning/coverage gate, Pages deployment,
release or historical evidence is changed.
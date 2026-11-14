# GNATDOC-SEARCH-002 — public Ada search completeness

## Baseline and scope

Started from freshly fetched upstream `main`, commit
`0120bee2f2455e4c832d1d5ddae0a4cb03cb9477`, tree
`01900ddb099c801eeb92fba718f4c528f87d865f` (v0.1.5). Work is isolated
from the pre-existing GNATDOC-036 branch. No release/version bump, publication,
consumer installation, merge, or Imgproc/Geometry consumer edit is included.

MEL source commit `1d7cf8a11ee6fc154fee2b577aa7296b5a1fbd0a`, tree
`2866a78de690e24c38065f513c08dcf37b609793`. All 52 retained Ada specifications
were independently compared byte-for-byte to that Git revision. The complete
API is the retained pristine GNATdoc 26 acquisition, not a new compiler run.
Input provenance is pinned in
`/home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures/search-mel/provenance.json`.

## Root cause and independently established inventory

The old `flat_public()` rejected an entire public region containing any
`package`, `generic`, `task`, `protected`, `begin`, or `declare` token.
Each of the seven affected MEL packages contains **package instantiations or
renamings**, not ambiguous sibling declarations. Its unrelated direct public
types/subprograms already have independently observed native anchors.

| Package | Independently reconciled additions |
| --- | ---: |
| AMS.MEL.Status | 157 |
| AMS.MEL.IR.Channel | 68 |
| AMS.MEL.IR.C2 | 51 |
| AMS.MEL.IR.Health_Status.Metadata | 47 |
| AMS.MEL.IR.Calibration_Configuration | 19 |
| AMS.MEL.IR.NUC | 5 |
| AMS.MEL.IR.Discovery | 1 |
| **Total** | **348** |

The independent oracle scans the complete public specs and observed native
signatures, without calling the corrected source inventory or destination
collector. It asserts that these real inputs have the separately supported
flat-with-package-instances shape before inventorying them. Reported counts
and the supplied omission list are not oracle inputs. Afterwards, the 348
derived destination identities were compared to that evidence: exact set parity.

| Inventory | Before | After |
| --- | ---: | ---: |
| Packages | 42 | 42 |
| Types/subtypes | 315 | 421 |
| Functions/procedures | 786 | 1,028 |
| Total records | 1,143 | 1,491 |

All **1,143 existing records are byte-equivalent as JSON records**, including
their text, names, labels and destinations. No existing record was removed.
There are no additional eligible omissions from other search filters in this
acquisition. The complete oracle/index destination sets match exactly once.
46 native sections remain outside the direct public type/subprogram contract:
17 constants, 17 exceptions and 12 package instantiation/renaming declarations.
262 private-part source declarations/completions remain excluded (207 types,
54 procedures, one function). Private library packages, quoted operators,
constants, nested members and synthetic instantiated members remain outside
the search contract. Native existence alone never authorizes a record.

Complete individual names, signatures, owning packages, source locations,
native destinations, unchanged/removed lists and input/output hashes are in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/search002/inventory.json`;
private exclusions are in the adjacent `excluded-private-source.json`.
The corrected MEL index SHA-256 is
`3af66092beeecddac4a33983fc660d5619b04c139acee0c1d86d4c98acfc2106`.

## Correction and safety model

The existing masked Ada lexical infrastructure now walks declaration boundaries
with exact source offsets. It skips nested package/task/protected scopes,
generic formals/templates, instances and bodies without promoting their members.
Private boundaries are recognized as declaration boundaries, including same-line
private parts; partial private views and `with private` type extensions are not
mistaken for a private-part separator. Existing source-order signatures,
associated text, line identities and overload ordinals are preserved.

Search additionally requires exact immutable declaration identity (kind, name,
signature and source line), rather than a signature substring. Independent
native profile/anchor reconciliation remains mandatory. No browser runtime,
schema, limits, routing, digest, allowlist or same-origin restriction is relaxed.

The walker intentionally is not a complete Ada parser. Ambiguous/unbalanced
scopes fail closed for the unit instead of guessing an `end` boundary. Complex
executable blocks/declare expressions are not newly supported. Well-bounded
unsupported nested declarations do not exclude unrelated siblings. Native
profile projections remain exactly the separately qualified existing contract.

## Executed qualification and reproduction

```sh
cd /home/zboll/git/ada-gnatdoc-enhancer
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -O -m unittest discover -s tests -p 'test_search*.py' -v
PYTHONPATH=src .venv/bin/python scripts/qualify_search_scopes.py \
  --source-root /home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures/search-mel/authority \
  --native /home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures/search-mel/pristine \
  --before /home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures/search-mel/before.json \
  --output /tmp/search-002-independent --browser
```

Two independently generated complete MEL outputs match every file byte.
Chromium searched and clicked **all 348** previously absent records, checking
the actual iframe anchor's visibility after navigation. The adjacent
`browser.json` retains each observed canonical URL. No runtime errors or
external requests; JavaScript-disabled native navigation passed.
Existing queries passed with 20, 4, 4 and 1 displayed matches respectively:
`Navigation Report`, `Navigation_Report`, `Submit Navigation Report`,
`Submit_Navigation_Report`.

Nine adversarial scope tests cover before/after/multiple nested packages,
generic formals/templates, protected/task declarations, nested bodies,
visible/private and partial/completed views, overloads, comments, literals,
quoted operators, unsupported boundaries, and native evidence loss/swap.
Forged private/nested/formal/invented records are rejected even with a matching
index digest, shell count/allowlist insertion and output-manifest hashes.

Existing real-Core Chromium search tests passed for default, symbol and instance
routers (including overloads, bookmarks/history, malicious input, rehashed cache
mutations, themes/mobile, guides, same-origin and no-JavaScript navigation).
Its complete historical 1,462-record fixture is unchanged. A separate current
Core source/native acquisition at commit
`9398e7fc899c0bb82f9071f4747d85dd97fa97a3`, tree
`166e938a45ac9085cc9ed0f4aaf16e4b156f8b13`, authenticates every native input
against its authored manifest and produces 1,487 records reproducibly. No
analogous eligible exclusion was found. Compiler-verified example decoration
was disabled only for that extra acquisition because its retained generated
compiler configuration is stale; the separately pinned production-Core example
tests and eight-case Chromium suite passed with decoration enabled.

Four-profile conformance, synthetic Chromium navigation, optimized verified
example tests (34), and predecessor research tests passed (31: 23 tests/five
documented skips; 32: 18 tests/one documented skip in both normal/optimized modes).
The complete pre-delivery discovery run passed all **754 tests**. Optimized
search passed all **25 tests**, including complete MEL reconstruction.
Clean wheel/sdist/rebuilt-wheel content auditing passed (all module/assets
equal, RECORD hashes/sizes verified, all 1,455 required sdist inputs present),
as did strict Twine checks and installed CLI/four-profile conformance.
Installed full-suite and exact-head hosted results are recorded in the PR
qualification report; do not infer success from a pending job. An initial
local build correctly failed content auditing because the pre-existing build
directory contained GNATDOC-036 modules. A clean rebuild excludes those modules
and passes; no existing release artifact was replaced.
Hosted CI now repeats complete MEL qualification and browser
navigation, retaining structured evidence alongside the existing Core suite.

## Review and release boundary

Independent review and merge remain required. `READY_FOR_INDEPENDENT_REVIEW`
is only appropriate after all required qualification, including exact-head
hosted jobs, succeeds. This document is not release authorization.
After review/merge, prepare a **separate immutable official upstream release**,
provisionally v0.1.6. MEL must adopt that release through its existing hash-pinned
installation and independent publication verifier, not this working tree.
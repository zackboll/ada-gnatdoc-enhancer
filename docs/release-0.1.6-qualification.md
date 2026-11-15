# GNATDOC-037 — v0.1.6 candidate qualification

This is release preparation, not publication or consumer adoption. The final PR
delivery record supplies exact final commit/tree, candidate digests and exact-HEAD
hosted run results without embedding a commit's own hash in that commit.
`READY_FOR_MAINTAINER_REVIEW` requires every applicable gate to pass. Pending
source, artifact or hosted results are not passes.

## Prerequisites and preserved official baseline

Refreshed main: commit `a4befbec2ac8b40e7a0234853aa204e90d13a19c`, tree
`7802f094fe9f2d3e4c5ea4549a4c17881fe8f588`. PR #31 (GNATDOC-036) and PR #32
(GNATDOC-SEARCH-002) are merged. Exact-merged-main workflow
[43659846712](https://github.com/zackboll/ada-gnatdoc-enhancer/actions/runs/43659846712)
succeeded in all eight Python, wheel/sdist and browser jobs. v0.1.6 did not exist
at preflight. The clean release worktree is separate from the original checkout.

The four official v0.1.5 assets were independently acquired once, then preserved.
Tag object `c6ca2b445b089e7f50abc1779d76dd4ff3f0f1eb` peels to source commit
`0120bee2f2455e4c832d1d5ddae0a4cb03cb9477`, tree
`01900ddb099c801eeb92fba718f4c528f87d865f`; GitHub and Git agree.

| Official asset | SHA-256 |
| --- | --- |
| Wheel | `d712d330f213fc1909a66c47bc2c7e5e15d5ec687222bea3c4922f5243db4247` |
| sdist | `2bc2cc4160a182a2a9b1a4907f47198daabf88883888fa09d736913bd2931079` |
| release-provenance.json | `6c30b7a4ec987ab4f74a44d04586dcd57308dd592ac13f33c9444ef3acf0a8f3` |
| SHA256SUMS | `93e061866d52e13b6266c6fa0efb3b9c2e3a1bd1b4c818981a11a802ded74756` |

All checksums, 3,082 source-file identities, published archive member identities,
complete wheel RECORD, safe inventories, distribution metadata, strict Twine,
independently rebuilt-sdist content and 47 installed non-RECORD payload members
passed verification. Installed smoke/conformance ran non-editably outside the
checkout with PYTHONPATH unset. These are **baseline** checks, not v0.1.6 tests.

## Exact version-authority classification

The retained pre-edit audit has 59 matching lines. Active authorities advanced
to 0.1.6:

* `pyproject.toml`, `src/ada_gnatdoc_enhancer/__init__.py`;
* `tests/test_release.py`, `tests/test_cli.py`, `tests/test_distribution_archives.py`;
* `scripts/check_distributions.py`, `scripts/record_candidate_provenance.py`,
  `scripts/test_installed.py`;
* current README, changelog, migration, compatibility, example and release docs.

Current release rejection tests additionally reject v0.1.5 manifests. The two
completed Unreleased sections are consolidated into one v0.1.6 candidate entry.
Historical 014/015 and earlier comparators/tests, evidence, research observations,
and authentic fixture/provenance values remain unchanged. The authentic MEL
reference manifest stays 0.1.5; comparisons explicitly assert old/new versions
and normalize only that release field. `qualify_source_blocks.py` still requires
an official v0.1.5 interpreter for consumer reconstruction. CI's existing browser
job now acquires the independently pinned official v0.1.5 baseline; no new jobs,
governance or reviewer roles were introduced.

## Compatibility and source/native authority

`scripts/qualify_release_015_016.py` runs once in the verified official-wheel
environment and once with the candidate. It retains all established Core,
Imgproc, Geometry, MEL, navigation-disabled, symbol, operation, no-theme,
incoming-instance, lexical-example and historical Core-search profiles.
Unaffected complete file inventories/bytes must match except the exact serialized
release-version field. Historical comparators remain independently tested.

For affected MEL search, the comparator requires source/native reconstruction,
unchanged existing records/order, unique destinations, canonical serialization,
and only newly eligible declaration records. It reconstructs the exact shell
authority/count/hash and permits only the corresponding two manifest output
hashes plus version. Every unrelated byte, reformat, asset or inventory change
is rejected, even after output-side resealing. The official baseline reproduces
the retained old-record evidence; the independent public-spec/native-signature
oracle derives the complete destination set without calling the search collector.
The pinned reproduction must preserve all 1,143 old records and represent all
348 recovered declarations exactly once. These are pinned evidence outcomes,
not a new production declaration-count gate.

Current Core remains a separate independently pinned 1,487-record acquisition at
commit `9398e7fc899c0bb82f9071f4747d85dd97fa97a3`, tree
`166e938a45ac9085cc9ed0f4aaf16e4b156f8b13`. Its harness stages public specs
byte-for-byte into `public/`, retaining original-path compiler inputs separately.
The retained generated compiler configuration is stale: the explicit
`--without-verified-examples` option qualifies this acquisition's search and
lexical presentation only, not its mappings. Separate production-Core and
mixed-guide controls must still pass with compiler-verified decoration enabled.

Schema-3 is new opt-in functionality; v0.1.5 is not required to implement it.
The independent nine-output MEL portal byte oracle, source-block adversarial
tests, native parity, idempotence, determinism, atomic failure and complete
publication reconstruction remain required and unchanged in scope.

## Qualification evidence and artifact boundary

Complete local logs, baseline assets, source exports, browser observations and
candidate archive audits are retained under `/tmp/gnatdoc037/`. The original
preflight files are preserved. Source, installed-wheel and independently rebuilt
sdist suites must run on Python 3.11, 3.12 and 3.13. Installed execution must be
non-editable, outside source, with PYTHONPATH unset. Research/compiler controls
report actual skips when private inputs are unavailable; no skip is a pass.
Retained native acquisitions are not claimed as fresh GNATdoc/compiler builds.

Browser gates cover all 348 recovered MEL search/native navigations; Core search
with default/symbol/instance routing, history, themes and guides; schema-3 portal;
static example visual/clipboard/focus controls; compiler-verified production Core
and mixed guides; and synthetic no-JavaScript navigation controls.

Candidates must come from an immutable qualified Git export. Require strict
Twine, safe inventories, full RECORD verification, independently rebuilt-sdist
comparison and exact source/module/asset/input equality. Preserve Python 3.11+,
Apache-2.0, zero mandatory runtime dependencies and optional
`markdown-it-py==3.0.0` / `mdurl==0.1.2`. Provenance binds independently supplied
source commit/tree and keeps `publication_authorized: false`. SHA256SUMS covers
the exact final wheel, sdist and provenance bytes; retain its own digest separately.

Only after applicable local gates pass may a focused non-draft PR be opened.
Exact-HEAD hosted source qualification and candidate-artifact qualification are
reported separately in its delivery record. No merge, auto-merge, tag, publication,
deployment, PyPI/Alire upload or consumer modification is authorized. After
maintainer approval/merge, public assets require a fresh build and complete
qualification from the approved merged-main source.
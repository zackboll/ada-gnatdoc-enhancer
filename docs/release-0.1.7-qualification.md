# GNATDOC-REL-017 — v0.1.7 candidate qualification

This is release preparation, not publication, deployment or consumer adoption.
Exact final commit/tree, archive hashes, complete local results and exact-HEAD
hosted conclusions are recorded in the PR delivery record, avoiding self-hashing
commit claims. Pending gates are not passes; readiness requires all mandatory
technical gates. Final publication requires separate explicit maintainer authorization.

## Merged-main and official baseline authorities

Starting main is `d17570c33743103018900376f07364a95523ff08`, tree
`e5f005c7ec66c1dc577dac682dc3e6821b7da74d`. PR #35 merged with feature commit
`f0b5b425bd43382a3f587035ef3372c356928114` included. Exact merged-main run
[44020954054](https://github.com/zackboll/ada-gnatdoc-enhancer/actions/runs/44020954054)
must finish all nine jobs successfully. Initial observation was `MAIN_CI_PENDING`;
the delivery record reports its final observed state independently of PR-head CI.

The four official v0.1.6 assets were freshly downloaded, without replacing any
existing asset. Annotated tag object `77b55f509eebb8c80424cc5f231d5eb08e88f82c`
peels to commit `8661855bfc245c3389e2ef30a423c100776ff525`, tree
`a1e1fb0d9477c81ef3a1afb0adff2edb5bd53d4e`, matching published provenance.

| Official v0.1.6 asset | SHA-256 |
| --- | --- |
| Wheel | `adfec71188a868e3fb70a6da71a124c937f9e63e26a2f2e31af45364f49ffb27` |
| sdist | `c036f040bea187e9959908a6f6a1e30ff7eaef18e777baf9cc5a8d9d9b22703f` |
| release-provenance.json | `009b996f014383cfeaa35fbb54ac8dd6bed6833b7db1af842088d11fe608078b` |
| SHA256SUMS | `f92951691a6291beb9bdac76656a2b73f0aeb1b720ae4591d2e733a0830efffd` |

All three entries in official SHA256SUMS verified. Archive safety, RECORD,
published member identities, source identities, metadata, strict Twine and
independent baseline sdist reconstruction remain separate qualification gates.

## Version-authority audit

The pre-edit tracked audit found 59 matching lines for `0.1.6`. Active authorities
advance to 0.1.7: project metadata, module/CLI, current release and source-block
tests, archive-security fixture identities, distribution audit, installed smoke,
candidate provenance, current source-block reconstruction and current release docs.
Previous-release rejection adds 0.1.6. Historical 015/016 comparators and qualification
harness stay unchanged; the synthetic historical integration test explicitly pins
its pipeline version to 0.1.6, preserving its original comparison and security
assertions. Authentic source-block reference version
0.1.5, all historical evidence and prior release qualification records.

New 016/017 comparison and adversarial tests permit only the exact serialized
manifest version change; they reject missing/extra files, aliases, changed search,
CSS/router/native bytes, manifest reformatting and resealed output. Current hosted
browser gates acquire the independently pinned official v0.1.6 wheel, not a PR build.

Python 3.11/3.12/3.13, GNATdoc 26.0.0, zero mandatory runtime dependencies,
`markdown-it-py==3.0.0`, `mdurl==0.1.2`, `py3-none-any` and Apache-2.0 remain.

## Compatibility and source-browser contracts

`scripts/qualify_release_016_017.py` reconstructs official and candidate output on
identical approved source/native inputs. It retains existing Core, Imgproc,
Geometry, MEL, guide/highlighting, navigation-disabled, symbol, operation,
no-theme and incoming-instance profiles and adds full MEL search, resize and
schema-3 source-block compatibility. Complete inventories and bytes must match
except the exact serialized version. All 1,143 old MEL search records and 348
recovered declarations must remain unchanged, with independent source/native
oracle identities and signatures. Existing source-block nine-output oracle and
security regressions remain required.

`scripts/qualify_source_view.py --baseline-python` builds disabled output with the
verified official wheel interpreter, then independently reconstructs v0.1.7
enabled MEL/Core pages against retained source/native inputs. The predecessor
never enables unsupported source view. Every published specification must match
original source bytes; public declarations, line anchors and overload identities
must reconcile with independent fixture oracles. Require determinism, idempotence,
strict ownership/hash verification, tamper rejection and atomic failure.

Chromium includes MEL Navigation_Report at 663, Submit_Navigation_Report at 775,
distinct Core Create overloads, browser history, reload, direct links, fresh tabs,
keyboard, desktop/mobile, light/dark and JavaScript-disabled readability/copying.
Existing search, resize, authored-HTML and verified-example browser gates remain.

Source browsing is default-off. Enabling it deliberately publishes **complete
selected `.ads` specifications, including private sections**. `.adb` implementation
body browsing is deferred. MEL Bridge adoption requires a subsequent separately
qualified consumer change. Retained fixtures are not fresh private compiler,
GNATdoc, integration or hardware qualification; unavailable research tests must
report their actual skips rather than claim passes.

## Distribution and evidence boundary

Local campaign evidence is retained separately under `/tmp/gnatdoc-rel-017/`.
Release candidates must be built from a clean immutable Git export. Run complete
applicable suites in nine isolated source/wheel/rebuilt-sdist Python environments,
with actual counts. Installed tests are non-editable, outside checkout and with
PYTHONPATH unset. Require strict Twine, safe paths, no links/duplicates, complete
RECORD and exact source/module/asset/input correspondence, metadata, dependencies,
entry points, CLI, installed inventories and independent sdist wheel reconstruction.

Exactly four candidate assets belong in the candidate directory: wheel, sdist,
`release-provenance.json`, `SHA256SUMS`. Provenance binds independently supplied
source commit/tree, archive sizes/hashes, rebuilt-wheel correspondence, complete
installed inventories, tool versions, qualification outcomes and source-browser
scope, retaining `publication_authorized: false`. Candidate assets are technical
evidence, never permission to publish or overwrite existing artifacts.

After the preparation PR merges, final official assets must be **freshly built
and fully qualified against the approved merged-main source** before separately
authorized publication. One non-draft PR, auto-merge disabled; no merge, approval,
tag, publication, deployment, PyPI/Alire upload or MEL Bridge edit is authorized.
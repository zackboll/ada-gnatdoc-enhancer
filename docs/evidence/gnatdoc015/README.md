# GNATDOC-015 — v0.1.1 release preparation

Preparation only: no tag, publication, merge or consumer modification is authorized.
Starting merged main is `5ac7be66d23169dba7f9d13187a3eec5c8caee3c`, tree
`fd6c94ed68e0e9e70e48e0b8ac6e26952e9d4f10`; reviewed GNATDOC-014 head is
`aa40ad9727c0a3fc7c38b011dd851e7e96f68f6d`. Fresh GitHub refs and PR #16 confirm
these identities. `starting-main-run.json` and `starting-main-jobs.json` record
all six passing jobs from post-merge run 39902608553, not a prior PR run.

## Executed evidence before the evidence commit

The clean `git archive` source was commit
`201e6cbd1230dee8acacf623909ab50e12fc44a6`, tree
`112e7803b84aab233affa753db8a35e7cbaa720f`. These are explicitly **initial**
candidate identities, not claims about a later PR head. The independent expected
commit/tree and complete source/archive membership appear in
`initial-candidate-provenance.json`. It does not authorize publication.

- `distribution-matrix.json`, nine `3.*-*-result.json` files and complete test
  transcripts: **579 distinct tests in each environment**, 5,211 executions;
  zero failures, errors or skips. All 576 merged-main IDs are retained, with three
  additive release archive controls (`test-retention.json`). Each Python wheel
  environment installs the same canonical Python 3.11 candidate wheel; each sdist
  environment uses its independently rebuilt wheel and extracted shipped tests.
- Build/rebuild logs, strict Twine results, complete archive inventories, exact
  membership/content audits, installed smoke/conformance, package/toolchain lists,
  compilation and dependency checks are retained per Python/environment. Canonical
  and rebuilt wheel **complete member bytes** agree, not compressed archive bytes.
- `official-v010-download.json`: freshly downloaded original public v0.1.0 wheel,
  sdist, provenance and checksums, independently checked against retained official
  hashes/Git source. Official non-editable installation bytes were checked.
- `default-publication-parity.json`: 12 freshly regenerated official/candidate
  publication comparisons (both Core revisions × default/symbol/incoming, MEL
  default/symbol and four synthetic profiles). The only difference is the exact
  canonical `enhancer_version` value, 0.1.0 → 0.1.1. No asset/native/link/text drift.
- `imgproc-wheel.json` and `imgproc-sdist.json`: actual non-editable candidate and
  rebuilt wheel independently pass 329 native declarations, 586 source/type-mark
  occurrences / 14 Core types, 350 unchanged local links, 329 source-owned operation
  destinations and fresh 1,596/1,596 source/native documentation coverage checks.
  Two-copy determinism, repeat idempotence and installed CLI `verify` pass. Default
  bytes equal original official v0.1.0 except manifest version; opt-in bytes equal
  verified merged GNATDOC-014 except that same version. `consumer-installed-identities.json`
  binds installed module bytes to the actual initial archives.
- `live-browser-wheel.json` and `live-browser-sdist.json`: **224 top-level traces
  each**, plus direct fragments, eight default iframe controls and eight network/
  console summaries (240 assertion records per campaign), zero failures. Exact
  declaration visibility, mouse/keyboard, Back/Forward, JS on/off, desktop/mobile
  and light/dark pass over unintercepted live Core HTTPS with reviewed page bytes.
  The deployment identity was freshly rechecked before/after: deployment 7190346920,
  Core commit `aa8a378ab614e9a5fc4f43765cd3ff1bbcf6a44d`.
- `protected-inputs.json`: 1,095 historical evidence/assets/GNATDOC-014 implementation
  and test files verified unchanged against merged main. Runtime changes in this
  PR are limited to `__version__`; no implementation/security protection is removed.
- `superseded-harness-attempts.json`: three initial harness failures caused by
  dereferencing a venv interpreter symlink are recorded, not counted as passes.
  The correction preserves the venv executable path; runtime was not weakened.
- The provenance recorder was positively checked against the initial authorized
  source and negatively checked with the wrong expected tree (rejected before
  reading archives). CI now checks out the actual PR head, retains exact source
  and complete archive provenance, and remains read-only without publishing secrets.

## Final-head qualification and handoff

After this evidence commit, **rebuild and rerun** all nine environments, both
installed consumer/browser campaigns and all default profiles from a clean final
source snapshot. Do not reuse the initial archive digests. `qualify_distributions.py`
takes `--source` and a new `--workspace`; `qualify_final_consumers.py` takes that
source and the retained `/home/zboll/qualification/gnatdoc015` workspace and expects
`distributions-final`. It creates fresh installations/browser/default campaigns.
Original attempts and outputs remain available there; nothing modifies consumers.

Final exact PR head/tree, new canonical/sdist/rebuilt identities, results and hosted
links belong in the **PR handoff comment**, not a self-referential commit claim.
Final-head hosted artifacts contain `candidate-provenance.json` with independently
supplied Git commit/tree and full source/archive inventories. Download them, verify
actual contents/digests against Git, and link the successful exact-head six jobs.
Only after all final gates pass may the handoff say `READY_FOR_INDEPENDENT_REVIEW`.
Until then the disposition is pending, not qualified by the initial campaign.

Local tools: Python 3.11.17 / 3.12.15 / 3.13.16, build 1.6.1, isolated setuptools
84.2.1, twine 7.0.0, Node v20.19.2, Playwright 1.62.0, Chrome 156.0.8078.47. Source
venv pip/backend versions differ by Python and are recorded in `3.*-toolchain.json`
and `3.*-*-packages.json` (3.11 starts with pip 24.0 / setuptools 79.0.1).

Historical GNATDOC-014 and v0.1.0 records remain unchanged. Retained native inputs
are hash-revalidated, not freshly generated. Fresh installed-package/browser
campaigns must independently verify the actual v0.1.1 archives and mutable Core
HTTPS bytes/deployment identity. Imgproc PR #81's Core policy, authored-site parity,
full production browser/security qualification and Pages deployment stay separate.
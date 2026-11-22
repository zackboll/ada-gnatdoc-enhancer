# GNATDOC-REL-018 — v0.1.8 release preparation

This is a preparation record, not a publication or authorization. The candidate
provenance and exact-HEAD CI carry the immutable source and measured results;
those values cannot be embedded in the source commit that they identify. Do not
infer a passing gate from its inclusion in this procedure.

## Authorities

* Starting main and frozen feature-complete comparator:
  `502bcae9c0194642394347ba7347c28c0af4b90a`, tree
  `d950ad3b8413ad3a99975a308eaec06368303d0d`. Includes PR #37 (merge
  `624c02e3b08198e77d3e126f745431af1b6dc8b0`) and PR #38 (starting main).
  [Merged-main run](https://github.com/zackboll/ada-gnatdoc-enhancer/actions/runs/45068563086)
  must independently pass all nine jobs; PR-head runs are not a substitute.
* [Official v0.1.7](https://github.com/zackboll/ada-gnatdoc-enhancer/releases/tag/v0.1.7):
  annotated tag object `ff2ad9b04a9ed9b19bab557683e25c5aeadf5980`, peeled commit
  `5efaea9ac018101f33ac5b68b1b98ab4b3e170f6`, tree
  `733c472ab4c3a570f2156487c3cde7b6fd0c187a`. The downloaded release assets and
  every `SHA256SUMS` entry were independently checked. The official wheel and
  sdist were audited against the tagged sources; the wheel was installed and
  passed its release's CLI, asset and four-profile conformance checks.

| Official asset | SHA-256 |
| --- | --- |
| `ada_gnatdoc_enhancer-0.1.7-py3-none-any.whl` | `957c65797b03b5c6b3779e2a1918730a2e44749670e37535d2c8ff3e109f3ba4` |
| `ada_gnatdoc_enhancer-0.1.7.tar.gz` | `09814e5bb08a9338d38f17ed83b6d936e8d1c1e81ea72c4218b7f434f051cb6b` |
| `release-provenance.json` | `9251e3d23bc693184263ccfcf9e6323bdef0a61599f2062233bd6ba54f8e7889` |
| `SHA256SUMS` | `e12f4cce148bda2b340942427deed05444bfef91d1a2ed0e347eb38e1fe89dfd` |

## Version audit

Tracked version references were inventoried before editing. Classification:

| Class | Treatment |
| --- | --- |
| Active authorities | Advance project/module, candidate filenames and install docs, archive/installed CLI checks, source-view/body and source-block candidate checks, provenance and active CI |
| Historical versions/evidence | Preserve older comparators and their tests, prior qualification records, changelog entries, evidence and research outputs |
| Compatibility inputs | Keep the official v0.1.7 package and tag, the frozen v0.1.7 engine, and older independently pinned fixture/reference bytes |
| Qualification fixtures | Advance current positive package and manifest assertions; add explicit rejection of v0.1.7 in obsolete identity controls; keep old-version and historical authored fixtures unchanged |

## Qualification contracts

`scripts/qualify_release_017_018.py` reconstructs source-disabled release
profiles (including Core, Imgproc, Geometry, MEL, search, resize, authored
examples and source blocks). `scripts/qualify_source_view.py` independently
reconstructs the official and candidate schema-1 variants, with highlighting on
and off. `scripts/qualify_body_navigation.py` requires frozen-main parity in
all three source modes and independently verifies exact original source, native
HTML and package/operation navigation. The comparator checks all publication
files, not just declared hashes, and rejects unrelated or resealed differences.

Schema 1 publishes complete selected `.ads` files, including private sections.
Schema 2 additionally publishes complete authorized `.adb` files, including
private helpers. Source browsing is default-off. No generated metadata grants
authorization. Matching is conservative and lexical; unsupported or ambiguous
operations have no guessed implementation link. Mandatory journeys use pinned
fixture bytes: `Navigation_Report` #L663, `Submit_Navigation_Report` #L775/#L509,
`Exec_Stare` #L74/#L46, `Wait (Abort_Request)` #L123/#L162, and distinct Core
`Create` overloads. Retained MEL, Scheduling.Commands and Core are separate
acquisitions. Historical body page/link/omission counts are respectively
39/350/678, 40/359/710 and 1/200/847; these are not acceptance constants.

The local campaign records real Chromium source inventories, text/clipboard,
keyboard, layout, history/reload, offline and error checks across desktop/mobile,
light/dark, and JavaScript on/off. Separate search, resize, examples, authored
content and router campaigns are retained. Mutations include stale hashes,
wrong real destinations, swapped ownership, unsafe paths and resealed output.

Require Python 3.11/3.12/3.13 × source, non-editable wheel and non-editable
rebuilt sdist wheel, plus normal/optimized security controls. Node.js and Chromium
are qualification tools only. Installed use is offline, supports GNATdoc HTML
26.0.0, remains Apache-2.0 with zero mandatory dependencies, and offers only the
existing optional `markdown-it-py==3.0.0` and `mdurl==0.1.2` pins. Private Ada
compiler, Libadalang, fresh GNATdoc acquisition and external integration are
separate from compiler-free reconstruction of retained fixtures.

## Candidate assets and status

Build from the exact committed Git export. Check archive safety, RECORD,
metadata, strict Twine, source/sdist/installed content and rebuilt wheel equality
over decompressed members. Preserve `publication_authorized: false` in
`release-provenance.json`. Keep the independent rebuild and test logs outside
the four public candidate files (wheel, sdist, provenance and `SHA256SUMS`).
Only all required local and exact-HEAD hosted results allow
`READY_FOR_MAINTAINER_REVIEW`. No tag, release, deployment or consumer change
is part of this PR. After merge, requalify and regenerate against the approved
merged-main SHA; publication requires separate maintainer authorization.
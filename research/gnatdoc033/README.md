# GNATDOC-033 qualification

Delivery status: **HOSTED_CI_PENDING**. No approval, merge, release or deployment.

## Starting identities

Authenticated `git fetch origin main` matched the requested main commit
`a0d4b5f68017cd3640cf1c5d1fa196d36fb056d8` and tree
`ba1ce0f30ededa258293aad994fb955a071ad9a7` before branching to
`feature/gnatdoc-033-verified-example-links`. Final identities are reported in the
PR because a commit cannot contain its own identity.

## Interfaces and implementation

* Build-time `scripts/generate_verified_examples.py`: authentic project/source,
  qualified compiler, fresh build, native snapshot and public enhancer config;
  optional separate byte-identical presentation export and project scenarios.
* GNATDOC-032 ALI verifier is reused unchanged except for factoring precise LAL
  selection into a reusable `SelectionSession`; the original API delegates to it.
  Its inventory digest is refreshed for that deliberate refactor.
* Installed consumer: `[guides.verified_examples] mapping/sha256`, schema 1 JSON;
  no semantic dependencies, no URL authority, no new human-approval workflow.
* Existing `Resolver.positions` merges verified token spans and conservative
  lexical results, suppressing overlap. Existing `code` and Markdown renderer
  retain every character. Search rendering clears the mapping alongside disabled
  example options, preserving search records.
* Full usage/schema/trust boundary: `docs/compiler-verified-examples.md`.

## Source-backed link counts

The two pinned `tests/verified-fixtures/*/mapping.json` records contain **16 newly
linked call sites** (4 Core + 12 overload-fixture). Core has 6 rendered links:
4 compiler-confirmed calls and 2 pre-existing lexical Mat type marks. The overload
fence has 12 rendered links, all compiler-confirmed. No production guide coverage
or general Ada coverage is claimed. Deployed documentation is untouched.

Core compiler defining positions are `src/opencv-core.ads:1130:13` (Mat Create),
`:1242:13` (Mat Clone), `:3661:13` (Rows), `:3669:13` (Columns). The fixture covers
Mat/UMat Clone, Integer/String Pick, argument-count overloads, reordered named
parameters, defaults, contextual return-type overloads and qualified calls.

## Executed local gates

Retained evidence in `evidence/`:

* Baseline: **703 tests passed** (339.265 s).
* Existing + new regressions: **722 passed** (358.808 s), after an earlier
  **721 passed** run (356.657 s). A final 723-test run adds complete authored
  overload rendering; results are reported on the PR.
* Consumer: **20 passed**, normal and `-O`, including full pipeline idempotence
  and wrong-destination verification; original 18 also passed with
  `PYTHONOPTIMIZE=1`.
* Real compiler generator: **4 passed** normal, `-O`, and `PYTHONOPTIMIZE=1`.
  Fresh compile count, deterministic new builds, wrong-LAL-overload injection,
  unsupported canonical form and source mutation during selection are checked.
* GNATDOC-031: **23 passed, no skips** in the private compiler/Core environment.
* GNATDOC-032: **18 passed, no skips**, normal and `-O`; includes original
  generics/renamings/dispatch negatives and real Core wrong-UMat injection.
* Browser: **4 passed** (JavaScript on/off × light/dark); exact example text,
  native clipboard, focus, computed syntax colors, Mat Clone and Mat-returning
  Create clicks; no external requests or runtime errors. Legacy browser checks
  also pass 24 cases and 24 byte-identical disabled screenshots. Existing example browser checks also
  passed 24 cases and 24 byte-equal disabled screenshot comparisons.
* Wheel/sdist/rebuilt wheel audit passed. Wheel METADATA is byte-identical to
  baseline; mandatory dependencies remain empty and guides extras unchanged.
* Clean no-deps wheel installation without Libadalang passed installed smoke and
  four-profile conformance. Compiler tools are never runtime imports.
* Disabled output compared against the verified main source: five complete
  fixture campaigns (Core, Imgproc, Geometry, MEL, full historical Core-search)
  have byte-identical file inventories. This is verified-main parity, not a claim
  about an independently downloaded release.
* Missing/malicious mapping, duplicate JSON keys/spans, conflicting declarations,
  invalid coordinates/token boundaries, unsupported classifications/kinds,
  modified source/project, profile/anchor changes, incorrect pin, arbitrary URL,
  incomplete context and reordered overloads fail closed.

Compiler-qualified controls are opt-in and local; hosted CI exercises portable
compiler-free fixtures, optimized consumption, offline predecessor controls,
packaging and browser behavior. It does not certify the compiler installation.

## Performance

On this Linux/Python 3.13 host (five initialization samples and five batches of
100 renders, medians): reduced authentic Core resolver initialization 0.596 s
lexical / 1.077 s verified; 9-line fence rendering 0.966 ms lexical / 0.928 ms
verified. Noise is larger than that rendering difference; no speedup is claimed.
Fresh compilation: Core one unit / four mappings 0.261 s; fixture one unit /
twelve mappings 0.220 s. ALI validation/index costs are retained separately.
These are narrow fixture measurements, not whole-project scalability claims.

## Remaining limitations

Only qualified GNAT 16.1.0 ALI syntax and precise LAL 26 ordinary public static
subprogram declarations. Generic instances/renamings, dispatch, implicit/inherited,
operators, nested public scopes, local declarations, incomplete fragments,
non-ASCII/tabs/source remapping and landing mappings remain unsupported. Local
receipt and configuration pins are not signed attestations or human review.
Native evidence must remain immutable during generation/consumption.

The exact changed-file inventory is in `changed-files.txt` (including itself);
the PR reports final commit/tree and hosted-check identities/status.
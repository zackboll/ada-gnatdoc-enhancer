# GNATDOC-SOURCE-002 qualification contract

Starting main: `5efaea9ac018101f33ac5b68b1b98ab4b3e170f6`.
This feature does not change version 0.1.7, publish a release, or qualify a
consumer deployment. Exact tested commit/tree, local totals, hosted run and PR
disposition belong in the delivery record, not a self-referential source hash.

## Implementation boundary

`source_view.highlighted_lines()` uses one `source_lexer.tokenize()` pass per
specification, validates its contiguous source partition, and serializes only
escaped source and seven fixed lexical classes. Line wrappers and number links
remain unchanged. Syntax highlighting follows `Config.highlight`; source browsing
remains default-off. No semantic classification, ownership, declaration mapping,
dependency, JavaScript, evidence-schema or `.adb` policy change is introduced.

The standalone source CSS reuses the GNATdoc palette in both system themes.
Targeted lines override nested token colors with the paired system `MarkText`.
Selection uses the original DOM source; Chromium's established terminal-LF visual
selection exception does not change source data.

## Independent compatibility authority

Use the released v0.1.7 wheel, SHA-256
`957c65797b03b5c6b3779e2a1918730a2e44749670e37535d2c8ff3e109f3ba4`,
installed non-editably outside the checkout. `scripts/qualify_source_view.py
--baseline-python /absolute/official-env/bin/python --workspace
/absolute/evidence/publication --browser` reconstructs retained complete MEL/Core
publications with independently fingerprinted authentic source/native inputs:

1. Browsing disabled: complete publication inventories/hashes must be identical.
2. Browsing enabled, highlighting disabled: all source/API HTML bytes must be
   identical; only the source stylesheet and its exact manifest hash may change.
3. Browsing enabled, highlighting enabled: only fixed token-span insertions,
   source CSS and their exact output hashes may change. Removing just those
   spans must recover official HTML bytes. The entire remaining manifest,
   including source/native schema, source hashes, destinations and inventory,
   must be byte-identical after the classified hash substitution.

Existing previous-release comparators are not relaxed. Native API declarations,
search/navigation/resize assets, authored HTML and guides are outside the delta.
Rebuilt publications must be deterministic and idempotent; reversed package
traversal and original source-file identity are separately checked.

## Fidelity, hostile input and browser coverage

Unit/mutation tests cover every lexical category, mixed-case keywords, Unicode,
quotes, doubled quotes, attributes/qualification ticks, based numbers, tabs,
blank lines, trailing spaces, LF/CRLF, terminal newline choices, empty sources,
Unicode separators and a 20,000-line source. Invalid/overlapping/incomplete lexer
partitions fail closed. Recomputed output hashes cannot authorize malformed or
nested tokens, concealed text edits, active markup, attributes, hyperlinks,
resource additions, missing/duplicated/reordered lines, forged source ownership,
hashes or native destinations. Existing independent reconstruction remains the
authority; output manifests cannot authorize themselves.

Chromium visits the full published source inventory in desktop/mobile,
light/dark, JavaScript-enabled/disabled combinations, checking DOM text, ordered
line anchors, lexical classes/colors, keyboard focus, target colors, selection
and actual keyboard clipboard copy. Four additional hostile UTF-8/LF/CRLF source
controls exercise all categories and horizontal scrolling. The established MEL
`Navigation_Report` → `#L663` and `Submit_Navigation_Report` → `#L775` journeys,
Core overloads, history, reload and direct links remain. External requests and
JavaScript runtime errors fail the campaign.

## Required gates and limitations

Run the complete Python 3.11/3.12/3.13 source/wheel/rebuilt-sdist matrix, installed
CLI/conformance, archive/content identities, strict Twine, optimized security and
verified-example tests, compiler-free research regressions, previous-release
compatibility, source/native reconstruction and the existing search, resize,
navigation, authored HTML/example and source-block browser campaigns. Distinguish
unavailable compiler-dependent research skips from passed tests. Hosted checks
must be green at the exact final HEAD before `READY_FOR_INDEPENDENT_REVIEW`.
Pending hosted qualification is `HOSTED_CI_PENDING`, never a pass.

Retained GNATdoc fixtures are not a fresh compiler/GNATdoc execution or MEL Bridge
adoption. Lexical display is not compiler validation, semantic resolution or an
independent assistive-technology audit. Clipboard/OS newline conversions are
separate from the exact decoded UTF-8 DOM-text contract.
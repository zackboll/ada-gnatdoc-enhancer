# Current-package type marks: authentic reduced MEL declarations

Source: `zackboll/ams-gra-mel-bridge` at
`a5484514cfae3b7bccde078118b838fa40ce4d0e` (actual PR #117 merge).
`provenance.json` records original source blobs, complete-file SHA-256 hashes,
exact original declaration offsets/lines, pristine GNATdoc 26.0.0 snippets,
and existing destinations from `docs/gnatdoc-native-anchors.json` (Git blob
`bcd145d95d14fb2bf75c1a250311cc5f19654a66`). No anchors were synthesized.

Reduction boundaries: 18 complete public type declarations from Image,
Instrumentation and Status; comments between declarations, unrelated public
declarations, context clauses (except the original `with AMS.MEL.Status` needed
by Navigation_Report) and private parts are omitted. Original declaration
text and pristine tokens are retained verbatim. The reduced files support lexical
and rendering regressions, **not full-unit visibility proof** or a compilable MEL
replacement. Full-unit qualification uses immutable complete source and authenticated
pristine output externally. Synthetic mutations are explicitly labeled in tests.
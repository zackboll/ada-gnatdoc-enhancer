# GNATDOC-012R2 corrective qualification

The existing PR #14 is reconciled by a normal two-parent merge with reviewed
R3 main. No router was edited during reconciliation. Version remains 0.1.0.
The 561 required tests are retained; three additive malformed-wheel tests bring
the total to 564 after an observed wheel-symlink audit failure was repaired.
All nine source/wheel/rebuilt-sdist environments pass without skips or errors.

`qualification-summary.json` binds the qualified source commit/tree. These
evidence-only files were collected later and are excluded from distributions.
Historical GNATDOC-011/R1/R2/R3 and original GNATDOC-012 evidence is unchanged.
The old 543-test, 860-file and archive-hash claims are historical only.

R2, actual merged R3 development, old release and corrected release publications
are independently reconstructed. R3 development to release differs only by the
manifest version field. Old symbol-only output additionally changes the approved
router and dependent manifest; it is not called byte-identical. Native/source
authority is checked independently, never authorized by candidate manifests.

Retained Core and MEL acquisitions were hash-checked, not freshly compiled or
generated with GNATdoc. Consumer repositories are unchanged. The complete
workspace (archives, screenshots, prior/superseded runs and intermediate sites)
is `/home/zboll/qualification/gnatdoc012r2/`.

Exact submitted head, normal-push identity agreement and final-head hosted run/job
IDs and inspected conclusions are recorded after push in that workspace's
`FINAL-HANDOFF.md` and existing PR #14. This avoids self-referential artifacts.
The final evidence manifest binds the permanent record, excluding itself.
No release publication, tag, PR merge or consumer migration is authorized.

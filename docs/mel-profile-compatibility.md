# GNATDOC-004 — source-verified MEL presentation compatibility

## Result and scope

All four original, hash-verified GNATdoc 26.0.0 native API acquisitions pass
structural qualification. **Production adoption is not complete.** The work
stops at independent review, without consumer changes, deployment, release,
workflow migration, merge or auto-merge.

**READY_FOR_INDEPENDENT_REVIEW**. Hosted push run `39007740840` and PR run
`39007792510` pass all Python 3.11/3.12/3.13 and wheel/sdist jobs on tested
implementation `d875f3a9051dfb2c1c541cf377e911b9412787d8`; exact job/step
results are in the new `hosted-ci.json`. Evidence-only final-head checks and
final tested SHA are recorded in PR #4, without self-referential commit claims.

Starting SHA: `3be5739901e2ac5559f66a47a0a1765987942173`, fetched `origin/main`
including merged GNATDOC-003. The tree was clean and all **134 baseline tests**
passed on Python 3.13.5. Final tested SHA and exact hosted check identities are
recorded in the PR (a commit cannot contain its own identity).

## Reproduction and independent authorities

Before implementation the original GNATDOC-002 source and pristine-native
SHA-256 inventories were checked, without regenerating or replacing inputs.
The complete MEL audit reproduced exactly three mismatches:

| Package | Declaration | Before | After |
| --- | --- | --- | --- |
| AMS.MEL.RF.C2 | Add_Job_Intervals | inventory mismatch | subprogram-renaming-profile |
| AMS.MEL.RF.Product_Rx | Complex_I16 | inventory mismatch | record-convention-aspect |
| AMS.MEL.RF.Product_Rx | Complex_I8 | inventory mismatch | record-convention-aspect |

MEL source revision remains `6065129aba5dee89e70b61e05a9e1c9b2c3061c0`.
The renderer is AdaCore/gnatdoc revision
`04606c2152636ca2125047e3db701b50ed356cd4`, release v26.0.0,
binary version `GNATdoc 26.0.0 (20260415)`.
No new consumer native build is claimed: qualification reuses the independently
pinned original acquisition and warning logs. Historical GNATDOC-002 and
GNATDOC-003 evidence is unchanged.

Renderer implementation locations, file hashes and exact excerpts are in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc004/provenance.json`:

* `source/gnatdoc-comments-extractor.adb:540–551`: the subprogram-renaming
  branch passes `F_Subp_Spec`, not the target clause.
* `source/gnatdoc-comments-extractor.adb:2623–2648`: subprogram extraction
  copies the specification's token start through token end.
* `source/gnatdoc-comments-extractor.adb:2207–2241`: record extraction stops
  at `F_Type_Def.Token_End`, before the declaration's aspects.
* `source/gnatdoc-comments-extractor-code_snippets.adb:80–152,373–384`:
  copies the selected token range, removes comments, and explicitly appends
  `;` to record snippets. Whitespace/empty lines are presentation, not identity.
* `source/backend/xml_templates/gnatdoc-entities-proxies.adb:278–284`:
  the template's code value comes from the extracted Ada snippet.

Authentic MEL snippets and complete source declarations independently confirm
these boundaries. Absence from HTML alone is **not** a semantic proof.

## Projection rules and proof boundaries

The implementation is in
`/home/zboll/git/ada-gnatdoc-enhancer/src/ada_gnatdoc_enhancer/profiles.py`.
Exact matching remains the default. The existing expression-function and
enumeration-first-eight/last rules remain supported, as do pre-existing
top-level contract-aspect handling and all ambiguity/integrity protections.

### `subprogram-renaming-profile`

Supported source grammar:

```text
(procedure | function) Identifier [(Named_Formals)] [return Qualified_Type]
  renames Direct_Identifier;
```

The entire declaration is tokenized, with balanced parentheses, comments and
quoted literals handled lexically. The callable parser consumes all formal
groups before the terminal renaming clause. Names, explicit modes, qualified
type marks, complete default-expression tokens and function return types must
match the entire native callable profile, with no native trailing clause or
semicolon. There is no implicit-mode or default-value semantic equivalence.

An ordinary, flat source-owned public package must supply exactly one direct
target declaration. Only the defining name may differ between callable profiles.
The target must be an ordinary complete callable declaration, not another
renaming or expression/body/generic declaration. Even distinguishable target
overloads, chains, cycles, cross-package names, operator names, generic scopes,
nested packages and executable scopes are declined. Anonymous access formals,
complex subtype syntax and overriding renamings are not newly supported.

The renamed declaration still needs its **own unique observed native anchor**;
the target's anchor cannot substitute for it. Source target identity and omitted
tokens are reported as source-owned, not visibly rendered. No target hyperlink
is introduced: existing local-type linking policy is unchanged.

### `record-convention-aspect`

Supported source grammar:

```text
type Identifier is record
  Identifier {, Identifier} : Qualified_Type;
  ...
end record
  [Ada comments]
with Convention => C;
```

Only simple nonempty component-only records with unique component names and
qualified type marks are projected. The entire record structure, field names,
order, grouping, types and visible punctuation must match. The projected ending
is exactly `end record;`. The original native snippet and anchor are retained.
The omitted `with Convention => C` tokens remain explicitly source-owned.

Other conventions, `Pack`, multiple aspects, malformed/trailing syntax, variant
records, extensions, discriminants, constraints and component defaults are not
newly authorized. Such records can still match exactly when fully rendered;
they cannot use this omission rule. Commented or quoted aspect-like text cannot
activate it. Hash pins and publication source fingerprints remain mandatory:
the visible projection alone cannot prove identity of omitted source text.

## Full real-site results

| Consumer | Packages | Native sections preserved | Local type links | Structural |
| --- | ---: | ---: | ---: | --- |
| Core | 195 | 1,268 | 2,459 | pass |
| Imgproc | 1 | 314 | 326 | pass |
| Geometry | 2 | 130 | 171 | pass |
| MEL | 29 | 1,237 | 1,418 | pass |

Every full run checks original input hashes, all scanner declaration profiles,
isolated dry-run bytes, enhancement, independently reconstructed publication,
native declarations/anchors/visible content, original CSS bytes, original and
staged source fingerprints, two-copy determinism, byte-idempotence and rejected
anchor/link/asset/source tampering. Full report inventories support independent
reconstruction. The scanner audit is not a substitute for consumer coverage.

Consumer coverage gates pass on both pristine and enhanced sites: Imgproc
**1,512/1,512**, Geometry **452/452**, MEL **4,294/4,295**. MEL's Health Status
metadata package renaming remains the one unrendered, uncredited exception.
All four warning ratchets pass against the original logs with **0 additions,
0 removals**; MEL retains its historical **73** warnings. The unchanged MEL
approved integrity policy passes for **1,162 protected files**, foundation
`42648a92eb0cc84b2980d16db6028992c0494ba1`, reviewed native tests in the original
state, isolated checkout clean afterward. No warning/coverage/policy changes.

## Tests, browser and distribution

**189 tests pass**: the 134-test baseline plus 55 focused regressions. The
original test that rejected Complex_I8's then-unsupported omission retains its
negative purpose using an unrelated `Pack` aspect; it was not deleted or skipped.
Authentic reduced fixtures separately cover both Complex_I16 and Complex_I8,
the renamed declaration and its independent target. Wrappers and mutations are
explicitly synthetic. Negative tests cover profile changes, missing/ambiguous
targets, chains/cycles, lexical boundaries, unsupported aspects/structures,
duplicate/missing anchors, ambiguous native matches and source mutations.

The four original synthetic profiles pass separately. A clean installed wheel
and a wheel rebuilt from the extracted sdist each pass all 189 tests out of
tree, installed assets/CLI checks and four-profile conformance. Python 3.11,
3.12 and 3.13 hosted jobs run the same focused regressions; full local sites
are not represented as hosted CI inputs. Existing setuptools license metadata
deprecation warnings are not suppressed.

Browser evidence records **38 passing assertions per site** in Chromium
156.0.8078.4 across desktop/mobile,
light/dark, search/clear, bookmarks, history, keyboard focus, responsive layout,
native/local-type destinations and JavaScript-disabled navigation. It tests
the acquired navigation policy: Core/MEL are package-only, Geometry/Imgproc
have operation categories, and Imgproc has just one package. Initial driver
failures (requiring operation categories everywhere and two packages) are
retained in evidence; the driver was corrected, not the site or its policy.
These API-only runs **do not qualify authored MEL portals or guides**.

## Evidence and reproduction

New evidence is under
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc004/`:

* `baseline.json`, `mel-before-profiles.json`: clean start and three failures.
* `provenance.json`: renderer/excerpt hashes and exact selected source ranges.
* `*-profiles.json`: full audit and explicit omitted-source ownership.
* `*-report.json`, `compatibility-matrix.json`: four complete structural runs.
* `consumer-gates.json`: original coverage, warning and integrity executions.
* `*-browser.json`, `browser-initial.json`: executed browser assertions/history.
* `validation.json`: test/distribution/log identities and remaining blockers.
* `hosted-ci.json`: exact successful implementation CI runs/jobs/steps.

```sh
/absolute/python /home/zboll/git/ada-gnatdoc-enhancer/scripts/qualify_profile_sites.py \
  --acquisition /absolute/original-gnatdoc002-validated-acquisition \
  --workspace /absolute/new-workspace --output /absolute/new-evidence \
  --task GNATDOC-004
```

Source/native inventory differences must fail, never silently replace pins.
Remaining adoption blockers include Core's **25 generic-instance summary gaps**,
unqualified external Core targets, native dependency integration, authored guides
and portals, compiled examples and consumer workflow/publication integration.
No four-site structural pass is a production adoption certificate.
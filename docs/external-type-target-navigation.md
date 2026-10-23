# GNATDOC-014 — opt-in top-level external type navigation

## Scope and contract

Starting point: freshly fetched `origin/main`,
`4ee95e8c95b8c7f54397a07e3e1c507783c115aa`.
Implementation branch: `feature/014-top-level-external-types`.

```toml
[presentation]
type_links = true
external_type_target = "_top"
```

Omitting this key retains the exact v0.1.0 publication, including the absence of
target attributes. `_top` is the only accepted explicit target. The renderer
adds it only after the existing resolver has accepted an external typed-context
occurrence. URL eligibility, allowlists, source/native reconciliation and external
dependency evidence are unchanged. Local and generic-instance references never
receive this attribute. No navigation script, stylesheet, guide renderer, version
or dependency is changed. See [configuration](configuration.md) for regeneration
and trust-boundary details.

The strict `TYPE_LINK` grammar adds one noncapturing optional canonical literal;
its three existing capture groups remain URL, identity and original escaped
label. Highlighting protects the entire anchor, and plain-text reconstruction
remains exact. Other target values, duplicate attributes, unquoted/reordered or
executable attributes and nested markup are not accepted by that grammar.
Publication verification reconstructs the precise allowed location/presence of
every attribute from source and configuration. Rehashing output metadata does
not authorize a changed target or an attribute on a local link.

## Independent consumer evidence

Read-only input: [Imgproc PR #81](https://github.com/zackboll/opencv_imgproc_ada/pull/81),
head `a4d4a2edbc7cae49cf07a6d1e9f753f8d833d569`.
Its committed R1 proposal has SHA-256
`04aeb19845dd50890690ea6ec721f74443f305af5e949ea70195a31a462828f4`.
The proposal and its approval=false disposition are not changed or promoted.

The qualification script reuses the **unchanged consumer-owned legacy census**
and occurrence reconciliation, independently checks retained source/native
hashes, rederives all 14 referenced Core declarations and checks the reviewed
209-file artifact. Core is pinned to indexed 0.5.0,
`f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f`; its genuine native input is retained,
hash-verified GNATdoc 26 output, **not freshly regenerated in this task**.
The reviewed hosted artifact is `12238050173`, ZIP SHA-256
`fd328d27efc3196b5861d11c73561c2d22451e2a0fcf2b6477d7c6e0f853cc37`,
from Core commit `aa8a378ab614e9a5fc4f43765cd3ff1bbcf6a44d`.
Mutable GitHub Pages is not asserted to be an immutable versioned service.

All 586 external occurrences retain exact identity, decoded offsets, label,
source declaration and native anchor/profile. All 350 local links stay target-free,
including the original 348 plus the two source-proven constant type marks already
present in the PR's v0.1.0 candidate. The 329 native operation declarations are
unchanged. Two fresh opt-in enhancements agree and repeat enhancement is
byte-idempotent. Default bytes equal both an independent `origin/main` process
and the PR's retained v0.1.0 candidate. Opting in changes only the 586 canonical
attributes on one package page and its dependent manifest hash.

## Browser and distribution qualification

`tests/external_type_target_browser.cjs` serves only the independently generated
consumer candidates locally. Core is reached through **unintercepted live HTTPS**.
It covers all 14 types at 1280/390px, light/dark and JavaScript enabled/disabled:
direct exact-fragment entry, generated mouse and keyboard activation, top-document
identity (no remaining iframe), visible exact native declaration, byte equality
with the reviewed artifact, and Back/Forward return paths. A default-mode control
continues loading Core in the Imgproc iframe. Optional authentic Core favicon
404s are separately classified; other network/console failures fail the campaign.
Actual results, rather than this procedure alone, are in `docs/evidence/gnatdoc014/`.

The Python 3.11–3.13 campaign runs the complete retained suite plus the additive
GNATDOC-014 tests in source, clean installed wheel and extracted-sdist/rebuilt
wheel environments outside the checkout. It also runs four-profile conformance,
installed CLI/assets smoke checks, compilation, dependency checks, strict Twine
validation and the existing source/wheel/sdist/rebuilt archive auditor. Archives
remain version 0.1.0 qualification artifacts only; nothing is released.

## Reproduction

From `/home/zboll/git/ada-gnatdoc-enhancer`, with the retained read-only PR inputs:

```sh
PYTHONPATH=src python scripts/qualify_external_type_target.py \
  --consumer /home/zboll/git/opencv/imgproc-gnatdoc009 \
  --retained /home/zboll/git/opencv/imgproc-gnatdoc009-r1-work \
  --native /home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native \
  --baseline-src /home/zboll/qualification/gnatdoc014/baseline/src \
  --output /absolute/new-imgproc-qualification
PLAYWRIGHT_MODULE=/absolute/node_modules/playwright \
  GNATDOC014_WORKSPACE=/absolute/new-imgproc-qualification \
  GNATDOC014_REPORT=/absolute/new-browser-report.json \
  node tests/external_type_target_browser.cjs
python -m unittest discover -s tests -v
```

Full campaign harnesses, identities and limitations accompany the evidence.
No consumer files, Imgproc PR #81, deployment, release, tag or main branch are
modified. Stop at one non-draft enhancer PR for independent review. This support
does not approve Imgproc production migration or erase its other remaining gates.
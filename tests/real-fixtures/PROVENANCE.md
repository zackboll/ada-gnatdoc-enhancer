# Authentic native regression inputs

All upstream repositories are Zack Boll's Apache-2.0 repositories. Copyright
and license remain upstream's; this repository is also Apache-2.0.

`excerpts.json` contains literal, contiguous GNATdoc 26.0.0 (20260415) sections,
not recreated HTML, plus source signatures selected by the lexical inventory.
Each entry records its immutable Git revision, original native page path,
whole-page SHA-256, literal excerpt SHA-256 and source-file SHA-256.

`geometry/` contains the actual two native Geometry pages, native index and CSS,
the exact two public specifications and category manifest at
`fa81e5140cbebf2aa41397a40c08ba194a5f6f73`. Its `input.json` pins all bytes.
These API regression files total approximately 300 KB, not a published portal.
No production source is modified. This layer tests 130 native declarations,
171 conservative local type references, determinism/idempotence and tampering.

Acquisition: detached/exported snapshots, GNAT 16.1.0, GPRbuild Alire release
26.0.1, Alire 2.1.1, OpenCV 4.10.0, GNATdoc 26.0.0. Invoke `docs_api.gpr` with
`--backend html --generate public --style leading --warnings`; MEL uses
`--style trailing`. Capture before any consumer presentation script.
Full methodology and full-site results are in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/real-site-qualification.md`.

**Reduced regression success is not full-site qualification.** The excerpts
explicitly retain failing expression-function and abbreviated-enumeration
profiles; their tests do not claim the enhancer supports those profiles.

`generic-core/` contains ten complete source/native package pairs from Core
`c5545eee815431568495c6c76af83df56cf5c3dd`: five representative instances,
their two templates, the two actual-type owners and the conversion package.
`provenance.json` binds original paths and SHA-256 identities. Only the native
index lists are reduced to this selected package set; no declaration page or
Ada source is synthesized or shortened. `qualification.json` records those
reduced inputs and is explicitly not the full 25-instance qualification.
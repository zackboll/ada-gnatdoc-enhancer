# GNATDOC-034 authentic and mixed publishing controls

Core source identity:

* repository: `https://github.com/zackboll/opencv_core_ada`
* commit: `dbdb410c0d86b640271733d7b999ede5a5f92267`
* tree: `5bcbe86967fea4f718aab96a348fcaef5e8cfe8a`

`home.html` is the original `docs/index.html`, unchanged. `guide.md` combines
the complete original `docs/example.adb`, an original fragment from
`docs/ownership-and-views.md`, an unauthenticated prefixed overloaded expression,
ordinary prose, and shell/text fences. The fixture changes no original guide.

`production/` overlays only current inputs that differ from the historical
`tests/authored-fixtures/core` snapshot. `production/authored.json` is the exact
original pinned Core manifest (`source-text`, five guides, empty guide example
inventory). `tests/verified_support.py` reconstructs its inputs and the 195-package
public source/native inventory, sharing unchanged files rather than duplicating
the whole site. Its original input and native hashes are checked by publishing.

`production/mapping.json` was freshly generated with GNAT 16.1.0, GPRbuild
26.0.0 and Libadalang 26 from a `git archive` of the pinned Core, plus the retained
generated `config/*.gpr` files from the predecessor qualification. All original
Ada and GPR project source bytes are unchanged. The compiler ran once for
`docs/example.adb`; four static calls were accepted and the nonstatic end-name
reference at line 9 was explicitly skipped. The portable map binds all compiler
source/project inputs; no URL or alternate declaration is introduced.

Native evidence is the existing GNATdoc 26 artifact from Core run `41245425725`,
artifact `13059359370`, ZIP SHA-256
`2537dae628887231dfdd2a16159457bb5be4a25f7a840923458fc2a896870dbd`.
The updated Core package page is shared with `tests/verified-fixtures/core`;
the other 194 package pages and native index/CSS are unchanged historical inputs.

The two test fixture constructors update only the disposable publishing
configuration/pins to select mappings and highlighting. They neither alter the
Core checkout nor create human-review authorization. Compiler tooling is not
needed to consume these fixtures or run their installed-wheel tests.
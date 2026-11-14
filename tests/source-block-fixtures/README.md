# Exact MEL-GNATDOC-015-002 source/native fixture

Repository: https://github.com/zackboll/ams-gra-mel-bridge
Commit: `039bd4f05be969f0f224747728dfbae5305ee29b`
Tree: `44aa2c2ae4eba378b85694f34e07cfbaf20a33a6`
License: Apache-2.0 (same as this repository).

`mel/ada/src`, authored HTML/CSS and executable Ada inputs are exact Git-export
bytes. `docs/gnatdoc-native-anchors.json` is independently regenerated for this
source epoch, not the historical checked-in ledger. `native/api` is pristine
GNATdoc input; `reference` is independently reconstructed production output.
`provenance.json` binds input/native/reference bytes separately. The schema-3
manifest and pilot TOML are qualification-only derived inputs; they are not MEL
production configuration. No source program is executed by fixture tests.

Regenerate/verify with the explicitly trusted consumer tooling using
`scripts/qualify_source_blocks.py`, documented in `docs/source-backed-blocks.md`.
Do not replace the reference with enhancer output to make a mismatch pass.

`epoch` is an explicitly synthetic, isolated public-declaration regression.
GNAT 16.1.0/GPRbuild 26.0.0 compile-only checks and GNATdoc 26.0.0 independently
regenerated its native page. Original-source regeneration reproduced every
`mel/native` byte before the change. Its separate provenance binds the changed
Ada file and native page. It changes no MEL production source or runtime API.
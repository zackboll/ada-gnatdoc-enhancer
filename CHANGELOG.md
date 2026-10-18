# Changelog

## Unreleased — GNATDOC-010

- Source-verified document metadata: every generated API page gets `lang="en"`,
  an explicit head, a UTF-8 charset and a title from its verified package (or
  `API Reference`) and the project name; Markdown guides get their site-map
  label as title, which must equal the H1. Author pages must carry their own
  metadata. See `docs/html-page-metadata.md`.

## 0.1.0.dev0 — bootstrap

- Packaging, CLI, offline enhancement and verification, source inventories, presentation assets.
- Four sample project profiles and offline regression fixtures.
- No compatibility or distribution release claimed.

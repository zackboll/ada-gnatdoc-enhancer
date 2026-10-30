# Offline documentation search (GNATDOC-023)

## Opt-in contract

Existing consumers keep their package/operation link filter and native routing.
The label now accurately says **Filter navigation links**. Full search requires
an explicit, independently versioned configuration table:

```toml
[search]
schema_version = 1
mode = "documentation"
```

Navigation must be enabled. No consumer is automatically migrated. No backend,
network search service, CDN, external JavaScript library, or runtime Python is
needed on the published site. Serve the resulting static directory over HTTP(S)
(including GitHub Pages or localhost); `file:` URLs are not supported. HTTPS or
localhost is required for the browser's SHA-256 Web Crypto verification.

Full search adds `api/gnatdoc-search-index.json` and `api/gnatdoc-search.css` and
composes a single shared search asset into the existing published router file.
The three bundled legacy routers remain byte-identical. The index has its own
`schema_version: 1`; the existing presentation schema is unchanged. Verification
reconstructs its exact expected file inventory and all bytes from source/native
inputs and the approved configuration, including the rendered guide contract.
An output manifest or updated output checksum cannot authorize a forged index.

## Coverage and authorization

* Public packages come from the existing public Ada inventory and native index.
* Types, subtypes, functions, and procedures use `source_destinations`: complete
  signature reconciliation, observed filenames/anchors, and source-order
  overload ordinals. No declaration destination is inferred from a name/hash.
* A further conservative public-prefix/scope check excludes private-part
  declarations, `Internal` package components, and unsupported nested scopes.
  Public partial private views such as `OpenCV.Core.Mat` are public symbols.
* Signatures and associated source text are searchable. Guide titles, headings,
  and visible text come only from approved guides actually rendered by the
  existing publishing pipeline; navigation, metadata, scripts and styles are
  excluded. No arbitrary HTML link is harvested as search authority.
* Instantiated generic members without native declaration anchors are not
  invented. Generic packages remain searchable, and genuine public template
  declarations are indexed. Constants, quoted operators, nested declarations,
  arbitrary repository files and external dependency APIs are not added.

The shell contains a separately generated destination allowlist and the index's
SHA-256. The browser verifies that digest, schema, exact record count, unique
destinations, and record-to-allowlist identities before exposing any result.
Corrupt, missing, duplicated or forged index bytes fail closed with an explicit
unavailable message and leave native navigation usable. This protects the cache
boundary, not an attacker who controls the entire published shell/JavaScript.

API results resolve to approved states in the existing router. Existing
authorized symbols use their existing symbol-bookmark contract; all other
declarations use package/declaration routing with verified native anchors.
Opening a result invokes the same router activation and scrolling logic, not a
new iframe navigation mechanism. Canonical shell hrefs support fresh tabs,
reload and history. Guide results are same-site, approved top-level pages and
never iframe destinations. Input alone changes neither URL nor package.

## Interaction and bounds

Search is case-insensitive and matches unqualified, qualified and partial names,
signatures and guide text. Whitespace-separated terms are combined with AND.
Exact names rank first, then partial names, then descriptive matches; ties use
deterministic source/index order. Results show package/symbol/operation/guide
kinds, qualified names, overload numbers and signature/text excerpts.

Empty input restores a help status, not a replacement package selection. Clear
returns focus to the input; Escape clears it. Down/Enter moves from input to
results; Up/Down/Home/End move among result links, Enter opens, Escape returns
focus to input, and ordinary Tab navigation works throughout. Search text is
never inserted through `innerHTML` or interpreted as a regex, HTML, or URL.

Version 1 admits at most 20,000 records, an 8 MiB UTF-8 index, 64,000 characters
per record, 256 query characters, and renders at most 50 results. It reports the
full match count and asks users to refine larger matches. Oversized guide input
fails at build time rather than silently dropping searchable guide content.
The scoped stylesheet works alongside both bundled and source-approved custom
themes, without changing the homepage, API layout or native navigation.

## Reproducible qualification

The original released-wheel failure is retained in
`/home/zboll/git/ada-gnatdoc-enhancer/docs/evidence/gnatdoc023/original-failing-reproduction.json`
and before screenshots. The actual pinned Core fixture is under
`/home/zboll/git/ada-gnatdoc-enhancer/tests/real-fixtures/search-core`.

```sh
python -m unittest discover -s tests -v
python scripts/check_search_browser.py --workspace /tmp/search-sites --output /tmp/search-evidence
```

The Chromium harness builds all three router variants from actual Core inputs
with the existing Core custom theme. It checks required queries, distinct
overload destinations, canonical links/history/reload/fresh tabs, keyboard
navigation, rapid/malicious input, corrupt/missing index caches, no horizontal
overflow at 1280/390 pixels, both themes, no external requests, and native
JavaScript-disabled access. Playwright is a separately installed test tool, not
a runtime package dependency. Hosted CI runs this dedicated job as well as all
predecessor tests and archive checks.
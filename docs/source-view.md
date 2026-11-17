# Optional offline specification browser

Source browsing is **disabled by default**. Existing configurations produce
exactly the same publication bytes. It requires no JavaScript, runtime Python,
network service, GitHub source URL, font download or CDN.

## Visibility and scope

Enabling this feature deliberately publishes the **entire original `.ads`
file**, including comments and any **private section inside a public package
specification**. It does not redact that section or claim the text is public-only.
Review specifications for confidential material before enabling it.

Only public library package specifications independently discovered in the
configured source directories are eligible. Private library units, `.adb`
implementation bodies, arbitrary repository files and unselected dependencies
are not source views. The existing conservative Ada inventory and exact native
profile reconciliation authorize type, subtype, function and procedure links,
plus existing supported constant identities. Unsupported declarations receive
no guessed link. Package headings have package-level links. Overloads retain
their distinct native anchors and actual declaration-token source lines.

## Configuration and reviewed input evidence

The versioned contract is strict; all four fields are required:

```toml
[source_view]
schema_version = 1
mode = "public-specifications"
native_manifest = "docs/source-native.json"
native_manifest_sha256 = "<SHA-256 of the reviewed input evidence>"
```

`native_manifest` is a project-relative, source-owned input, **not**
`api/presentation.json`. Its schema-1 JSON has `files` (complete pristine native
API HTML/CSS SHA-256 inventory) and `sources` (complete eligible specification
SHA-256 inventory). Paths and hashes are exact, case-sensitive identities.
Pinning both inputs prevents a resealed output manifest from authorizing
substituted source, wrong native anchors or swapped overload destinations.

Before adding the opt-in table, acquire pristine GNATdoc **26.0.0** output and
record its identity with the shipped source-distribution utility:

```sh
python /absolute/enhancer/scripts/pin_source_view.py \
  --source-root /absolute/project --config docs/gnatdoc-enhance.toml \
  --site /absolute/pristine-site \
  --output /absolute/project/docs/source-native.json
```

Independently review the input acquisition and evidence; commit the JSON and its
printed hash in configuration. Do not generate authorization from an enhanced
publication. Regenerate/review the pin after changing source or native input.
Then use the normal enhance/verify commands with the opt-in configuration.
No original Ada file or pristine acquisition is edited. As with existing
enhancement, the publication copy of native HTML receives bounded insertions.

## Layout and navigation

For `ada/src/ams-mel-ir-image.ads`, the static page is
`api/source/ada/src/ams-mel-ir-image.ads.html`. Native declaration headings gain
a small **View source** link. `AMS.MEL.IR.Image.Navigation_Report`, for example,
opens that file at `#L663`; `Submit_Navigation_Report` opens at `#L775` in the
retained MEL qualification input. These are qualification examples, not fixed
counts or promised locations for future revisions.

Links leave the native iframe for a directly addressable static source page;
browser Back returns to the API. Every physical line has a stable `#L1`, `#L2`,
etc. Keyboard-focusable line links expose their line number accessibly. Displayed
numbers are CSS-generated, not source text, and do not contaminate copied code.
The layout supports narrow screens and system light/dark color preferences.

The complete UTF-8 source, indentation, tabs, LF or CRLF and missing final newline
are preserved in the code element's DOM text and independently tested. HTML
character references preserve CR without HTML newline normalization. Browser
clipboard/OS newline conversion is outside this byte-identity guarantee. Invalid
UTF-8, NUL, bare CR, unsafe path characters and symlinked input trees fail closed.
Source is escaped rather than highlighted: preserving original bytes takes
precedence over introducing another Ada parser or lossy token normalization.

## Verification and compatibility

The publication manifest records ownership, source hashes, line counts and
declaration/anchor/line correspondence. Verification reconstructs all pages and
links from source and pinned native evidence, then compares exact output bytes
and the complete inventory. Output-side digests do not authorize themselves.
Only the exact reconstructed source markup is admitted; no blanket HTML,
`data-*`, scripting or URL permission is introduced. Malicious comments remain
inert source text. Existing native anchors, search, navigation, bookmarks,
guides, examples and theme assets are unchanged by this opt-in.

The qualification utility records complete disabled/enabled publication hashes
and the compatibility delta for retained official GNATdoc MEL/Core fixtures,
without freezing source-page counts in the product contract. A dedicated hosted
Chromium job covers both configurations and the mandatory Navigation Report
journey. Retained fixtures do not represent a new GNATdoc/compiler execution.

Implementation body browsing, spec-to-body mapping and arbitrary repository
file browsing are explicitly deferred (GNATDOC-SOURCE-002).
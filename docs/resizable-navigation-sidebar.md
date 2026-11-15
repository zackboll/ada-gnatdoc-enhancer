# Opt-in resizable navigation sidebar (GNATDOC-038)

Enable this shared shell presentation feature explicitly:

```toml
[navigation]
mode = "packages" # operations and none also supported
resizable_sidebar = true
```

The option is a strict Boolean, defaults to `false`, and requires
`presentation.theme = true` (the default). It works with the bundled theme and
source/hash-approved custom themes using the GNATdoc `.side-navigation` and
`.document-content` shell. No Ada declarations, consumer runtime libraries or
navigation routers need changing.

## Interaction and accessibility

On desktop, drag the visible 8px divider. Pointer capture and a temporary shield
keep the gesture working over the documentation iframe. Pointer-up commits the
width; cancellation, lost capture, blur, page exit or window resize cancel the
gesture and remove capture/shield state. No iframe DOM or router state is read.

The divider is a focusable vertical separator labelled **Navigation width**.
Left/Right change the width by 16px; Home/End select the current minimum/maximum.
`aria-valuemin`, `aria-valuemax`, `aria-valuenow` and pixel-valued
`aria-valuetext` track the visible width. Double-click resets to the theme's
default width and removes the preference.

Navigation is at least 240px wide and content at least 320px wide. The maximum
is recalculated from the viewport minus content and divider space. A desktop
preference constrained by a narrower viewport is retained for a later wider
viewport. At the theme's existing mobile breakpoint, the divider is hidden and
unfocusable and the theme's original stacked layout is restored (bundled:
810px; qualified Core custom theme: 800px). A custom theme must retain a
side-by-side desktop shell and stacked mobile shell; the implementation detects
the actual unmodified theme layout rather than overriding its breakpoint.

Widths are stored at `gnatdoc:sidebar-width:v1:<API-directory-path>` in
`localStorage`. Storage is already origin-isolated; path scoping also separates
GitHub Pages projects and documentation versions on a shared origin. Query,
fragment and declaration/history changes do not change the key. Only finite
positive decimal widths are accepted, then rounded and clamped to current bounds.
Malformed values are ignored. Blocked/unavailable storage affects persistence
only, never dragging, keyboard controls or reset.

Without JavaScript the divider stays hidden, original layout remains active,
and native GNATdoc links still target the documentation iframe.

## Publication and qualification

No existing asset is edited. Enabled publication adds exactly
`api/gnatdoc-resize.css` and `api/gnatdoc-resize.js`, and changes only
`api/index.html` and `api/presentation.json`. The latter records hashes in its
existing exact output inventory. Both assets and HTML are reconstructed from
the project configuration during independent `verify`; generated hashes cannot
authorize altered assets. Disabled publication remains byte-identical to
upstream, including the manifest, and cannot authorize resize assets or script
references. No router is copied, forked or extended by this feature.

Run the focused publication/mutation tests and real browser qualification:

```sh
python -m unittest discover -s tests -p test_resizable_sidebar.py -v
python scripts/check_resize_browser.py --workspace /tmp/resize-qualification
```

The browser script uses the existing pinned actual Core GNATdoc fixture and
approved custom theme with package, symbol and instance routers, plus bundled
theme, synthetic operation and native-only modes. It checks actual pointer
gestures over the iframe, persistence, reset, keyboard/ARIA, cancellation/cleanup,
path isolation, malformed storage, denied storage, bounds, exact mobile
breakpoints, light/dark, native declarations, search, bookmarks, history and
JavaScript-disabled fallback. It also reconstructs each publication twice,
verifies complete output and records hashes, checks, errors and screenshots.
`--baseline-source /absolute/path/to/upstream-checkout` additionally generates
each disabled variant with upstream and compares every published byte.

This qualifies shared presentation against these fixtures, not a new release or
complete certification of all consumer documentation sites.
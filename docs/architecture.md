# Architecture

```text
Consumer Ada specifications        GNATdoc 26.0.0 generated raw HTML
             |                                   |
             v                                   v
    Source inventory -----------> Native page/profile inventory
             |                                   |
             +-------> Verified type targets <---+
                                                   |
  Project TOML -> allowed features -> theme/links/highlight/navigation
                                                   |
    Strict HTML or Markdown guides -----------------+
                                                   v
                Deterministic enhanced static site
                                                   |
                              Reconstructed independent verifier
```

The CLI does not run GNATdoc or Alire, and it cannot synthesize a declaration
hash from an Ada name. Its type resolver requires a single source-owned native
anchor and returns no link when it cannot establish Ada visibility. Layout CSS
and the optional browser script are local package assets. HTML enhancements
carry a raw-output presentation manifest, which is independently recomputed at
verification, preserving source text and native anchors.

The shipped static browser is progressive enhancement; ordinary GNATdoc
package links survive with JavaScript disabled. The validator independently
checks local links, fragments, asset bytes, exact output file inventories and
all source package identities.

The manifest is stored in the generated site for repeatable verification, but
should not be construed as a cryptographic signature. A changed branch can
change validator code: preserve repository review, pinned releases and existing
source-integrity rules.

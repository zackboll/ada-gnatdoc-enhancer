# Retained GNATDOC-033 compiler controls

`core` retains byte-identical public `opencv.ads` / `opencv-core.ads`, the authentic
`docs/example.adb` and project/dependency inputs from Core commit
`dbdb410c0d86b640271733d7b999ede5a5f92267`, tree
`5bcbe86967fea4f718aab96a348fcaef5e8cfe8a`. Native package pages/CSS are unchanged
excerpts of the GNATDOC-032 authenticated GNATdoc artifact (see
`research/gnatdoc032/environment.json` and `research/gnatdoc031/provenance.py`).
The native index is reduced only to the two retained public packages. No anchor
or declaration profile is invented. Publishing-only guide/home/CSS/manifest files
exercise the existing authored renderer; they are not compiler semantic context.

`overloads` derives from the original GNATDOC-031/032 fixtures. The unsupported
generic/renaming declarations and their calls are omitted with blank call lines
preserving the positive occurrence coordinates. `valid.adb` gains a final LF.
`public` is a byte-identical export of the compiled public specs. Native package
pages were freshly generated with GNATdoc 26 using leading comments; only the
index was reduced to the retained packages. Original unsupported controls remain
unchanged in research/gnatdoc032 and are run separately.

Both mappings were freshly generated with GNAT 16.1.0 / GPRbuild 26 and Libadalang
26, not constructed from names or expected anchors. Tests check independently
fixed declaration positions and wrong-overload injections. The full runtime
consumer needs none of those compiler tools. `mapping.json` contains no absolute
paths or URL authority. These fixtures are test evidence, not independent review
approval, released documentation, or evidence of general Ada coverage.
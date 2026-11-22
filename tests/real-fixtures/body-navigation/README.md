# Authentic specification/body qualification inputs

`provenance.json` records the upstream commits, trees and SHA-256 of all retained
files. The underlying specification/native baselines remain `search-mel` and
`search-core`. The input bytes in this directory are complete, unmodified files.

* `mel`: bodies from the same MEL Bridge Git revision as `search-mel`. Each
  corresponding `.ads` was independently compared with its Git blob.
* `core`: the complete `OpenCV.Core` body from the revision whose `src/opencv-core.ads`
  exactly matches the `search-core` specification. Only this Core body is included
  in the disposable authority; this is not a complete Core body acquisition.
* `commands`: a byte delta from `search-mel` to the retained MEL Bridge hosted
  GNATdoc 26 acquisition (run `44437859821`), with Ada bytes taken from that
  acquisition's source commit. Replaced and additional native files match its
  hosted payload hashes. It supplies `AMS.MEL.IR.Scheduling.Commands` while
  preserving the earlier fixture for compatibility. This is not a fresh
  consumer build or publication.

The upstream Apache-2.0 terms and attribution are unchanged. Qualification
uses disposable copies. No consumer repository or configuration is edited.
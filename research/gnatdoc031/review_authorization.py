#!/usr/bin/env python3
"""Explicit LOCAL review record; not acquisition and not an attestation.

Run only after independent human review. The consumer must separately trust
the named reviewer. This program cannot establish who actually operated it.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from provenance import digest, input_binding, require, verified_inputs


def record_review(qualification, source_root, native, output, reviewer, reason):
    require(bool(reviewer.strip()) and bool(reason.strip()), "reviewer and reason required")
    q = verified_inputs(qualification, source_root, native)
    record = {"schema": 1, "decision": "APPROVE_EXACT_INPUTS", "reviewer": reviewer,
              "reason": reason, "reviewed_at": datetime.now(timezone.utc).isoformat(),
              "qualification_sha256": digest(qualification), "inputs_sha256": input_binding(q),
              "trust_limitation": "Editable local record, NOT a cryptographic independent-review attestation."}
    with Path(output).open("x") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("qualification", "source-root", "native-site", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--approve-exact-inputs", required=True, action="store_true")
    args = parser.parse_args()
    record_review(args.qualification, args.source_root, args.native_site, args.output, args.reviewer, args.reason)


if __name__ == "__main__":
    main()
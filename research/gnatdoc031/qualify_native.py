#!/usr/bin/env python3
"""Qualify the pinned authenticated pristine artifact without publishing it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

from probe import inventory

COMMIT = "dbdb410c0d86b640271733d7b999ede5a5f92267"
ARTIFACT = 13059359370
RUN = 41245425725
SHA256 = "2537dae628887231dfdd2a16159457bb5be4a25f7a840923458fc2a896870dbd"


def api(endpoint):
    return subprocess.check_output(["gh", "api", "repos/zackboll/opencv_core_ada/" + endpoint])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-checkout", required=True, type=Path)
    parser.add_argument("--zip", required=True, type=Path,
                        help="retained ZIP, or new file to download via authenticated GitHub")
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=False)
    artifact = json.loads(api(f"actions/artifacts/{ARTIFACT}"))
    run = json.loads(api(f"actions/runs/{RUN}"))
    assert artifact["id"] == ARTIFACT and artifact["workflow_run"]["id"] == RUN
    assert run["id"] == RUN and run["head_sha"] == artifact["workflow_run"]["head_sha"] == COMMIT
    assert run["conclusion"] == "success" and artifact["digest"] == "sha256:" + SHA256
    assert artifact["name"] == "gnatdoc-diagnostics-" + COMMIT
    assert subprocess.check_output(["git", "-C", str(args.core_checkout), "rev-parse", "HEAD"], text=True).strip() == COMMIT
    # Tracked source may not differ from the authenticated commit. Generated
    # config/build files in a separate export are not source evidence.
    assert not subprocess.check_output(["git", "-C", str(args.core_checkout), "status", "--porcelain"], text=True)
    if not args.zip.exists():
        args.zip.write_bytes(api(f"actions/artifacts/{ARTIFACT}/zip"))
    assert hashlib.sha256(args.zip.read_bytes()).hexdigest() == SHA256
    native = output / "native"
    with zipfile.ZipFile(args.zip) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        identities = archive.read("obj/docs/git-identities.txt").decode().splitlines()
        assert identities[0] == COMMIT
        assert identities[1] == subprocess.check_output(
            ["git", "-C", str(args.core_checkout), "rev-parse", "HEAD^{tree}"], text=True).strip()
        for name in archive.namelist():
            if not name.startswith("obj/docs/native/") or name.endswith("/"):
                continue
            rel = PurePosixPath(name.removeprefix("obj/docs/native/"))
            assert not rel.is_absolute() and ".." not in rel.parts
            target = native / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    provenance = {"repository": "https://github.com/zackboll/opencv_core_ada",
                  "commit": COMMIT, "run_id": RUN, "artifact_id": ARTIFACT,
                  "artifact_sha256": SHA256, "zip_prefix": "obj/docs/native/",
                  "authentication": "fresh gh api metadata; ZIP digest verified against GitHub",
                  "gnatdoc": "26.0.0 (20260415)"}
    qualification = {"schema": 1, "reviewed": True, "provenance": provenance,
                     "sources": inventory(args.core_checkout, ["src/**/*.ads", "src/**/*.adb"]),
                     "native": inventory(native, ["api/*"])}
    (output / "qualification.json").write_text(json.dumps(qualification, indent=2) + "\n")
    (output / "artifact.json").write_text(json.dumps(artifact, indent=2) + "\n")
    (output / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    print(output / "qualification.json")


if __name__ == "__main__":
    main()
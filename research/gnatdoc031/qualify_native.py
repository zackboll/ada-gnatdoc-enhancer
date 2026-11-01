#!/usr/bin/env python3
"""Acquire and verify pinned authenticated evidence; NEVER grant review."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import shutil
import stat
import zipfile

from provenance import (API_ROOT, ARTIFACT, COMMIT, NATIVE_PATTERNS, REPOSITORY,
                        RUN, SHA256, SOURCE_PATTERNS, TREE, inventory,
                        require, validate_metadata)


def api(endpoint):
    return subprocess.check_output(["gh", "api", API_ROOT + "/" + endpoint])


def git(checkout, *args):
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


def archive_members(archive):
    """Preflight EVERY member, including unextracted files, before any write."""
    seen = {}
    for member in archive.infolist():
        name = member.orig_filename
        require(name == member.filename and "\x00" not in name and "\\" not in name,
                "unsafe archive member path")
        path = PurePosixPath(name)
        parts = name.removesuffix("/").split("/")
        require(bool(name) and not path.is_absolute() and
                all(p not in ("", ".", "..") and ":" not in p for p in parts),
                "unsafe archive member path")
        kind = stat.S_IFMT(member.external_attr >> 16)
        require(kind in (0, stat.S_IFREG, stat.S_IFDIR) and
                (kind != stat.S_IFDIR or member.is_dir()) and
                (kind != stat.S_IFREG or not member.is_dir()) and not (member.flag_bits & 1),
                "unsafe archive member type")
        normalized = path.as_posix().casefold()
        require(normalized not in seen, "duplicate or conflicting normalized archive destination")
        seen[normalized] = member.is_dir()
    for name in seen:
        for parent in PurePosixPath(name).parents:
            require(seen.get(parent.as_posix(), True), "conflicting archive file/directory destinations")
    require(archive.testzip() is None, "ZIP integrity failure")
    return archive.infolist()


def private_destination(output):
    output = Path(output)
    require(output.is_absolute() and ".." not in output.parts, "unsafe extraction destination")
    require(not output.exists() and not output.is_symlink(), "extraction destination already exists")
    for parent in output.parents:
        require(not parent.is_symlink(), "symlink in extraction destination")
    require(output.parent.is_dir(), "private extraction parent must already exist")
    return output


def acquire(checkout, zip_path, output):
    """Only api() supplies metadata; offline fixtures replace that boundary."""
    output = private_destination(output)
    artifact = json.loads(api(f"actions/artifacts/{ARTIFACT}"))
    run = json.loads(api(f"actions/runs/{RUN}"))
    validate_metadata(artifact, run)
    require(git(checkout, "rev-parse", "HEAD") == COMMIT, "checkout commit identity mismatch")
    require(git(checkout, "rev-parse", "HEAD^{tree}") == TREE, "checkout tree identity mismatch")
    require(not git(checkout, "status", "--porcelain", "--untracked-files=all", "--ignored"),
            "checkout is not clean (including ignored evidence)")
    # New downloads stay in memory; no failed acquisition writes a retained ZIP
    # or any other file outside the designated private extraction root.
    data = Path(zip_path).read_bytes() if Path(zip_path).exists() else api(f"actions/artifacts/{ARTIFACT}/zip")
    require(hashlib.sha256(data).hexdigest() == SHA256, "artifact ZIP digest mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive_members(archive)
        identities = archive.read("obj/docs/git-identities.txt").decode().splitlines()
        require(len(identities) >= 2 and identities[:2] == [COMMIT, TREE], "archive Git commit/tree mismatch")
        native_members = [m for m in members if m.filename.startswith("obj/docs/native/") and not m.is_dir()]
        require(bool(native_members), "missing native evidence")
        sources = inventory(checkout, SOURCE_PATTERNS)
        require(bool(sources), "empty source inventory")
        # Parent must be operator-controlled: concurrent hostile filesystem
        # mutation is outside this local research tool's trust model.
        output.mkdir(mode=0o700)
        try:
            native = output / "native"
            for member in native_members:
                target = native / member.filename.removeprefix("obj/docs/native/")
                require(target.resolve().is_relative_to(native.resolve()), "native extraction escapes root")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(archive.read(member))
            (output / "artifact.zip").write_bytes(data)
            provenance = {"repository": "https://github.com/" + REPOSITORY,
                          "commit": COMMIT, "tree": TREE, "run_id": RUN, "artifact_id": ARTIFACT,
                          "artifact_sha256": SHA256, "zip_prefix": "obj/docs/native/",
                          "authentication": "fresh gh api metadata; ZIP digest verified against GitHub",
                          "gnatdoc": "26.0.0 (20260415)"}
            qualification = {"schema": 2, "state": "VERIFIED", "acquired": True, "verified": True,
                             "provenance": provenance,
                             "authenticated_metadata": {"artifact": artifact, "run": run},
                             "sources": sources, "native": inventory(native, NATIVE_PATTERNS)}
            # Last write; failures remove the entire tree owned by this call.
            (output / "qualification.json").write_text(json.dumps(qualification, indent=2) + "\n")
        except BaseException:
            shutil.rmtree(output)
            raise
    return output / "qualification.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-checkout", required=True, type=Path)
    parser.add_argument("--zip", required=True, type=Path,
                        help="retained ZIP, or new file to download via authenticated GitHub")
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args()
    print(acquire(args.core_checkout, args.zip, args.output_directory))


if __name__ == "__main__":
    main()
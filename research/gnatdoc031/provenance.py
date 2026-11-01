"""Research trust boundaries, active under -O; local records are not attestations."""
import hashlib
import json
from pathlib import Path

COMMIT = "dbdb410c0d86b640271733d7b999ede5a5f92267"
TREE = "5bcbe86967fea4f718aab96a348fcaef5e8cfe8a"
ARTIFACT = 13059359370
RUN = 41245425725
SHA256 = "2537dae628887231dfdd2a16159457bb5be4a25f7a840923458fc2a896870dbd"
REPOSITORY = "zackboll/opencv_core_ada"
REPOSITORY_ID = 1328215387
API_ROOT = "https://api.github.com/repos/" + REPOSITORY
NATIVE_PATTERNS = ["**/*"]
SOURCE_PATTERNS = ["src/**/*.ads", "src/**/*.adb"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root, patterns):
    """Hash ordinary files only; reject symlinks in each inventoried subtree."""
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "unsafe inventory root")
    for pattern in patterns:
        prefix = pattern.split("*")[0].rsplit("/", 1)[0]
        subtree = root / prefix
        for entry in [subtree, *subtree.rglob("*")]:
            require(not entry.is_symlink(), "symlink in inventory")
            require(entry.is_dir() or entry.is_file(), "unsafe inventory member")
    return {p.relative_to(root).as_posix(): digest(p)
            for pattern in patterns for p in sorted(root.glob(pattern)) if p.is_file()}


def validate_metadata(artifact, run):
    """Metadata must originate ONLY at the authenticated gh API boundary."""
    try:
        require(artifact["id"] == ARTIFACT and artifact["workflow_run"]["id"] == RUN,
                "artifact/workflow-run identity mismatch")
        require(run["id"] == RUN and
                run["head_sha"] == artifact["workflow_run"]["head_sha"] == COMMIT,
                "Git commit identity mismatch")
        require(run["status"] == "completed" and run["conclusion"] == "success",
                "workflow did not complete successfully")
        require(run["event"] == "push" and run["head_branch"] == "main" and
                run["path"] == ".github/workflows/documentation.yml", "unexpected workflow execution")
        require(run["repository"]["full_name"] == run["head_repository"]["full_name"] == REPOSITORY
                and run["repository"]["id"] == run["head_repository"]["id"] == REPOSITORY_ID
                and artifact["workflow_run"]["repository_id"] == REPOSITORY_ID
                and artifact["workflow_run"]["head_repository_id"] == REPOSITORY_ID,
                "repository identity mismatch")
        require(artifact["name"] == "gnatdoc-diagnostics-" + COMMIT, "artifact name mismatch")
        require(artifact["digest"] == "sha256:" + SHA256, "artifact digest mismatch")
        require(artifact["url"] == API_ROOT + f"/actions/artifacts/{ARTIFACT}" and
                artifact["archive_download_url"] == API_ROOT + f"/actions/artifacts/{ARTIFACT}/zip"
                and run["url"] == API_ROOT + f"/actions/runs/{RUN}",
                "authenticated endpoint identity mismatch")
    except (KeyError, TypeError) as exc:
        raise ValueError("missing or inconsistent authenticated metadata") from exc


def verified_inputs(qualification, source_root, native):
    q = json.loads(Path(qualification).read_text())
    require(q.get("schema") == 2 and q.get("state") == "VERIFIED" and
            q.get("acquired") is True and q.get("verified") is True and
            "reviewed" not in q, "native acquisition is not explicitly verified")
    try:
        validate_metadata(q["authenticated_metadata"]["artifact"], q["authenticated_metadata"]["run"])
        require(q["provenance"]["commit"] == COMMIT and q["provenance"]["tree"] == TREE
                and q["provenance"]["artifact_sha256"] == SHA256
                and q["provenance"]["repository"] == "https://github.com/" + REPOSITORY
                and q["provenance"]["run_id"] == RUN and q["provenance"]["artifact_id"] == ARTIFACT
                and q["provenance"]["zip_prefix"] == "obj/docs/native/", "qualification provenance mismatch")
        require(inventory(source_root, SOURCE_PATTERNS) == q["sources"], "source/native snapshot mismatch")
        require(inventory(native, NATIVE_PATTERNS) == q["native"], "native inventory mismatch")
        require(bool(q["sources"]) and bool(q["native"]), "empty evidence inventory")
    except (KeyError, TypeError) as exc:
        raise ValueError("incomplete verified qualification") from exc
    return q


def input_binding(q):
    inputs = {k: q[k] for k in ("provenance", "authenticated_metadata", "sources", "native")}
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_review(qualification, q, authorization, authorized_reviewers):
    require(authorization is not None, "missing explicit review authorization")
    approval = json.loads(Path(authorization).read_text())
    require(approval.get("schema") == 1 and approval.get("decision") == "APPROVE_EXACT_INPUTS",
            "invalid review authorization")
    require(approval.get("reviewer") in authorized_reviewers and bool(approval.get("reviewer")),
            "unauthorised reviewer (operator trust policy required)")
    require(bool(approval.get("reason")) and bool(approval.get("reviewed_at")), "incomplete review authorization")
    require(approval.get("qualification_sha256") == digest(qualification) and
            approval.get("inputs_sha256") == input_binding(q), "stale or mismatched review authorization")
    return approval
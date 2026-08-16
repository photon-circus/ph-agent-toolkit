"""Bounded local Git observation helpers."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path


class GitError(ValueError):
    """Raised when the requested local Git comparison cannot be established."""


def run_git(root: Path, arguments: list[str], *, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(arguments)} failed")
    return result.stdout.decode("utf-8") if text else result.stdout


def repository_root(path: str | Path) -> Path:
    candidate = Path(path).resolve()
    root = run_git(candidate, ["rev-parse", "--show-toplevel"], text=True).strip()
    return Path(root).resolve()


def resolve_commit(root: Path, revision: str) -> str:
    return run_git(root, ["rev-parse", "--verify", f"{revision}^{{commit}}"], text=True).strip()


def has_conflicts(root: Path) -> bool:
    return bool(run_git(root, ["diff", "--name-only", "--diff-filter=U", "-z"]))


def sha256(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def read_revision_file(
    root: Path,
    revision: str,
    path: str,
    max_bytes: int | None = None,
) -> bytes | None:
    object_name = f"{revision}:{path}"
    size_result = subprocess.run(
        ["git", "cat-file", "-s", object_name],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if size_result.returncode:
        return None
    try:
        size = int(size_result.stdout)
    except ValueError as error:
        raise GitError(f"git returned an invalid object size for {path}") from error
    if max_bytes is not None and size > max_bytes:
        raise GitError(f"file exceeds max_file_bytes ({max_bytes}): {path}")
    result = subprocess.run(
        ["git", "show", object_name],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def list_untracked_paths(root: Path) -> list[str]:
    raw = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def read_worktree_file(root: Path, path: str, max_bytes: int) -> bytes | None:
    target = (root / Path(path)).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise GitError(f"path escapes repository root: {path}") from error
    if not target.is_file():
        return None
    size = target.stat().st_size
    if size > max_bytes:
        raise GitError(f"file exceeds max_file_bytes ({max_bytes}): {path}")
    return target.read_bytes()


def list_target_paths(root: Path, revision: str | None) -> list[str]:
    if revision is not None:
        raw = run_git(root, ["ls-tree", "-r", "--name-only", "-z", revision])
    else:
        tracked = run_git(root, ["ls-files", "-z"])
        untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
        raw = tracked + untracked
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def _name_status(root: Path, base: str, target: str | None) -> list[tuple[str, str | None, str]]:
    args = [
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "--find-renames=50%",
        "--name-status",
        "-z",
        base,
    ]
    if target is not None:
        args.append(target)
    raw = run_git(root, args)
    fields = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    output: list[tuple[str, str | None, str]] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            old_path, path = fields[index], fields[index + 1]
            index += 2
            output.append((status[0], old_path, path))
        else:
            path = fields[index]
            index += 1
            output.append((status[0], None, path))
    return output


def collect_changes(
    root: Path,
    base: str,
    target: str | None,
    *,
    max_files: int,
    max_diff_bytes: int,
    max_file_bytes: int,
    excluded_paths: set[str],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    statuses = _name_status(root, base, target)
    if target is None:
        known = {path for _, _, path in statuses}
        for path in list_untracked_paths(root):
            if path not in known:
                statuses.append(("A", None, path))
    statuses = [item for item in statuses if item[2] not in excluded_paths]
    if len(statuses) > max_files:
        raise GitError(f"comparison exceeds max_files ({max_files})")

    changes: list[dict[str, object]] = []
    consumed: dict[str, str] = {}
    total_diff = 0
    for status, old_path, path in sorted(statuses, key=lambda item: item[2]):
        old_bytes = read_revision_file(root, base, old_path or path, max_file_bytes)
        new_bytes = (
            read_revision_file(root, target, path, max_file_bytes)
            if target is not None
            else read_worktree_file(root, path, max_file_bytes)
        )
        if old_bytes is not None and len(old_bytes) > max_file_bytes:
            raise GitError(f"file exceeds max_file_bytes ({max_file_bytes}): {old_path or path}")
        if new_bytes is not None and len(new_bytes) > max_file_bytes:
            raise GitError(f"file exceeds max_file_bytes ({max_file_bytes}): {path}")
        if target is None:
            consumed[path] = sha256(new_bytes) if new_bytes is not None else "<missing>"
        binary = (old_bytes is not None and b"\0" in old_bytes) or (
            new_bytes is not None and b"\0" in new_bytes
        )
        if binary:
            patch = ""
        elif old_bytes is None:
            patch = (new_bytes or b"").decode("utf-8", errors="replace")
        else:
            args = [
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--no-color",
                "--diff-algorithm=myers",
                "--src-prefix=a/",
                "--dst-prefix=b/",
                "--no-relative",
                "--unified=3",
                base,
            ]
            if target is not None:
                args.append(target)
            args.extend(["--", old_path or path, path])
            patch = run_git(root, args, text=True)
        encoded_patch = patch.encode("utf-8")
        remaining = max_diff_bytes - total_diff
        truncated = len(encoded_patch) > remaining
        if remaining <= 0:
            patch = ""
            truncated = bool(encoded_patch)
        elif truncated:
            patch = encoded_patch[:remaining].decode("utf-8", errors="ignore")
        total_diff += min(len(encoded_patch), max(remaining, 0))
        changes.append(
            {
                "path": path,
                "old_path": old_path,
                "status": status,
                "old_sha256": sha256(old_bytes),
                "new_sha256": sha256(new_bytes),
                "binary": binary,
                "patch": patch,
                "patch_truncated": truncated,
            }
        )
    return changes, consumed


def worktree_identity(consumed: dict[str, str]) -> str:
    preimage = "".join(f"{path}\0{digest}\n" for path, digest in sorted(consumed.items()))
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def relative_output(root: Path, output: str) -> str | None:
    if output == "-":
        return None
    resolved = Path(output).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return None


def check_worktree_unchanged(root: Path, consumed: dict[str, str], max_file_bytes: int) -> None:
    for path, expected in consumed.items():
        current = read_worktree_file(root, path, max_file_bytes)
        actual = sha256(current) if current is not None else "<missing>"
        if actual != expected:
            raise GitError(f"repository changed during inspection: {path}")


def atomic_write(path: str | Path, data: bytes) -> None:
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()

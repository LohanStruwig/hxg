from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

PRIVATE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+[\\/]", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+/", re.IGNORECASE),
)
PRIVATE_EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo|icloud|protonmail)\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
TOKEN_PATTERNS = (
    re.compile("gh" + r"[pousr]_[A-Za-z0-9]{30,}"),
    re.compile("github" + r"_pat_[A-Za-z0-9_]{40,}"),
    re.compile("sk" + r"-[A-Za-z0-9_-]{20,}"),
    re.compile("AK" + r"IA[0-9A-Z]{16}"),
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
SENSITIVE_SUFFIXES = {
    ".7z",
    ".bak",
    ".db",
    ".gz",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".tar",
    ".tgz",
    ".zip",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def tracked_paths() -> list[Path]:
    return [ROOT / item for item in git("ls-files").splitlines() if item]


def assert_no_private_or_secret_text(text: str, context: str) -> None:
    assert not PRIVATE_EMAIL_PATTERN.search(text), f"Private email found in {context}"
    for pattern in PRIVATE_PATH_PATTERNS:
        assert not pattern.search(text), f"Absolute user path found in {context}"
    for pattern in TOKEN_PATTERNS:
        assert not pattern.search(text), f"Credential signature found in {context}"


def test_tracked_text_and_reachable_history_are_sanitized() -> None:
    for path in tracked_paths():
        if path == SELF:
            continue
        data = path.read_bytes()
        if b"\x00" in data:
            continue
        assert_no_private_or_secret_text(data.decode("utf-8", errors="ignore"), str(path))

    history_patch = git("log", "-p", "--format=", "HEAD")
    assert_no_private_or_secret_text(history_patch, "reachable Git history")


def test_release_commits_use_github_noreply_addresses() -> None:
    """Prevent v0.3 work from adding to the disclosed pre-release metadata exposure."""
    base = git("merge-base", "HEAD", "origin/main").strip()
    addresses = {
        address.strip().lower()
        for address in git("log", "--format=%ae%n%ce", f"{base}..HEAD").splitlines()
        if address.strip()
    }
    if not addresses:
        configured = git("config", "--get", "user.email").strip().lower()
        addresses = {configured}
    assert all(address.endswith("@users.noreply.github.com") for address in addresses)


def test_sensitive_file_types_and_environment_files_are_not_tracked() -> None:
    for path in tracked_paths():
        relative = path.relative_to(ROOT).as_posix()
        assert path.suffix.lower() not in SENSITIVE_SUFFIXES, f"Sensitive artifact tracked: {relative}"
        if path.name.startswith(".env"):
            assert path.name == ".env.example", f"Non-placeholder environment file tracked: {relative}"
            meaningful = [
                line for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            for line in meaningful:
                key, separator, value = line.partition("=")
                assert separator, f"Malformed placeholder in {relative}: {key}"
                if any(marker in key.upper() for marker in ("KEY", "PASSWORD", "SECRET", "TOKEN")):
                    assert not value, f"Credential-like placeholder is populated in {relative}: {key}"


def test_publication_and_image_metadata_are_intentional_and_sanitized() -> None:
    for path in tracked_paths():
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            with pymupdf.open(path) as document:
                metadata = document.metadata
            if path.name in {"linkedin-carousel.pdf", "hxg-poster.pdf"}:
                assert metadata.get("author") == "Hospitality Experience Graph (HXG)"
                assert metadata.get("creator") == "HXG deterministic Python publication pipeline"
                assert metadata.get("title")
                assert metadata.get("subject")
            else:
                assert metadata.get("author") == "anonymous"
                assert metadata.get("creator") == "anonymous"
            assert metadata.get("creationDate") == "D:20000101000000+00'00'"
            assert metadata.get("modDate") == "D:20000101000000+00'00'"
            assert_no_private_or_secret_text("\n".join(str(value) for value in metadata.values()), str(path))
        elif suffix in {".jpeg", ".jpg", ".png", ".webp"}:
            with Image.open(path) as image:
                assert image.info == {}, f"Unexpected embedded image metadata in {path}"


def test_workflow_actions_are_pinned_to_immutable_commits() -> None:
    uses_pattern = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s+#\s*(v\S+))?", re.MULTILINE)
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for action, version_comment in uses_pattern.findall(path.read_text(encoding="utf-8")):
            if action.startswith("./"):
                continue
            _, separator, revision = action.rpartition("@")
            assert separator and re.fullmatch(r"[0-9a-f]{40}", revision), (
                f"Mutable action reference in {path}: {action}"
            )
            assert version_comment.startswith("v"), f"Missing version comment for {action}"

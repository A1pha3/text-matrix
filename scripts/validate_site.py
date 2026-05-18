from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"\A(?P<delim>\+\+\+|---)\n(?P<body>.*?)(?:\n(?P=delim))\n?", re.DOTALL)
TOML_KV_RE = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*=\s*(?P<value>.+?)\s*$", re.MULTILINE)
YAML_KV_RE = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*:\s*(?P<value>.+?)\s*$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    future = subparsers.add_parser("future-dates")
    future.add_argument("--root", default="content")

    expected = subparsers.add_parser("expected-files")
    expected.add_argument("--site-dir", default="public")
    expected.add_argument(
        "--paths",
        nargs="+",
        help="Site-relative files that must exist after build, e.g. ai-agent/index.html",
    )
    expected.add_argument(
        "--manifest",
        help="Optional newline-delimited manifest of site-relative files to validate",
    )

    return parser.parse_args()


def load_front_matter(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None
    return match.group("delim"), match.group("body")


def parse_front_matter_map(path: Path) -> dict[str, str]:
    parsed = load_front_matter(path)
    if not parsed:
        return {}
    delim, body = parsed
    matcher = TOML_KV_RE if delim == "+++" else YAML_KV_RE
    values: dict[str, str] = {}
    for match in matcher.finditer(body):
        key = match.group("key").strip()
        value = match.group("value").strip().strip("'\"")
        values[key] = value
    return values


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes", "on"}


def parse_iso_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_future_dates(root: Path) -> int:
    now = datetime.now(timezone.utc)
    failures: list[str] = []

    for path in sorted(root.rglob("*.md")):
        metadata = parse_front_matter_map(path)
        if not metadata:
            continue
        if is_truthy(metadata.get("draft")):
            continue
        if is_truthy(metadata.get("allowFuture")) or is_truthy(metadata.get("buildFuture")):
            continue
        date_value = metadata.get("date")
        if not date_value:
            continue
        try:
            publish_date = parse_iso_datetime(date_value)
        except ValueError:
            failures.append(f"无法解析日期: {path} -> {date_value}")
            continue
        if publish_date > now:
            failures.append(f"未来发布时间会导致生产构建缺页: {path} -> {date_value}")

    if failures:
        print("发现会被 Hugo 生产构建排除的未来页面:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("未来发布时间校验通过")
    return 0


def validate_expected_files(site_dir: Path, rel_paths: list[str]) -> int:
    missing = [rel_path for rel_path in rel_paths if not (site_dir / rel_path).is_file()]
    if missing:
        print("构建产物缺少预期页面:")
        for rel_path in missing:
            print(f"- {site_dir / rel_path}")
        return 1

    print("预期页面校验通过")
    return 0


def load_expected_paths(paths: list[str] | None, manifest: str | None) -> list[str]:
    expected_paths = list(paths or [])

    if manifest:
        manifest_path = Path(manifest)
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            expected_paths.append(stripped)

    # Preserve order while deduplicating.
    return list(dict.fromkeys(expected_paths))


def main() -> None:
    args = parse_args()
    if args.command == "future-dates":
        raise SystemExit(validate_future_dates(Path(args.root)))
    if args.command == "expected-files":
        expected_paths = load_expected_paths(args.paths, args.manifest)
        if not expected_paths:
            print("expected-files 至少需要提供 --paths 或 --manifest")
            raise SystemExit(2)
        raise SystemExit(validate_expected_files(Path(args.site_dir), expected_paths))
    raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Gate pip-audit results: fail on High/Critical or unknown severity.

Usage (example):
    uv run python scripts/pip_audit_gate.py --input pip-audit.json --summary pip-audit-summary.txt

    # With ignore file (recommended):
    uv run python scripts/pip_audit_gate.py --input pip-audit.json --summary pip-audit-summary.txt \
        --ignore-file .pip-audit-ignore.json

    # With inline ignore (can be combined with --ignore-file):
    uv run python scripts/pip_audit_gate.py --input pip-audit.json --summary pip-audit-summary.txt \
        --ignore-vuln CVE-2025-66416

This script is used by CI to parse pip-audit JSON output and enforce severity thresholds.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

SeverityFinding = tuple[str, str, str, str]


def load_ignored_vulns(ignore_file: Path | None) -> set[str]:
    """Load ignored vulnerability IDs from a JSON config file.

    Expected format:
        {
            "ignored_vulnerabilities": ["CVE-xxx", "GHSA-xxx"]
        }
    """
    if ignore_file is None or not ignore_file.exists():
        return set()
    try:
        data = json.loads(ignore_file.read_text())
        return set(data.get("ignored_vulnerabilities", []))
    except (json.JSONDecodeError, TypeError):
        return set()


def load_findings(
    data: object, ignored_vulns: set[str] | None = None
) -> list[SeverityFinding]:
    """Extract findings from pip-audit JSON output.

    Handles both dict and list layouts that pip-audit may emit.
    Filters out vulnerabilities whose ID or aliases are in ignored_vulns.
    """
    ignored = ignored_vulns or set()

    if isinstance(data, dict):
        dependencies = data.get("dependencies") or data.get("results") or []
    elif isinstance(data, list):
        dependencies = data
    else:
        dependencies = []

    findings: list[SeverityFinding] = []
    for dep in dependencies:
        name = dep.get("name") or dep.get("dependency", {}).get("name") or "unknown"
        version = (
            dep.get("version") or dep.get("dependency", {}).get("version") or "unknown"
        )
        for vuln in dep.get("vulns", []):
            vuln_id = vuln.get("id") or ""
            aliases = vuln.get("aliases", [])
            # Skip if the vuln ID or any alias is in the ignored set
            all_ids = {vuln_id} | set(aliases)
            if all_ids & ignored:
                continue
            severity = (vuln.get("severity") or "").lower()
            findings.append((severity, name, version, vuln_id))
    return findings


def write_summary(path: Path, findings: Iterable[SeverityFinding]) -> None:
    lines = [
        f"- {(sev or 'unknown').upper()}: {name}@{version} {vuln_id}".rstrip()
        for sev, name, version, vuln_id in findings
    ]
    content = "\n".join(lines) if lines else "No vulnerabilities reported."
    path.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail on High/Critical or unknown severity findings from pip-audit JSON output."
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Path to pip-audit JSON output"
    )
    parser.add_argument(
        "--summary",
        required=True,
        type=Path,
        help="Path to write human-readable summary",
    )
    parser.add_argument(
        "--ignore-file",
        type=Path,
        dest="ignore_file",
        help="Path to JSON file with ignored vulnerabilities (e.g., .pip-audit-ignore.json)",
    )
    parser.add_argument(
        "--ignore-vuln",
        action="append",
        default=[],
        dest="ignore_vulns",
        metavar="ID",
        help="Vulnerability ID (CVE or GHSA) to ignore. Can be specified multiple times.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print("pip-audit output not found", flush=True)
        return 1

    # Merge ignored vulns from file and CLI
    ignored_vulns = load_ignored_vulns(args.ignore_file) | set(args.ignore_vulns)
    data = json.loads(args.input.read_text())
    findings = load_findings(data, ignored_vulns)

    write_summary(args.summary, findings)

    high_or_critical = [f for f in findings if f[0] in {"high", "critical"}]
    unknown = [f for f in findings if not f[0]]

    if high_or_critical or unknown:
        print("High/Critical (or unknown severity) vulnerabilities detected:")
        for sev, name, version, vuln_id in high_or_critical + unknown:
            print(f"- {sev or 'unknown'}: {name}@{version} {vuln_id}".rstrip())
        return 1

    print("No High/Critical vulnerabilities detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

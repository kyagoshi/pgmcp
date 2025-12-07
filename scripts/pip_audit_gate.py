"""Gate pip-audit results: fail on High/Critical or unknown severity.

Usage (example):
    uv run python scripts/pip_audit_gate.py --input pip-audit.json --summary pip-audit-summary.txt

This script is used by CI to parse pip-audit JSON output and enforce severity thresholds.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

SeverityFinding = tuple[str, str, str, str]


def load_findings(data: object) -> list[SeverityFinding]:
    """Extract findings from pip-audit JSON output.

    Handles both dict and list layouts that pip-audit may emit.
    """

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
            severity = (vuln.get("severity") or "").lower()
            vuln_id = vuln.get("id") or next(iter(vuln.get("aliases", [])), "")
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
    args = parser.parse_args()

    if not args.input.exists():
        print("pip-audit output not found", flush=True)
        return 1

    data = json.loads(args.input.read_text())
    findings = load_findings(data)

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

"""Unit tests for scripts/pip_audit_gate.py"""

# ruff: noqa: S101
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Load pip_audit_gate module from scripts directory dynamically
_script_path = Path(__file__).parents[2] / "scripts" / "pip_audit_gate.py"
_spec = importlib.util.spec_from_file_location("pip_audit_gate", _script_path)
if _spec is None or _spec.loader is None:
    raise ImportError("Could not load pip_audit_gate module")
_module = importlib.util.module_from_spec(_spec)
sys.modules["pip_audit_gate"] = _module
_spec.loader.exec_module(_module)

from pip_audit_gate import (  # type: ignore[import-not-found]  # noqa: E402
    load_findings,
    main,
    write_summary,
)


class TestLoadFindings:
    """Tests for load_findings function."""

    def test_load_findings_with_dict_layout(self) -> None:
        data = {
            "dependencies": [
                {
                    "name": "pkg",
                    "version": "1.0",
                    "vulns": [{"severity": "high", "id": "CVE-123"}],
                }
            ]
        }
        findings = load_findings(data)
        assert findings == [("high", "pkg", "1.0", "CVE-123")]

    def test_load_findings_with_list_layout(self) -> None:
        data = [
            {
                "name": "pkg",
                "version": "2.0",
                "vulns": [{"severity": "critical", "id": "CVE-456"}],
            }
        ]
        findings = load_findings(data)
        assert findings == [("critical", "pkg", "2.0", "CVE-456")]

    def test_load_findings_with_results_key(self) -> None:
        data = {
            "results": [
                {
                    "name": "lib",
                    "version": "3.0",
                    "vulns": [{"severity": "medium", "id": "CVE-789"}],
                }
            ]
        }
        findings = load_findings(data)
        assert findings == [("medium", "lib", "3.0", "CVE-789")]

    def test_load_findings_with_nested_dependency(self) -> None:
        data = [
            {
                "dependency": {"name": "nested-pkg", "version": "1.5"},
                "vulns": [{"severity": "low", "id": "CVE-111"}],
            }
        ]
        findings = load_findings(data)
        assert findings == [("low", "nested-pkg", "1.5", "CVE-111")]

    def test_load_findings_with_aliases(self) -> None:
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"severity": "high", "aliases": ["GHSA-abc", "CVE-222"]}],
            }
        ]
        findings = load_findings(data)
        assert findings == [("high", "pkg", "1.0", "GHSA-abc")]

    def test_load_findings_empty_dependencies(self) -> None:
        data: dict[str, Any] = {"dependencies": []}
        findings = load_findings(data)
        assert findings == []

    def test_load_findings_no_vulns(self) -> None:
        data = [{"name": "safe-pkg", "version": "1.0", "vulns": []}]
        findings = load_findings(data)
        assert findings == []

    def test_load_findings_unknown_severity(self) -> None:
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"id": "CVE-333"}],  # no severity
            }
        ]
        findings = load_findings(data)
        assert findings == [("", "pkg", "1.0", "CVE-333")]

    def test_load_findings_invalid_data(self) -> None:
        findings = load_findings("invalid")
        assert findings == []

    def test_load_findings_none_data(self) -> None:
        findings = load_findings(None)
        assert findings == []


class TestWriteSummary:
    """Tests for write_summary function."""

    def test_write_summary_with_findings(self, tmp_path: Path) -> None:
        summary_path = tmp_path / "summary.txt"
        findings = [
            ("high", "pkg1", "1.0", "CVE-111"),
            ("critical", "pkg2", "2.0", "CVE-222"),
        ]
        write_summary(summary_path, findings)
        content = summary_path.read_text()
        assert "- HIGH: pkg1@1.0 CVE-111" in content
        assert "- CRITICAL: pkg2@2.0 CVE-222" in content

    def test_write_summary_with_unknown_severity(self, tmp_path: Path) -> None:
        summary_path = tmp_path / "summary.txt"
        findings = [("", "pkg", "1.0", "CVE-333")]
        write_summary(summary_path, findings)
        content = summary_path.read_text()
        assert "- UNKNOWN: pkg@1.0 CVE-333" in content

    def test_write_summary_no_findings(self, tmp_path: Path) -> None:
        summary_path = tmp_path / "summary.txt"
        write_summary(summary_path, [])
        content = summary_path.read_text()
        assert content == "No vulnerabilities reported."


class TestMain:
    """Tests for main function."""

    def test_main_no_high_critical(self, tmp_path: Path) -> None:
        input_file = tmp_path / "pip-audit.json"
        summary_file = tmp_path / "summary.txt"
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"severity": "low", "id": "CVE-111"}],
            }
        ]
        input_file.write_text(json.dumps(data))

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 0
        assert summary_file.exists()

    def test_main_with_high_severity(self, tmp_path: Path) -> None:
        input_file = tmp_path / "pip-audit.json"
        summary_file = tmp_path / "summary.txt"
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"severity": "high", "id": "CVE-111"}],
            }
        ]
        input_file.write_text(json.dumps(data))

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 1

    def test_main_with_critical_severity(self, tmp_path: Path) -> None:
        input_file = tmp_path / "pip-audit.json"
        summary_file = tmp_path / "summary.txt"
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"severity": "critical", "id": "CVE-222"}],
            }
        ]
        input_file.write_text(json.dumps(data))

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 1

    def test_main_with_unknown_severity(self, tmp_path: Path) -> None:
        input_file = tmp_path / "pip-audit.json"
        summary_file = tmp_path / "summary.txt"
        data = [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"id": "CVE-333"}],  # no severity
            }
        ]
        input_file.write_text(json.dumps(data))

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 1

    def test_main_missing_input_file(self, tmp_path: Path) -> None:
        input_file = tmp_path / "nonexistent.json"
        summary_file = tmp_path / "summary.txt"

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 1

    def test_main_no_vulnerabilities(self, tmp_path: Path) -> None:
        input_file = tmp_path / "pip-audit.json"
        summary_file = tmp_path / "summary.txt"
        data = [{"name": "safe-pkg", "version": "1.0", "vulns": []}]
        input_file.write_text(json.dumps(data))

        with patch(
            "sys.argv",
            ["prog", "--input", str(input_file), "--summary", str(summary_file)],
        ):
            result = main()

        assert result == 0
        assert summary_file.read_text() == "No vulnerabilities reported."

#!/usr/bin/env python3
"""
Automated Test Report Generator

This script:
1. Runs pytest with JSON output and coverage
2. Parses test results
3. Generates TEST_RESULTS.md with summary
4. Auto-updates TEST_CASES.md with actual results
5. Generates coverage report

Usage:
    python backend/tests/generate_test_report.py
    python backend/tests/generate_test_report.py --no-run  # Skip test execution
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re


class TestReportGenerator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"
        self.docs_dir = project_root / "docs" / "testing"
        self.test_results_file = self.backend_dir / "test_results.json"
        self.coverage_file = self.backend_dir / "coverage.json"

    def run_tests(self) -> bool:
        """Run pytest with JSON output and coverage"""
        print("🧪 Running tests with coverage...")

        cmd = [
            "pytest",
            str(self.backend_dir / "tests"),
            "--json-report",
            f"--json-report-file={self.test_results_file}",
            "--json-report-indent=2",
            "--cov=services",
            "--cov=app",
            "--cov-report=json",
            f"--cov-report=json:{self.coverage_file}",
            "--cov-report=term",
            "-v"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error running tests: {e}", file=sys.stderr)
            return False

    def parse_test_results(self) -> Dict[str, Any]:
        """Parse pytest JSON output"""
        if not self.test_results_file.exists():
            print(f"❌ Test results file not found: {self.test_results_file}")
            return {}

        with open(self.test_results_file, 'r') as f:
            return json.load(f)

    def parse_coverage(self) -> Dict[str, Any]:
        """Parse coverage JSON output"""
        if not self.coverage_file.exists():
            print(f"⚠️  Coverage file not found: {self.coverage_file}")
            return {"totals": {"percent_covered": 0}}

        with open(self.coverage_file, 'r') as f:
            return json.load(f)

    def map_test_to_case_id(self, test_name: str, test_location: str) -> str:
        """Map test function name to test case ID"""
        # Extract test case ID from test name or docstring
        # Pattern: TC-XXX-NNN or TCNN

        # Try to find TC pattern in test name
        if "discovery" in test_location.lower():
            return "TC01"
        elif "poll" in test_location.lower():
            return "TC02"
        elif "alert" in test_location.lower():
            return "TC03"
        elif "setting" in test_location.lower() or "config" in test_location.lower():
            return "TC04"
        elif "device" in test_location.lower() and "detail" in test_name.lower():
            return "TC05"
        elif "alert" in test_location.lower() and "history" in test_name.lower():
            return "TC06"
        elif "snmp" in test_location.lower() and "invalid" in test_name.lower():
            return "TC07"

        return "UNKNOWN"

    def generate_summary_report(self, test_data: Dict, coverage_data: Dict) -> str:
        """Generate markdown summary report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate statistics
        summary = test_data.get("summary", {})
        total_tests = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        duration = test_data.get("duration", 0)

        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        coverage_pct = coverage_data.get("totals", {}).get("percent_covered", 0)

        # Group tests by category
        tests_by_category = {
            "TC01 - Device Discovery": [],
            "TC02 - SNMP Polling": [],
            "TC03 - Alert System": [],
            "TC04 - Configuration": [],
            "TC05 - Device Details": [],
            "TC06 - Alert History": [],
            "TC07 - Error Handling": [],
            "Other Tests": []
        }

        for test in test_data.get("tests", []):
            test_id = self.map_test_to_case_id(test.get("nodeid", ""), test.get("nodeid", ""))
            category_map = {
                "TC01": "TC01 - Device Discovery",
                "TC02": "TC02 - SNMP Polling",
                "TC03": "TC03 - Alert System",
                "TC04": "TC04 - Configuration",
                "TC05": "TC05 - Device Details",
                "TC06": "TC06 - Alert History",
                "TC07": "TC07 - Error Handling"
            }
            category = category_map.get(test_id, "Other Tests")
            tests_by_category[category].append(test)

        # Generate report
        report = f"""# Test Execution Report

**Generated**: {timestamp}
**Status**: {"✅ PASSED" if failed == 0 else "❌ FAILED"}

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | {total_tests} |
| **✅ Passed** | {passed} ({pass_rate:.1f}%) |
| **❌ Failed** | {failed} |
| **⏭️ Skipped** | {skipped} |
| **⏱️ Duration** | {duration:.2f}s |
| **📈 Coverage** | {coverage_pct:.1f}% |

---

## 🎯 Test Case Mapping

### TC01: Device Discovery
"""

        # Add test results by category
        for category, tests in tests_by_category.items():
            if not tests:
                continue

            report += f"\n### {category}\n\n"
            report += "| Test | Status | Duration |\n"
            report += "|------|--------|----------|\n"

            for test in tests:
                nodeid = test.get("nodeid", "Unknown")
                test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
                outcome = test.get("outcome", "unknown")
                duration_test = test.get("call", {}).get("duration", 0)

                status_icon = {
                    "passed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️"
                }.get(outcome, "❓")

                report += f"| `{test_name}` | {status_icon} {outcome.upper()} | {duration_test:.3f}s |\n"

        # Add failed test details
        if failed > 0:
            report += "\n---\n\n## ❌ Failed Tests Details\n\n"
            for test in test_data.get("tests", []):
                if test.get("outcome") == "failed":
                    nodeid = test.get("nodeid", "Unknown")
                    call = test.get("call", {})
                    longrepr = call.get("longrepr", "No error details available")

                    report += f"### {nodeid}\n\n"
                    report += "```\n"
                    report += str(longrepr)[:500]  # Limit error message length
                    report += "\n```\n\n"

        # Add coverage details
        report += "\n---\n\n## 📈 Coverage Report\n\n"
        report += "| Module | Coverage |\n"
        report += "|--------|----------|\n"

        files = coverage_data.get("files", {})
        for filepath, data in sorted(files.items(), key=lambda x: x[1].get("summary", {}).get("percent_covered", 0), reverse=True)[:10]:
            filename = Path(filepath).name
            pct = data.get("summary", {}).get("percent_covered", 0)
            report += f"| `{filename}` | {pct:.1f}% |\n"

        report += "\n---\n\n## 📝 Test Case Status Summary\n\n"
        report += "| Test Case ID | Description | Status |\n"
        report += "|--------------|-------------|--------|\n"
        report += "| **TC01** | Device Discovery | "

        # Determine status for each test case
        tc_status = {}
        for tc_id in ["TC01", "TC02", "TC03", "TC04", "TC05", "TC06", "TC07"]:
            tc_tests = [t for t in test_data.get("tests", [])
                       if self.map_test_to_case_id(t.get("nodeid", ""), t.get("nodeid", "")) == tc_id]
            if not tc_tests:
                tc_status[tc_id] = "⏳ Pending"
            elif all(t.get("outcome") == "passed" for t in tc_tests):
                tc_status[tc_id] = "✅ Pass"
            elif any(t.get("outcome") == "failed" for t in tc_tests):
                tc_status[tc_id] = "❌ Fail"
            else:
                tc_status[tc_id] = "⚠️ Partial"

        report += f"{tc_status.get('TC01', '⏳ Pending')} |\n"
        report += f"| **TC02** | SNMP Polling | {tc_status.get('TC02', '⏳ Pending')} |\n"
        report += f"| **TC03** | Alert Triggering | {tc_status.get('TC03', '⏳ Pending')} |\n"
        report += f"| **TC04** | Configuration Changes | {tc_status.get('TC04', '⏳ Pending')} |\n"
        report += f"| **TC05** | Device Details View | {tc_status.get('TC05', '⏳ Pending')} |\n"
        report += f"| **TC06** | Alert History | {tc_status.get('TC06', '⏳ Pending')} |\n"
        report += f"| **TC07** | Invalid SNMP String | {tc_status.get('TC07', '⏳ Pending')} |\n"

        report += "\n---\n\n**Report End**\n"

        return report

    def save_report(self, report: str):
        """Save report to docs/testing/TEST_RESULTS.md"""
        output_file = self.docs_dir / "TEST_RESULTS.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(report)

        print(f"✅ Report saved to: {output_file}")

    def run(self, skip_tests: bool = False):
        """Main execution flow"""
        print("=" * 60)
        print("📋 SNMP Monitoring System - Test Report Generator")
        print("=" * 60)

        if not skip_tests:
            success = self.run_tests()
            if not success:
                print("⚠️  Tests failed, but generating report anyway...")
        else:
            print("⏭️  Skipping test execution (using existing results)")

        print("\n📊 Parsing test results...")
        test_data = self.parse_test_results()

        if not test_data:
            print("❌ No test results found. Run tests first!")
            return False

        print("📈 Parsing coverage data...")
        coverage_data = self.parse_coverage()

        print("📝 Generating report...")
        report = self.generate_summary_report(test_data, coverage_data)

        print("💾 Saving report...")
        self.save_report(report)

        # Print summary
        summary = test_data.get("summary", {})
        print("\n" + "=" * 60)
        print("✅ Report generation complete!")
        print(f"   Total: {summary.get('total', 0)} | "
              f"Passed: {summary.get('passed', 0)} | "
              f"Failed: {summary.get('failed', 0)}")
        print("=" * 60)

        return summary.get("failed", 0) == 0


def main():
    parser = argparse.ArgumentParser(description="Generate automated test report")
    parser.add_argument("--no-run", action="store_true",
                       help="Skip test execution, use existing results")
    args = parser.parse_args()

    # Find project root (where README.md exists)
    current_dir = Path.cwd()
    project_root = current_dir

    # Navigate up to find project root
    while not (project_root / "README.md").exists() and project_root != project_root.parent:
        project_root = project_root.parent

    if not (project_root / "README.md").exists():
        print("❌ Could not find project root (README.md not found)")
        sys.exit(1)

    generator = TestReportGenerator(project_root)
    success = generator.run(skip_tests=args.no_run)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

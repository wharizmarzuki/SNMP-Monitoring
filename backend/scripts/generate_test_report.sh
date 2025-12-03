#!/bin/bash
# Generate test report with actual results

echo "Running tests and generating report..."

# Run tests and capture output
pytest tests/test_discovery.py tests/test_polling.py tests/test_settings.py tests/test_snmp_errors.py tests/test_alerts.py -v --tb=short > /tmp/test_output.txt 2>&1

# Extract results
TOTAL_PASSED=$(grep -oP '\d+(?= passed)' /tmp/test_output.txt | tail -1)
TOTAL_FAILED=$(grep -oP '\d+(?= failed)' /tmp/test_output.txt | tail -1 || echo "0")
TOTAL_TIME=$(grep -oP '\d+\.\d+(?=s)' /tmp/test_output.txt | tail -1)

# Generate report
cat > docs/testing/LATEST_TEST_RUN.md <<EOF
# Latest Test Run Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Command**: pytest -v

## Summary

- **Total Passed**: ${TOTAL_PASSED}
- **Total Failed**: ${TOTAL_FAILED}
- **Duration**: ${TOTAL_TIME}s
- **Pass Rate**: $(echo "scale=2; ${TOTAL_PASSED} / (${TOTAL_PASSED} + ${TOTAL_FAILED}) * 100" | bc)%

## Detailed Output

\`\`\`
$(cat /tmp/test_output.txt)
\`\`\`

EOF

echo "✅ Report generated: docs/testing/LATEST_TEST_RUN.md"
echo "📊 Passed: ${TOTAL_PASSED}, Failed: ${TOTAL_FAILED}"

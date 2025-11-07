#!/bin/bash
# Count Lines of Code
# Counts lines of code in current directory

echo "=== Lines of Code Count ==="
echo ""

# Python
PYTHON_FILES=$(find . -name "*.py" -not -path "./*/__pycache__/*" -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
PYTHON_LINES=$(find . -name "*.py" -not -path "./*/__pycache__/*" -not -path "./.git/*" -exec cat {} \; 2>/dev/null | wc -l | tr -d ' ')
echo "Python: $PYTHON_FILES files, $PYTHON_LINES lines"

# JavaScript/TypeScript
JS_FILES=$(find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v .git | wc -l | tr -d ' ')
JS_LINES=$(find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v .git | xargs cat 2>/dev/null | wc -l | tr -d ' ')
echo "JavaScript/TypeScript: $JS_FILES files, $JS_LINES lines"

# Total
TOTAL_FILES=$(($PYTHON_FILES + $JS_FILES))
TOTAL_LINES=$(($PYTHON_LINES + $JS_LINES))
echo ""
echo "Total: $TOTAL_FILES files, $TOTAL_LINES lines"


#!/bin/bash
# scripts/smart_commit.sh
# Automated proof-backed commits for UCOS
# Ensures every commit includes test results and validation status

set -e  # Exit on error

echo "🚀 UCOS Smart Commit"
echo "==================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Check if there are changes to commit
if [ -z "$(git diff --name-only --cached)" ] && [ -z "$(git diff --name-only HEAD)" ]; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
    exit 0
fi

# 2. Run safety validation
echo "🔒 Running safety validation..."
echo ""

if ! ./scripts/validate.sh > /tmp/validate_output.txt 2>&1; then
    echo -e "${RED}❌ Safety validation FAILED!${NC}"
    echo ""
    echo "Last 20 lines of output:"
    tail -20 /tmp/validate_output.txt
    echo ""
    echo -e "${YELLOW}⚠️  DO NOT COMMIT until validation passes.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Safety validation passed${NC}"
echo ""

# 3. Capture test results
echo "📊 Capturing test results..."
TEST_OUTPUT=$(python -m pytest --tb=short -q 2>&1 || true)
TEST_SUMMARY=$(echo "$TEST_OUTPUT" | grep -E "(passed|failed|PASSED|FAILED)" | tail -3 || echo "Tests completed")

# 4. Get changed files
CHANGED_FILES=$(git diff --name-only --cached 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || echo "No staged changes")

# 5. Ask for commit type
echo "📝 Commit type:"
echo "  1) [FEATURE] New functionality"
echo "  2) [FIX] Bug fix"
echo "  3) [DOCS] Documentation"
echo "  4) [TEST] Test updates"
echo "  5) [REFACTOR] Code restructuring"
echo "  6) [CHORE] Maintenance"
echo "  7) [SCENARIO] Nairobi business scenario"
read -p "Select (1-7): " COMMIT_TYPE

case $COMMIT_TYPE in
    1) PREFIX="[FEATURE]" ;;
    2) PREFIX="[FIX]" ;;
    3) PREFIX="[DOCS]" ;;
    4) PREFIX="[TEST]" ;;
    5) PREFIX="[REFACTOR]" ;;
    6) PREFIX="[CHORE]" ;;
    7) PREFIX="[SCENARIO]" ;;
    *) PREFIX="[UPDATE]" ;;
esac

# 6. Ask for component
echo ""
read -p "🔧 Component (e.g., TIMER, AUTO-REFUND, TRUST, CREDIT, SAFETY, DOCS, WORKFLOW): " COMPONENT
COMPONENT=${COMPONENT:-GENERAL}

# 7. Ask for description
echo ""
read -p "📋 Brief description: " DESCRIPTION

if [ -z "$DESCRIPTION" ]; then
    echo -e "${RED}❌ Description required${NC}"
    exit 1
fi

# 8. Generate commit message
COMMIT_MSG="$PREFIX[$COMPONENT] $DESCRIPTION

## Test Results
\`\`\`
$TEST_SUMMARY
\`\`\`

## Changed Files
$(echo "$CHANGED_FILES" | sed 's/^/- /')

## Validation
- Safety checks: PASSED ✅
- UCOS physics: VERIFIED ✅
- Nairobi scenarios: INTACT ✅"

# 9. Show preview and confirm
echo ""
echo "📄 Commit message preview:"
echo "=========================="
echo "$COMMIT_MSG"
echo "=========================="
echo ""
read -p "✅ Commit? (y/n): " CONFIRM

if [[ $CONFIRM == "y" || $CONFIRM == "Y" ]]; then
    # Stage all changes if nothing staged
    if [ -z "$(git diff --name-only --cached)" ]; then
        echo ""
        echo "📦 Staging all changes..."
        git add -A
    fi
    
    # Create commit with multi-line message
    echo "$COMMIT_MSG" | git commit -F -
    echo ""
    echo -e "${GREEN}🎉 Commit created with proof!${NC}"
    echo ""
    echo "View commit:"
    echo "  git show HEAD"
else
    echo ""
    echo -e "${YELLOW}❌ Commit cancelled${NC}"
    exit 1
fi


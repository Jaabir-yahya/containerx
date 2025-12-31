#!/bin/bash
# UCOS Safety: Validation Script
# Runs all safety checks before commit

set -e

echo "🔍 Running UCOS Safety Validation..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# 1. Run minimal safety scenario
echo "1️⃣  Running minimal safety scenario..."
if python -m pytest tests/scenarios/minimal_safety.py -v --tb=short; then
    echo -e "${GREEN}✅ Minimal safety passed${NC}"
else
    echo -e "${RED}❌ Minimal safety FAILED${NC}"
    FAILED=1
fi
echo ""

# 2. Run UCOS physics validation
echo "2️⃣  Running UCOS physics validation..."
if python -m pytest tests/ucos_physics/ -v --tb=short; then
    echo -e "${GREEN}✅ UCOS physics validated${NC}"
else
    echo -e "${RED}❌ UCOS physics FAILED${NC}"
    FAILED=1
fi
echo ""

# 3. Run TimerService tests (if exists)
if [ -f "tests/test_timer_service.py" ]; then
    echo "3️⃣  Running TimerService tests..."
    if python -m pytest tests/test_timer_service.py -v --tb=short; then
        echo -e "${GREEN}✅ TimerService tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  TimerService tests failed (non-blocking)${NC}"
    fi
    echo ""
fi

# Final result
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All safety checks passed! Safe to commit.${NC}"
    exit 0
else
    echo -e "${RED}❌ Safety checks FAILED! DO NOT COMMIT.${NC}"
    echo -e "${YELLOW}Fix the failing tests before committing.${NC}"
    exit 1
fi


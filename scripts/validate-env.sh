#!/usr/bin/env bash
#
# Environment Variable Validation Script
# Validates .env file before deployment to catch configuration errors early
#
# Usage: bash scripts/validate-env.sh
# Exit codes:
#   0 = Validation passed
#   1 = Validation failed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error tracking
ERRORS=0
WARNINGS=0

echo "================================================"
echo "Environment Variable Validation"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please create .env file from template:"
    echo "  cp .env.production.example .env"
    exit 1
fi

# Load .env file
export $(grep -v '^#' .env | xargs)

echo "✓ Found .env file"
echo ""

# ============================================================================
# REQUIRED VARIABLES
# ============================================================================

echo "Checking REQUIRED variables..."
echo "----------------------------------------"

# Check POSTGRES_PASSWORD
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}✗ POSTGRES_PASSWORD is not set${NC}"
    ((ERRORS++))
elif [ "$POSTGRES_PASSWORD" = "CHANGE_ME_GENERATE_STRONG_PASSWORD_MIN_16_CHARS" ]; then
    echo -e "${RED}✗ POSTGRES_PASSWORD still has placeholder value${NC}"
    echo "  Generate: openssl rand -base64 32"
    ((ERRORS++))
elif [ ${#POSTGRES_PASSWORD} -lt 16 ]; then
    echo -e "${RED}✗ POSTGRES_PASSWORD is too short (minimum 16 characters)${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ POSTGRES_PASSWORD is set and strong${NC}"
fi

# Check API_SECRET_KEY
if [ -z "$API_SECRET_KEY" ]; then
    echo -e "${RED}✗ API_SECRET_KEY is not set${NC}"
    ((ERRORS++))
elif [ "$API_SECRET_KEY" = "CHANGE_ME_GENERATE_STRONG_API_KEY_MIN_32_CHARS" ]; then
    echo -e "${RED}✗ API_SECRET_KEY still has placeholder value${NC}"
    echo "  Generate: openssl rand -base64 32"
    ((ERRORS++))
elif [ ${#API_SECRET_KEY} -lt 32 ]; then
    echo -e "${RED}✗ API_SECRET_KEY is too short (minimum 32 characters)${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ API_SECRET_KEY is set and strong${NC}"
fi

echo ""

# ============================================================================
# OPTIONAL VARIABLES (warnings only)
# ============================================================================

echo "Checking OPTIONAL variables..."
echo "----------------------------------------"

# Check DEBUG mode
if [ "$DEBUG" = "true" ]; then
    echo -e "${YELLOW}⚠ DEBUG=true (recommended: false for production)${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓ DEBUG mode disabled${NC}"
fi

# Check ALLOWED_ORIGINS
if [ -z "$ALLOWED_ORIGINS" ]; then
    echo -e "${GREEN}✓ ALLOWED_ORIGINS empty (using IP regex fallback)${NC}"
else
    echo -e "${GREEN}✓ ALLOWED_ORIGINS configured: $ALLOWED_ORIGINS${NC}"
fi

# Check FRONTEND_PORT
if [ -z "$FRONTEND_PORT" ]; then
    echo "  FRONTEND_PORT not set (will use default: 80)"
elif [ "$FRONTEND_PORT" -eq 80 ] 2>/dev/null; then
    echo -e "${GREEN}✓ FRONTEND_PORT=80 (standard HTTP port)${NC}"
else
    echo -e "${GREEN}✓ FRONTEND_PORT=$FRONTEND_PORT${NC}"
fi

echo ""

# ============================================================================
# SECURITY CHECKS
# ============================================================================

echo "Security checks..."
echo "----------------------------------------"

# Check for weak passwords
if echo "$POSTGRES_PASSWORD" | grep -qiE "(password|123456|qwerty|admin)"; then
    echo -e "${RED}✗ POSTGRES_PASSWORD contains common weak patterns${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ POSTGRES_PASSWORD doesn't contain obvious weak patterns${NC}"
fi

# Check if .env is in .gitignore
if [ -f .gitignore ]; then
    if grep -q "^\.env$" .gitignore; then
        echo -e "${GREEN}✓ .env is in .gitignore${NC}"
    else
        echo -e "${YELLOW}⚠ .env is NOT in .gitignore (secrets may be committed!)${NC}"
        ((WARNINGS++))
    fi
fi

echo ""

# ============================================================================
# FINAL RESULT
# ============================================================================

echo "================================================"
echo "Validation Summary"
echo "================================================"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Validation PASSED${NC}"
    echo ""
    echo "Your .env file is ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Review your configuration one more time"
    echo "  2. Deploy: docker compose -f docker-compose.prod.yml up -d"
    echo ""
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Note: $WARNINGS warning(s) found (review recommended)${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}✗ Validation FAILED${NC}"
    echo ""
    echo "Found $ERRORS error(s) and $WARNINGS warning(s)"
    echo "Please fix the errors above before deploying"
    echo ""
    exit 1
fi

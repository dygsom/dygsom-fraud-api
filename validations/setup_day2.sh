#!/usr/bin/env bash

# Setup script for Day 2 - Database and Seed Data
# Run inside Docker container

set -e

echo "=================================="
echo "DYGSOM FRAUD API - Day 2 Setup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Generate Prisma Client
echo -e "${YELLOW}[1/4] Generating Prisma Client...${NC}"
prisma generate

# Step 2: Push database schema
echo -e "${YELLOW}[2/4] Pushing database schema...${NC}"
prisma db push --skip-generate

# Step 3: Install Faker if not installed
echo -e "${YELLOW}[3/4] Checking dependencies...${NC}"
pip install faker==22.0.0 --quiet

# Step 4: Run seed script
echo -e "${YELLOW}[4/4] Running seed script...${NC}"
python -m src.scripts.seed_transactions

echo ""
echo -e "${GREEN}✅ Setup completed!${NC}"
echo ""
echo "Run verification:"
echo "  python scripts/verify_day2.py"

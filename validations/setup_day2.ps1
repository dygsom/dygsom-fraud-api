# Setup script for Day 2 - Database and Seed Data (Windows PowerShell)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "DYGSOM FRAUD API - Day 2 Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate Prisma Client
Write-Host "[1/4] Generating Prisma Client..." -ForegroundColor Yellow
prisma generate

# Step 2: Push database schema
Write-Host "[2/4] Pushing database schema..." -ForegroundColor Yellow
prisma db push --skip-generate

# Step 3: Install Faker if not installed
Write-Host "[3/4] Checking dependencies..." -ForegroundColor Yellow
pip install faker==22.0.0 --quiet

# Step 4: Run seed script
Write-Host "[4/4] Running seed script..." -ForegroundColor Yellow
python -m src.scripts.seed_transactions

Write-Host ""
Write-Host "✅ Setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Run verification:"
Write-Host "  python scripts/verify_day2.py"

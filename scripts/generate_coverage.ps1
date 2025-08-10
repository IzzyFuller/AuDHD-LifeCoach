# PowerShell script to run tests with coverage and generate badge
# Usage: .\scripts\generate_coverage.ps1

Write-Host "📊 Running AuDHD-LifeCoach Test Coverage Analysis" -ForegroundColor Green
Write-Host "=" * 50

# Change to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
Write-Host "📁 Working directory: $projectRoot" -ForegroundColor Blue

try {
    # Run tests with coverage
    Write-Host "🔄 Running tests with coverage..." -ForegroundColor Yellow
    poetry run pytest tests/ --cov=src/audhd_lifecoach --cov-report=term --cov-report=html --cov-report=xml
    
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed with exit code $LASTEXITCODE"
    }
    
    # Generate coverage badge
    Write-Host "🔄 Generating coverage badge..." -ForegroundColor Yellow
    poetry run coverage-badge -f -o coverage.svg
    
    if ($LASTEXITCODE -ne 0) {
        throw "Coverage badge generation failed with exit code $LASTEXITCODE"
    }
    
    Write-Host "`n✅ Coverage analysis complete!" -ForegroundColor Green
    Write-Host "📄 Coverage report: htmlcov/index.html" -ForegroundColor Cyan
    Write-Host "🏷️  Coverage badge: coverage.svg" -ForegroundColor Cyan
    Write-Host "📊 XML report: coverage.xml" -ForegroundColor Cyan
    
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

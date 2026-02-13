# Build script for AI Agent
# Creates a standalone executable using PyInstaller

Write-Host "Building AI Agent..." -ForegroundColor Green

# Clean previous builds
if (Test-Path "build") {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "build"
}

if (Test-Path "dist") {
    Write-Host "Cleaning dist directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}

# Run PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Green
pyinstaller ai_agent.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    Write-Host "Executable location: dist\AIAgent.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    exit 1
}

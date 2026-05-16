# Run course tests (Server + UI + BP) and generate Word report
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Docx = Join-Path $Root "docs\test_tables_STEEL_BLADE.docx"

Write-Host "=== Backend (15 tests: Server + BP) ===" -ForegroundColor Cyan
Push-Location (Join-Path $Root "Backend")
$env:USE_SQLITE = "1"
python manage.py test apps.salon.test_server_api apps.salon.test_business_processes -v 1
Pop-Location

Write-Host ""
Write-Host "=== Frontend (10 UI tests) ===" -ForegroundColor Cyan
Push-Location (Join-Path $Root "Frontend")
if (-not (Test-Path "node_modules")) { npm install }
npm test
Pop-Location

Write-Host ""
Write-Host "=== Word report ===" -ForegroundColor Cyan
$env:OUT_DOCX = $Docx
python (Join-Path $Root "tools\fill_three_test_tables.py")
Write-Host "Done. Report saved to:" -ForegroundColor Green
Write-Host $Docx -ForegroundColor Green

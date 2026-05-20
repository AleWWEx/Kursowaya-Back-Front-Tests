#Requires -RunAsAdministrator
<#
  Temporarily sets trust in pg_hba.conf for localhost, runs ALTER ROLE for alex,
  then restores pg_hba.conf from backup.

  Run in elevated PowerShell (Run as Administrator):
    cd "C:\Users\Asus\OneDrive\Desktop\Kursowaya_Back-Front-main\tools"
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
    .\reset_postgres_alex_password.ps1
#>
$ErrorActionPreference = "Stop"

$ServiceName = "postgresql-x64-18"
$PgData = "D:\PSQL\data"
$PgBin = "D:\PSQL\bin"
$Hba = Join-Path $PgData "pg_hba.conf"
$HbaBackup = Join-Path $PgData ("pg_hba.conf.bak_before_alex_pw_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$NewPassword = "1111"

if (-not (Test-Path -LiteralPath $Hba)) {
    Write-Error ("pg_hba.conf not found: " + $Hba + ". Edit PgData/PgBin in this script.")
}

Write-Host "Stopping service $ServiceName ..." -ForegroundColor Cyan
Stop-Service -Name $ServiceName -Force
Start-Sleep -Seconds 3

Copy-Item -LiteralPath $Hba -Destination $HbaBackup -Force
Write-Host ("Backup: " + $HbaBackup) -ForegroundColor Green

$lines = Get-Content -LiteralPath $Hba
$out = foreach ($line in $lines) {
    $t = $line
    if ($t -match "^\s*#" -or $t -notmatch "scram-sha-256") {
        $t
        continue
    }
    if ($t -match "127\.0\.0\.1/32\s+scram-sha-256") { $t -replace "scram-sha-256\s*$", "trust"; continue }
    if ($t -match "::1/128\s+scram-sha-256") { $t -replace "scram-sha-256\s*$", "trust"; continue }
    if ($t -match "^\s*local\s+all\s+all\s+") { $t -replace "scram-sha-256\s*$", "trust"; continue }
    if ($t -match "^\s*local\s+replication\s+") { $t -replace "scram-sha-256\s*$", "trust"; continue }
    if ($t -match "^\s*host\s+replication\s+") { $t -replace "scram-sha-256\s*$", "trust"; continue }
    $t
}
$out | Set-Content -LiteralPath $Hba -Encoding utf8

Write-Host "Starting service ..." -ForegroundColor Cyan
Start-Service -Name $ServiceName
Start-Sleep -Seconds 4

$psql = Join-Path $PgBin "psql.exe"
if (-not (Test-Path -LiteralPath $psql)) {
    Write-Error ("psql not found: " + $psql)
}

$sqlAlex = "ALTER ROLE alex WITH PASSWORD '" + $NewPassword + "';"
Write-Host "Setting password for role alex ..." -ForegroundColor Cyan
& $psql -U postgres -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=1 -c $sqlAlex
if ($LASTEXITCODE -ne 0) {
    Write-Host "Trying quoted role name Alex ..." -ForegroundColor Yellow
    & $psql -U postgres -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=1 -c 'ALTER ROLE "Alex" WITH PASSWORD ''1111'';'
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'ALTER ROLE failed. List roles: psql -U postgres -h 127.0.0.1 -d postgres -c "\du"'
    }
}

Write-Host "Restoring pg_hba.conf from backup ..." -ForegroundColor Cyan
Stop-Service -Name $ServiceName -Force
Start-Sleep -Seconds 3
Copy-Item -LiteralPath $HbaBackup -Destination $Hba -Force
Start-Service -Name $ServiceName

Write-Host ""
Write-Host ("Done. New password: " + $NewPassword) -ForegroundColor Green
Write-Host "Set POSTGRES_USER=alex (or Alex) and POSTGRES_PASSWORD in your environment." -ForegroundColor Green

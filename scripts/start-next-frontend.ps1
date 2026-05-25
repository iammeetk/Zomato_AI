# Bootstrap portable Node.js and run Next.js dev server on port 3000.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Frontend = Join-Path $Root "frontend-next"
$Tools = Join-Path $Frontend ".tools"
$NodeDir = Join-Path $Tools "node"
$NodeVersion = "v22.12.0"
$ZipName = "node-$NodeVersion-win-x64.zip"
$ZipUrl = "https://nodejs.org/dist/$NodeVersion/$ZipName"
$NodeExe = Join-Path $NodeDir "node.exe"
$NpmCmd = Join-Path $NodeDir "npm.cmd"

if (-not (Test-Path $NodeExe)) {
    Write-Host "Downloading portable Node.js $NodeVersion..."
    New-Item -ItemType Directory -Force -Path $Tools | Out-Null
    $zipPath = Join-Path $Tools $ZipName
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $Tools -Force
    $extracted = Join-Path $Tools "node-$NodeVersion-win-x64"
    if (Test-Path $NodeDir) { Remove-Item $NodeDir -Recurse -Force }
    Rename-Item $extracted "node"
    Remove-Item $zipPath -Force
    Write-Host "Node installed at $NodeDir"
}

$env:Path = "$NodeDir;" + $env:Path

$envLocal = Join-Path $Frontend ".env.local"
$envExample = Join-Path $Frontend ".env.local.example"
if (-not (Test-Path $envLocal) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envLocal
}

Set-Location $Frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies (first run may take a few minutes)..."
    & $NpmCmd install
}

Write-Host "Starting Next.js at http://localhost:3000 (API: http://127.0.0.1:8000)"
& $NpmCmd run dev

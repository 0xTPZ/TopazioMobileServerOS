[CmdletBinding()]
param(
    [switch]$SmokeKey
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$wslDistro = 'Ubuntu-24.04'

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL não encontrado. Instale uma distribuição Linux e execute novamente.'
}

$linuxRepo = (wsl.exe -d $wslDistro -- wslpath -a ($repo -replace '\\','/')).Trim()
if ($SmokeKey) {
    wsl.exe -d $wslDistro -- bash -lc "'$linuxRepo/scripts/smoke-qemu.sh'"
} else {
    wsl.exe -d $wslDistro -- bash -lc "'$linuxRepo/scripts/build-arm64.sh'"
}
if ($LASTEXITCODE -ne 0) { throw "Build WSL falhou com código $LASTEXITCODE" }

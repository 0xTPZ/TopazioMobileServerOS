[CmdletBinding()]
param(
    [string]$Source = '/root/topazio-sea-source'
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL não encontrado. Este build é somente para pesquisa no PC.'
}

$linuxRepo = (wsl.exe wslpath -a ($repo -replace '\','/')).Trim()
$envLine = "TOPAZIO_SEA_KERNEL_SOURCE='$Source' TOPAZIO_SEA_KERNEL_OUTPUT='$linuxRepo/build/out/sea-kernel'"
wsl.exe bash -lc "$envLine '$linuxRepo/scripts/build-sea-kernel.sh'"
if ($LASTEXITCODE -ne 0) { throw "Build sea bloqueado; consulte build/out/sea-kernel/manifest.json e build.log" }

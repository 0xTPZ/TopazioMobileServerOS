[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (wsl.exe -d Ubuntu-24.04 -- wslpath -a ($repo -replace '\\','/')).Trim()
wsl.exe -d Ubuntu-24.04 -- bash -lc "'$linuxRepo/scripts/run-qemu.sh'"
if ($LASTEXITCODE -ne 0) { throw "QEMU falhou com código $LASTEXITCODE" }

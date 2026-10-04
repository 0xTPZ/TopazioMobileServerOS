[CmdletBinding()]
param(
    [switch]$Qemu
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repo
try {
    python host-tools/verify_repo.py
    python host-tools/secret_scan.py --working-tree
    python -m unittest discover -s tests -v
    if (Test-Path 'build/out/arm64/manifests/topazio-arm64.json') {
        python host-tools/validate_arm64_artifact.py build/out/arm64
    }
    git diff --check
    if ($Qemu) {
        & (Join-Path $PSScriptRoot 'build.ps1') -SmokeKey
        if ($LASTEXITCODE -ne 0) { throw "QEMU smoke test falhou" }
    }
} finally {
    Pop-Location
}

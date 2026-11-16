# Install this skill into the DeepSeek Harness profile skills directory.
# ASCII-only on purpose: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI.

param(
    [string]$Dest = (Join-Path $env:USERPROFILE '.dsh\skills')
)

$ErrorActionPreference = 'Stop'
$src    = $PSScriptRoot
$target = Join-Path $Dest 'experiment-discipline'

if (-not (Test-Path (Join-Path $src 'SKILL.md'))) { throw "SKILL.md not found next to this script" }

New-Item -ItemType Directory -Force -Path (Join-Path $target 'scripts') | Out-Null
Copy-Item (Join-Path $src 'SKILL.md')             (Join-Path $target 'SKILL.md')            -Force
Copy-Item (Join-Path $src 'scripts\sigma_gate.py') (Join-Path $target 'scripts\sigma_gate.py') -Force
foreach ($f in 'README.md','CHANGELOG.md','LICENSE') {
    if (Test-Path (Join-Path $src $f)) { Copy-Item (Join-Path $src $f) (Join-Path $target $f) -Force }
}

# verify: the installed copy must be byte-identical, or the next reader gets a different skill
$bad = 0
foreach ($rel in 'SKILL.md','scripts\sigma_gate.py') {
    $a = (Get-FileHash (Join-Path $src $rel)).Hash
    $b = (Get-FileHash (Join-Path $target $rel)).Hash
    if ($a -ne $b) { Write-Host ("  MISMATCH after install: " + $rel); $bad++ }
}
if ($bad -gt 0) { exit 1 }

Write-Host ("  installed -> " + $target)
Write-Host '  selftest:'
& python (Join-Path $target 'scripts\sigma_gate.py') --selftest
exit $LASTEXITCODE

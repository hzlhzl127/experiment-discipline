# Self-check for the experiment-discipline skill: selftest + CLI smoke tests + drift check.
# Usage: powershell -ExecutionPolicy Bypass -File test.ps1
# ASCII-only on purpose: Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI.

$ErrorActionPreference = 'Continue'
$src  = $PSScriptRoot
$fail = @(); $ok = @()
$py   = 'python'
$gate = Join-Path $src 'scripts\sigma_gate.py'

if (-not (Test-Path $gate)) { Write-Host '  FAIL: scripts\sigma_gate.py missing'; exit 1 }

# 1. the four selftest cases
$out = & $py $gate --selftest 2>&1 | Out-String
if ($out -match 'SELFTEST: PASS') { $ok += 'selftest A/B/C/D pass' } else { $fail += 'selftest did not print SELFTEST: PASS' }
foreach ($c in 'A ','B ','C ','D ') {
    if ($out -notmatch [regex]::Escape($c) -or $out -notmatch ('(?m)^\s+' + [regex]::Escape($c) + '.*PASS')) {
        $fail += ("selftest case " + $c.Trim() + " did not report PASS")
    }
}

# 2. power smoke test: the numbers quoted in SKILL.md section 1 must come back
$p = & $py $gate --power 0.26 --sigma 0.16 2>&1 | Out-String
if ($p -match 'round up to 4 seed pairs') { $ok += 'power: sigma 0.16 -> 4 pairs (as documented)' }
else { $fail += 'power smoke: expected 4 seed pairs at sigma=0.16' }
$p2 = & $py $gate --power 0.26 --sigma 0.5 2>&1 | Out-String
if ($p2 -match 'round up to 30 seed pairs') { $ok += 'power: sigma 0.5 -> 30 pairs (as documented)' }
else { $fail += 'power smoke: expected 30 seed pairs at sigma=0.5' }

# 3. degenerate inputs must be refused, not crashed on
& $py $gate --power 0 --sigma 0.16 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { $fail += 'zero effect was not refused' } else { $ok += 'zero effect refused' }

# 4. the installed copy must match this one
$inst = Join-Path $env:USERPROFILE '.dsh\skills\experiment-discipline\SKILL.md'
if (Test-Path $inst) {
    if ((Get-FileHash (Join-Path $src 'SKILL.md')).Hash -ne (Get-FileHash $inst).Hash) {
        $fail += 'installed SKILL.md differs from this copy -- run install.ps1'
    } else { $ok += 'installed copy matches' }
} else { $ok += 'not installed here (skipped drift check)' }

Write-Host ''
foreach ($l in $ok)   { Write-Host ("  [OK]   " + $l) }
foreach ($l in $fail) { Write-Host ("  [FAIL] " + $l) }
Write-Host ''
if ($fail.Count -eq 0) { Write-Host '  VERDICT: PASS'; exit 0 }
Write-Host '  VERDICT: FAIL'
exit 1

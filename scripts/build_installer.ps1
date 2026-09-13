param(
    [string]$PythonPath = "python",
    [string]$InnoSetupPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot "build_release.ps1") -PythonPath $PythonPath
if ($LASTEXITCODE -ne 0) { throw "Application build failed" }

if (-not $InnoSetupPath) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $InnoSetupPath = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $InnoSetupPath -or -not (Test-Path -LiteralPath $InnoSetupPath)) {
    throw "Inno Setup 6 was not found. Install JRSoftware.InnoSetup or pass -InnoSetupPath."
}

Push-Location $projectRoot
try {
    & $InnoSetupPath "packaging\installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Installer build failed" }
    Write-Host "Installer build completed"
}
finally {
    Pop-Location
}

param(
    [string]$PythonPath = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & $PythonPath -m pytest -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw "测试失败" }

    & $PythonPath -m PyInstaller --noconfirm --clean "packaging\audit_tools_bundle.spec"
    if ($LASTEXITCODE -ne 0) { throw "构建失败" }

    Write-Host "构建完成：dist\审计工具箱\审计工具箱.exe"
}
finally {
    Pop-Location
}


param(
    [string]$InstallerPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $InstallerPath) {
    $installerFiles = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot "dist\installer") -Filter "*.exe" -File)
    if ($installerFiles.Count -ne 1) {
        throw "Expected exactly one installer executable, found $($installerFiles.Count)"
    }
    $InstallerPath = $installerFiles[0].FullName
}
$InstallerPath = [IO.Path]::GetFullPath($InstallerPath)
if (-not (Test-Path -LiteralPath $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}

$tempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
$installDir = Join-Path $env:TEMP ("FlightInspectionToolsInstallerSmoke-" + [guid]::NewGuid().ToString("N"))
$installDir = [IO.Path]::GetFullPath($installDir)
if (-not $installDir.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Smoke-test install directory is outside the system temp directory: $installDir"
}

try {
    $installer = Start-Process -FilePath $InstallerPath -ArgumentList @(
        "/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS", "/DIR=$installDir"
    ) -WindowStyle Hidden -Wait -PassThru
    if ($installer.ExitCode -ne 0) { throw "Silent install failed with exit code $($installer.ExitCode)" }

    $appFiles = @(Get-ChildItem -LiteralPath $installDir -Filter "*.exe" -File | Where-Object { $_.Name -ne "unins000.exe" })
    if ($appFiles.Count -ne 1) { throw "Expected exactly one installed application executable, found $($appFiles.Count)" }
    $appPath = $appFiles[0].FullName

    $worker = Start-Process -FilePath $appPath -ArgumentList "--worker-smoke" -WorkingDirectory $installDir -WindowStyle Hidden -Wait -PassThru
    if ($worker.ExitCode -ne 0) { throw "Installed worker smoke test failed with exit code $($worker.ExitCode)" }

    $gui = Start-Process -FilePath $appPath -WorkingDirectory $installDir -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 3
    if ($gui.HasExited) { throw "Installed GUI exited early with exit code $($gui.ExitCode)" }
    Stop-Process -Id $gui.Id
    $gui.WaitForExit()

    $uninstallerPath = Join-Path $installDir "unins000.exe"
    if (-not (Test-Path -LiteralPath $uninstallerPath)) { throw "Uninstaller not found" }
    $uninstaller = Start-Process -FilePath $uninstallerPath -ArgumentList @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"
    ) -WindowStyle Hidden -Wait -PassThru
    if ($uninstaller.ExitCode -ne 0) { throw "Silent uninstall failed with exit code $($uninstaller.ExitCode)" }
    Write-Host "Installer, worker, GUI, and uninstaller smoke tests passed"
}
finally {
    if (Test-Path -LiteralPath $installDir) {
        Remove-Item -LiteralPath $installDir -Recurse -Force
    }
}

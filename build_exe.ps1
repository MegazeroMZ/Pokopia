# Build a single-file executable for Pokopia on Windows using PyInstaller
# Usage: Run this from PowerShell in the repository root
#   .\build_exe.ps1

param(
    [string]$entry = 'app.py',
    [string]$name = 'Pokopia',
    [switch]$onefile = $true
)

Write-Host "Building $entry -> $name.exe"

# Ensure pip is available for the active Python
$py = "python"

# Install pyinstaller if missing
Write-Host "Installing pyinstaller (if missing)"
& $py -m pip install --upgrade pip
& $py -m pip install pyinstaller

# Build
# Include the CSV file as data so it is available when bundled.
$csv = 'Pokopia.csv'
# Build the --add-data option safely by concatenating strings to avoid
# confusing nested quotes/variable expansion in PowerShell.
$csvOpt = '--add-data "' + $csv + ';."'
$opts = "-w --noconfirm --name $name $csvOpt"
if ($onefile) { $opts += ' --onefile' }
$cmd = "pyinstaller $opts $entry"
Write-Host "Running: $cmd"
Invoke-Expression $cmd

Write-Host "Build complete. Output in dist\$name"

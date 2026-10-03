# Reads battery-related BIOS settings via HP's WMI interface
# (root\hp\instrumentedbios, HP_BIOSSetting). Requires elevation -
# run via read_bios_battery_mode.bat which triggers a UAC prompt.
# Writes config\hp_bios.local.json for the app to display (gitignored).

$ErrorActionPreference = "Stop"
$out = Join-Path $PSScriptRoot "..\config\hp_bios.local.json"

try {
    $settings = Get-WmiObject -Namespace "root\hp\instrumentedbios" -Class HP_BIOSSetting
} catch {
    Write-Host "HP WMI query failed: $($_.Exception.Message)"
    Write-Host "The HP BIOS WMI provider requires administrator rights and HP firmware support."
    exit 1
}

$battery = $settings | Where-Object { $_.Name -match "batter|charg|power|adaptive" }
$battery | ForEach-Object { Write-Host ("{0} = {1}" -f $_.Name, $_.CurrentValue) }

# Known mode names on HP business notebooks:
#   "Battery Health Manager"  (values: Maximize my battery duration /
#                             Let HP manage my battery /
#                             Maximize my battery health)
#   "Battery Care Function" / "Adaptive Battery Optimizer" (other models)
$modeSetting = $battery |
    Where-Object { $_.Name -match "Battery Health Manager|Battery Care" } |
    Select-Object -First 1

$result = [pscustomobject]@{
    mode        = if ($modeSetting) { $modeSetting.CurrentValue } else { $null }
    setting     = if ($modeSetting) { $modeSetting.Name } else { $null }
    all_battery = @($battery | ForEach-Object { "$($_.Name)=$($_.CurrentValue)" })
    updated     = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    source      = "root\hp\instrumentedbios HP_BIOSSetting"
}
$result | ConvertTo-Json | Set-Content -Path $out -Encoding UTF8
Write-Host ""
Write-Host "Wrote $out"
if (-not $modeSetting) {
    Write-Host "No Battery Health Manager setting found - this BIOS may not expose it via WMI."
}

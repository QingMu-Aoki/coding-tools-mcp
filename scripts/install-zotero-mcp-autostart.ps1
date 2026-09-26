param(
    [string]$TaskName = "Zotero MCP Local",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "start-zotero-mcp-background.ps1"
$launcher = (Resolve-Path $launcher).Path

[Environment]::SetEnvironmentVariable("ZOTERO_LOCAL", "true", "User")
[Environment]::SetEnvironmentVariable(
    "ZOTERO_MCP_URL",
    "http://127.0.0.1:$Port/mcp",
    "User"
)

$powerShell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`" -Port $Port"
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Start local Zotero MCP for the ChatGPT Coding Tool bridge." `
    -Force | Out-Null

Write-Host "Configured user environment and scheduled task: $TaskName"
Write-Host "ZOTERO_LOCAL=true"
Write-Host "ZOTERO_MCP_URL=http://127.0.0.1:$Port/mcp"

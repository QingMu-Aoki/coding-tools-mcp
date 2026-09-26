param(
    [string]$ZoteroMcpPath = (Join-Path $PSScriptRoot "..\..\zotero-mcp-main"),
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path $ZoteroMcpPath).Path
$env:ZOTERO_LOCAL = "true"
$env:ZOTERO_MCP_URL = "http://127.0.0.1:$Port/mcp"

function Test-LocalPort([int]$TargetPort) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $async = $client.BeginConnect("127.0.0.1", $TargetPort, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(500)) { return $false }
        $client.EndConnect($async)
        return $true
    }
    catch { return $false }
    finally { $client.Dispose() }
}
if (Test-LocalPort $Port) {
    exit 0
}

$logDir = Join-Path $env:LOCALAPPDATA "zotero-mcp-bridge"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "zotero-mcp.log"

Push-Location $resolved
try {
    "[$(Get-Date -Format s)] Starting Zotero MCP on port $Port" | Add-Content -Path $logFile
    & uv run zotero-mcp serve --transport streamable-http --host 127.0.0.1 --port $Port *>> $logFile
}
catch {
    "[$(Get-Date -Format s)] ERROR: $($_.Exception.Message)" | Add-Content -Path $logFile
    throw
}
finally {
    Pop-Location
}

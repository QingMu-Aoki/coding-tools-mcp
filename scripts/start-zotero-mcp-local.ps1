param(
    [string]$ZoteroMcpPath = (Join-Path $PSScriptRoot "..\..\zotero-mcp-main"),
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path $ZoteroMcpPath).Path
$env:ZOTERO_LOCAL = "true"

Write-Host "Starting Zotero MCP from $resolved"
Write-Host "Endpoint: http://127.0.0.1:$Port/mcp"
Push-Location $resolved
try {
    uv run zotero-mcp serve --transport streamable-http --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}

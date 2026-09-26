# Zotero Bridge

This fork can expose selected `54yyyu/zotero-mcp` capabilities through the existing
`coding-tools-mcp` endpoint. ChatGPT connects only to `coding-tools-mcp`; Zotero MCP
stays on localhost and does not need its own public tunnel.

## Architecture

```text
ChatGPT
  -> coding-tools-mcp (existing OAuth / remote endpoint)
  -> localhost Zotero bridge
  -> http://127.0.0.1:8000/mcp
  -> 54yyyu/zotero-mcp
  -> Zotero Desktop
```

The downstream URL defaults to `http://127.0.0.1:8000/mcp` and can be changed with
`CODING_TOOLS_MCP_ZOTERO_MCP_URL` or `ZOTERO_MCP_URL`.

## Available bridge tools

- `zotero_search`
- `zotero_get_collections`
- `zotero_get_collection_items`
- `zotero_get_item`
- `zotero_get_fulltext`
- `zotero_get_annotations`
- `zotero_set_item_collections`
- `zotero_write_status`
- `zotero_authorize_writes`

## Start the downstream Zotero MCP

From the sibling `zotero-mcp-main` checkout:

```powershell
$env:ZOTERO_LOCAL = "true"
uv run zotero-mcp serve --transport streamable-http --host 127.0.0.1 --port 8000
```

Keep Zotero Desktop running. The bridge performs a normal MCP initialize handshake,
keeps the returned session id, and retries once with a fresh session if the downstream
server restarts.

## Use from ChatGPT

After restarting the modified `coding-tools-mcp`, the new tools appear beside its
existing file/terminal/Git tools. Typical requests are:

- "List my Zotero collections."
- "Search Zotero for platelet migration."
- "Show the first 20 items in Platelet Chemotaxis."
- "Read the full text for item ABCD1234."
- "Add items ABCD1234 and EFGH5678 to collection X."

Write operations still depend on the write authorization configured by `zotero-mcp`.

## Security notes

Keep the Zotero MCP listener bound to `127.0.0.1`. Do not expose port 8000 directly
through Cloudflare/ngrok. The existing authenticated `coding-tools-mcp` endpoint remains
the only remote entry point.

The bridge URL is process configuration, not a model argument, so ChatGPT cannot choose
an arbitrary downstream host per tool call. Read tools are annotated read-only; collection
membership changes are annotated mutating/destructive.

## Scope

This first version intentionally exposes a small Zotero surface. It does not yet expose
semantic search administration, duplicate merging, Scite, collection creation/deletion,
metadata editing, note editing, or arbitrary downstream tool forwarding. Add those as
explicit bridge tools later instead of exposing the complete Zotero MCP tool catalog.

## Windows persistent/autostart setup

Run once:

```powershell
.\scripts\install-zotero-mcp-autostart.ps1
```

This stores these user-level variables permanently:

```text
ZOTERO_LOCAL=true
ZOTERO_MCP_URL=http://127.0.0.1:8000/mcp
```

It also creates the per-user scheduled task `Zotero MCP Local`, triggered at Windows logon.
The background launcher exits cleanly when port 8000 is already listening, so manually
starting Zotero MCP and the scheduled task do not create duplicate servers.

Logs for automatic starts are written to `%LOCALAPPDATA%\zotero-mcp-bridge\zotero-mcp.log`.

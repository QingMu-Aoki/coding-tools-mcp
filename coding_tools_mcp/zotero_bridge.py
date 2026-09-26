from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from typing import Any

from .envutils import ENV_PREFIX

DEFAULT_URL = "http://127.0.0.1:8000/mcp"


class ZoteroBridgeError(RuntimeError):
    pass


class ZoteroMcpBridge:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._session_id: str | None = None
        self._next_id = 1

    @property
    def url(self) -> str:
        return (
            os.environ.get(f"{ENV_PREFIX}_ZOTERO_MCP_URL")
            or os.environ.get("ZOTERO_MCP_URL")
            or DEFAULT_URL
        ).strip()

    def _id(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value

    @staticmethod
    def _decode(body: str, content_type: str) -> dict[str, Any] | None:
        body = body.strip()
        if not body:
            return None
        if "text/event-stream" not in content_type.lower():
            obj = json.loads(body)
            return obj if isinstance(obj, dict) else None
        messages: list[dict[str, Any]] = []
        body = body.replace("\r\n", "\n").replace("\r", "\n")
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    obj = json.loads(payload)
                    if isinstance(obj, dict):
                        messages.append(obj)
        return messages[-1] if messages else None

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload, separators=(",", ":")).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                self._session_id = response.headers.get("mcp-session-id") or self._session_id
                return self._decode(
                    response.read().decode("utf-8", errors="replace"),
                    response.headers.get("content-type", ""),
                )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ZoteroBridgeError(f"Zotero MCP HTTP {exc.code}: {detail or exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise ZoteroBridgeError(f"Cannot reach Zotero MCP at {self.url}: {exc.reason}") from exc

    def _initialize(self) -> None:
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "coding-tools-zotero-bridge", "version": "0.1"},
                },
            }
        )
        if not response or "result" not in response:
            raise ZoteroBridgeError(f"Zotero MCP initialize failed: {response!r}")
        self._post(
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        )

    @staticmethod
    def _text(result: dict[str, Any]) -> str:
        blocks = result.get("content")
        if not isinstance(blocks, list):
            return json.dumps(result, ensure_ascii=False)
        parts: list[str] = []
        for block in blocks:
            if (
                isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ):
                parts.append(block["text"])
        return "\n".join(parts) if parts else json.dumps(result, ensure_ascii=False)

    def call(self, tool: str, arguments: dict[str, Any] | None = None) -> str:
        with self._lock:
            if self._session_id is None:
                self._initialize()
            payload = {
                "jsonrpc": "2.0",
                "id": self._id(),
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments or {}},
            }
            try:
                response = self._post(payload)
            except ZoteroBridgeError:
                self._session_id = None
                self._initialize()
                response = self._post(payload)
            if not response:
                raise ZoteroBridgeError(f"No response from Zotero MCP for {tool}")
            if isinstance(response.get("error"), dict):
                error = response["error"]
                raise ZoteroBridgeError(str(error.get("message") or error))
            result = response.get("result")
            if not isinstance(result, dict):
                raise ZoteroBridgeError(f"Malformed Zotero MCP response: {response!r}")
            if result.get("isError"):
                raise ZoteroBridgeError(self._text(result))
            return self._text(result)


bridge = ZoteroMcpBridge()

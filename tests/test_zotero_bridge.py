from __future__ import annotations

import unittest

from coding_tools_mcp.zotero_bridge import ZoteroMcpBridge


class ZoteroBridgeTests(unittest.TestCase):
    def test_decode_streamable_http_sse(self) -> None:
        body = (
            "event: message\r\n"
            'data: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\r\n\r\n'
        )
        decoded = ZoteroMcpBridge._decode(body, "text/event-stream")
        self.assertEqual(decoded["id"], 1)
        self.assertTrue(decoded["result"]["ok"])

    def test_call_initializes_and_returns_text(self) -> None:
        class FakeBridge(ZoteroMcpBridge):
            def __init__(self) -> None:
                super().__init__()
                self.methods = []

            def _post(self, payload):
                method = payload["method"]
                self.methods.append(method)
                if method == "initialize":
                    self._session_id = "fake-session"
                    return {"jsonrpc": "2.0", "id": payload["id"], "result": {}}
                if method == "notifications/initialized":
                    return None
                return {
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {
                        "content": [{"type": "text", "text": "bridge ok"}],
                        "isError": False,
                    },
                }

        bridge = FakeBridge()
        text = bridge.call("zotero_get_collections", {"limit": 2})
        self.assertEqual(text, "bridge ok")
        self.assertEqual(
            bridge.methods,
            ["initialize", "notifications/initialized", "tools/call"],
        )


if __name__ == "__main__":
    unittest.main()

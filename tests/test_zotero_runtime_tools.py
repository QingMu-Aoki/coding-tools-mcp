from __future__ import annotations

import unittest

from coding_tools_mcp.server import Runtime


class DummyRuntime(Runtime):
    def _zotero_call(self, downstream_tool, args):
        self.last_call = (downstream_tool, args)
        return {"ok": True, "summary": "ok", "downstream_tool": downstream_tool}


class ZoteroRuntimeToolTests(unittest.TestCase):
    def setUp(self):
        self.runtime = object.__new__(DummyRuntime)
        self.runtime.last_call = None

    def test_update_item_passthrough(self):
        args = {"item_key": "ABC12345", "fields": {"title": "New"}, "add_tags": ["reviewed"]}
        self.runtime.zotero_update_item(args)
        self.assertEqual(self.runtime.last_call, ("zotero_update_item", args))

    def test_get_notes_passthrough(self):
        args = {"item_key": "ABC12345", "raw_html": True}
        self.runtime.zotero_get_notes(args)
        self.assertEqual(self.runtime.last_call, ("zotero_get_notes", args))

    def test_create_note_maps_action(self):
        args = {"item_key": "ABC12345", "note_text": "hello", "note_title": "Title"}
        self.runtime.zotero_create_note(args)
        self.assertEqual(
            self.runtime.last_call,
            ("zotero_manage_note", {"action": "create", **args}),
        )

    def test_update_note_maps_note_key(self):
        self.runtime.zotero_update_note({"note_key": "NOTE1234", "note_text": "changed", "append": False})
        self.assertEqual(
            self.runtime.last_call,
            (
                "zotero_manage_note",
                {"action": "update", "item_key": "NOTE1234", "note_text": "changed", "append": False},
            ),
        )

    def test_delete_note_maps_note_key(self):
        self.runtime.zotero_delete_note({"note_key": "NOTE1234"})
        self.assertEqual(
            self.runtime.last_call,
            ("zotero_manage_note", {"action": "delete", "item_key": "NOTE1234"}),
        )


if __name__ == "__main__":
    unittest.main()

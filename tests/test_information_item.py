import unittest

from ai_os.cognition.context import InformationItem


class InformationItemTests(unittest.TestCase):
    def test_create_text_item(self):
        item = InformationItem(
            item_id="memory:123",
            content="Random Forest was selected.",
            source="memory",
        )
        self.assertEqual(item.item_id, "memory:123")
        self.assertEqual(item.content, "Random Forest was selected.")
        self.assertEqual(item.source, "memory")
        self.assertIsNone(item.relevance)

    def test_structured_content(self):
        item = InformationItem(
            item_id="document:456",
            content={"title": "AI-OS", "tags": ["architecture", "runtime"]},
            source="knowledge",
            provenance={"document_id": "456", "page": 17},
        )
        self.assertEqual(item.content["title"], "AI-OS")
        self.assertEqual(item.provenance["page"], 17)

    def test_relevance_is_validated(self):
        item = InformationItem("doc:1", "result", "knowledge", relevance=0.92)
        self.assertEqual(item.relevance, 0.92)
        with self.assertRaises(ValueError):
            InformationItem("doc:2", "bad", "knowledge", relevance=-0.1)
        with self.assertRaises(ValueError):
            InformationItem("doc:3", "bad", "knowledge", relevance=1.1)

    def test_immutability(self):
        item = InformationItem(
            "memory:1", {"value": 10}, "memory", metadata={"source": "test"}
        )
        with self.assertRaises((AttributeError, TypeError)):
            item.source = "knowledge"
        with self.assertRaises(TypeError):
            item.content["value"] = 20
        with self.assertRaises(TypeError):
            item.metadata["source"] = "changed"

    def test_invalid_content_is_rejected(self):
        with self.assertRaises(TypeError):
            InformationItem("memory:1", {"bad": object()}, "memory")

    def test_invalid_relevance_is_rejected(self):
        with self.assertRaises(TypeError):
            InformationItem("memory:1", "value", "memory", relevance="high")

    def test_invalid_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            InformationItem("", "value", "memory")
        with self.assertRaises(ValueError):
            InformationItem("memory:1", "value", "")

    def test_round_trip(self):
        item = InformationItem(
            item_id="document:456",
            content={"answer": "yes", "score": 3},
            source="knowledge",
            relevance=0.87,
            provenance={"document_id": "456", "page": 4},
            metadata={"rank": 2},
        )
        restored = InformationItem.from_json(item.to_json())
        self.assertEqual(restored.to_dict(), item.to_dict())


if __name__ == "__main__":
    unittest.main(verbosity=2)

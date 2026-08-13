import unittest

from ai_os.cognition.context import InformationItem
from ai_os.cognition.knowledge import KnowledgeSource


class TestKnowledgeSource:
    def query(self, query, *, limit=10, filters=None):
        return (
            InformationItem(
                item_id="document:1",
                content="Random Forest uses multiple decision trees.",
                source="knowledge",
                provenance={"document_id": "1"},
            ),
        )[:limit]


class KnowledgeSourceTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        source = TestKnowledgeSource()

        self.assertIsInstance(source, KnowledgeSource)

    def test_query_returns_information_items(self):
        source = TestKnowledgeSource()

        results = source.query("random forest")

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], InformationItem)

    def test_query_respects_limit(self):
        class MultipleKnowledgeSource:
            def query(self, query, *, limit=10, filters=None):
                items = tuple(
                    InformationItem(
                        item_id=f"document:{i}",
                        content=f"Document {i}",
                        source="knowledge",
                    )
                    for i in range(5)
                )
                return items[:limit]

        source = MultipleKnowledgeSource()

        results = source.query("document", limit=2)

        self.assertEqual(len(results), 2)

    def test_knowledge_source_has_no_required_write_operation(self):
        source = TestKnowledgeSource()

        self.assertFalse(hasattr(source, "retain"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
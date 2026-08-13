import unittest

from ai_os.cognition.context import InformationItem
from ai_os.cognition.retrieval import Retriever


class TestRetriever:
    def query(self, query, *, limit=10, filters=None):
        items = (
            InformationItem(
                item_id="memory:1",
                content="Random Forest was selected.",
                source="memory",
                relevance=0.95,
            ),
            InformationItem(
                item_id="document:1",
                content="Random Forest uses multiple trees.",
                source="knowledge",
                relevance=0.87,
            ),
        )

        return items[:limit]


class RetrieverTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        retriever = TestRetriever()

        self.assertIsInstance(retriever, Retriever)

    def test_query_returns_information_items(self):
        retriever = TestRetriever()

        results = retriever.query("random forest")

        self.assertEqual(len(results), 2)

        for item in results:
            self.assertIsInstance(item, InformationItem)

    def test_query_respects_limit(self):
        retriever = TestRetriever()

        results = retriever.query(
            "random forest",
            limit=1,
        )

        self.assertEqual(len(results), 1)

    def test_retrieval_does_not_require_storage_operation(self):
        retriever = TestRetriever()

        self.assertFalse(hasattr(retriever, "retain"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
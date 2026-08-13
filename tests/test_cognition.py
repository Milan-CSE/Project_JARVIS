import unittest

from ai_os.cognition import Cognition
from ai_os.cognition.context import (
    Context,
    ContextRequest,
    InformationItem,
)


class TestRetriever:
    def __init__(self):
        self.last_query = None
        self.last_limit = None
        self.last_filters = None

    def query(self, query, *, limit=10, filters=None):
        self.last_query = query
        self.last_limit = limit
        self.last_filters = filters

        return (
            InformationItem(
                item_id="memory:1",
                content="Random Forest was selected.",
                source="memory",
                relevance=0.95,
            ),
            InformationItem(
                item_id="knowledge:1",
                content="Random Forest uses multiple trees.",
                source="knowledge",
                relevance=0.90,
            ),
        )[:limit]


class CognitionTests(unittest.TestCase):

    def test_cognition_accepts_retriever(self):
        retriever = TestRetriever()

        cognition = Cognition(retriever)

        self.assertIsInstance(cognition, Cognition)

    def test_get_context_returns_context(self):
        cognition = Cognition(TestRetriever())

        request = ContextRequest(
            query="random forest",
            max_items=2,
        )

        context = cognition.get_context(request)

        self.assertIsInstance(context, Context)
        self.assertEqual(context.query, "random forest")
        self.assertEqual(len(context.items), 2)

    def test_request_is_forwarded_to_retriever(self):
        retriever = TestRetriever()
        cognition = Cognition(retriever)

        request = ContextRequest(
            query="project decision",
            max_items=5,
            filters={"source": "memory"},
        )

        cognition.get_context(request)

        self.assertEqual(
            retriever.last_query,
            "project decision",
        )
        self.assertEqual(
            retriever.last_limit,
            5,
        )
        self.assertEqual(
            dict(retriever.last_filters),
            {"source": "memory"},
        )

    def test_context_contains_information_items(self):
        cognition = Cognition(TestRetriever())

        request = ContextRequest(
            query="random forest",
            max_items=1,
        )

        context = cognition.get_context(request)

        self.assertEqual(len(context.items), 1)
        self.assertIsInstance(
            context.items[0],
            InformationItem,
        )

    def test_request_metadata_becomes_context_metadata(self):
        cognition = Cognition(TestRetriever())

        request = ContextRequest(
            query="test",
            metadata={"trace_id": "abc123"},
        )

        context = cognition.get_context(request)

        self.assertEqual(
            context.metadata["trace_id"],
            "abc123",
        )

    def test_invalid_request_is_rejected(self):
        cognition = Cognition(TestRetriever())

        with self.assertRaises(TypeError):
            cognition.get_context("not a ContextRequest")

    def test_invalid_retriever_is_rejected(self):
        with self.assertRaises(TypeError):
            Cognition(object())


if __name__ == "__main__":
    unittest.main(verbosity=2)
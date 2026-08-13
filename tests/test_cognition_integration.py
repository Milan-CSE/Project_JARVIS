import unittest

from ai_os.cognition import Cognition
from ai_os.cognition.context import (
    Context,
    ContextRequest,
    InformationItem,
)
from ai_os.cognition.memory import MemoryStore
from ai_os.cognition.knowledge import KnowledgeSource
from ai_os.cognition.retrieval import Retriever


class TestMemory:
    def __init__(self):
        self.items = []

    def query(self, query, *, limit=10, filters=None):
        results = self.items

        if filters and "source" in filters:
            results = [
                item
                for item in results
                if item.source == filters["source"]
            ]

        return tuple(results[:limit])

    def retain(self, item):
        self.items.append(item)


class TestKnowledge:
    def __init__(self):
        self.items = []

    def query(self, query, *, limit=10, filters=None):
        results = self.items

        if filters and "source" in filters:
            results = [
                item
                for item in results
                if item.source == filters["source"]
            ]

        return tuple(results[:limit])


class CombinedRetriever:
    def __init__(self, memory, knowledge):
        self.memory = memory
        self.knowledge = knowledge

    def query(self, query, *, limit=10, filters=None):
        memory_items = self.memory.query(
            query,
            limit=limit,
            filters=filters,
        )

        knowledge_items = self.knowledge.query(
            query,
            limit=limit,
            filters=filters,
        )

        return (memory_items + knowledge_items)[:limit]


class CognitionIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.memory = TestMemory()
        self.knowledge = TestKnowledge()

        self.memory.retain(
            InformationItem(
                item_id="memory:1",
                content="Random Forest was selected for the project.",
                source="memory",
                relevance=0.95,
                provenance={"memory_id": "1"},
            )
        )

        self.knowledge.items.append(
            InformationItem(
                item_id="document:1",
                content="Random Forest combines multiple decision trees.",
                source="knowledge",
                relevance=0.90,
                provenance={"document_id": "1"},
            )
        )

        retriever = CombinedRetriever(
            self.memory,
            self.knowledge,
        )

        self.cognition = Cognition(retriever)

    def test_full_information_flow(self):
        request = ContextRequest(
            query="random forest",
            max_items=10,
        )

        context = self.cognition.get_context(request)

        self.assertIsInstance(context, Context)
        self.assertEqual(context.query, "random forest")
        self.assertEqual(len(context.items), 2)

    def test_memory_information_reaches_context(self):
        request = ContextRequest(
            query="project decision",
            max_items=10,
            filters={"source": "memory"},
        )

        context = self.cognition.get_context(request)

        self.assertEqual(len(context.items), 1)
        self.assertEqual(
            context.items[0].item_id,
            "memory:1",
        )
        self.assertEqual(
            context.items[0].source,
            "memory",
        )

    def test_multiple_sources_reach_context(self):
        request = ContextRequest(
            query="random forest",
            max_items=10,
        )

        context = self.cognition.get_context(request)

        sources = {
            item.source
            for item in context.items
        }

        self.assertEqual(
            sources,
            {"memory", "knowledge"},
        )

    def test_information_provenance_is_preserved(self):
        request = ContextRequest(
            query="random forest",
            max_items=10,
        )

        context = self.cognition.get_context(request)

        memory_item = next(
            item
            for item in context.items
            if item.source == "memory"
        )

        knowledge_item = next(
            item
            for item in context.items
            if item.source == "knowledge"
        )

        self.assertEqual(
            memory_item.provenance["memory_id"],
            "1",
        )

        self.assertEqual(
            knowledge_item.provenance["document_id"],
            "1",
        )

    def test_limit_is_respected_end_to_end(self):
        request = ContextRequest(
            query="random forest",
            max_items=1,
        )

        context = self.cognition.get_context(request)

        self.assertEqual(len(context.items), 1)

    def test_no_information_returns_empty_context(self):
        request = ContextRequest(
            query="something completely unrelated",
            max_items=10,
        )

        context = self.cognition.get_context(request)

        # Test implementations return no matching filtering only for memory;
        # this scenario verifies the contract can represent no information.
        empty_retriever = CombinedRetriever(
            TestMemory(),
            TestKnowledge(),
        )

        empty_cognition = Cognition(empty_retriever)

        empty_context = empty_cognition.get_context(request)

        self.assertIsInstance(empty_context, Context)
        self.assertEqual(empty_context.items, ())

    def test_context_remains_serializable(self):
        request = ContextRequest(
            query="random forest",
            max_items=10,
        )

        context = self.cognition.get_context(request)

        restored = Context.from_json(
            context.to_json()
        )

        self.assertEqual(
            restored.to_dict(),
            context.to_dict(),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
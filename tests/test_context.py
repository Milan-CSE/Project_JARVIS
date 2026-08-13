import unittest

from ai_os.cognition.context import (
    InformationItem,
    ContextRequest,
    Context,
)


class ContextRequestTests(unittest.TestCase):

    def test_valid_request(self):
        request = ContextRequest(
            query="What did we decide?",
            max_items=5,
        )

        self.assertEqual(request.query, "What did we decide?")
        self.assertEqual(request.max_items, 5)

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            ContextRequest("")

    def test_invalid_max_items_rejected(self):
        with self.assertRaises(ValueError):
            ContextRequest("test", max_items=0)

        with self.assertRaises(TypeError):
            ContextRequest("test", max_items="5")

    def test_request_is_immutable(self):
        request = ContextRequest("test")

        with self.assertRaises(AttributeError):
            request.query = "changed"

    def test_request_round_trip(self):
        request = ContextRequest(
            query="test",
            max_items=10,
            filters={"source": "memory"},
            metadata={"trace_id": "abc"},
        )

        restored = ContextRequest.from_json(request.to_json())

        self.assertEqual(
            restored.to_dict(),
            request.to_dict(),
        )


class ContextTests(unittest.TestCase):

    def test_context_with_information_items(self):
        item = InformationItem(
            item_id="memory:1",
            content="Random Forest was selected.",
            source="memory",
        )

        context = Context(
            query="What did we decide?",
            items=(item,),
        )

        self.assertEqual(context.query, "What did we decide?")
        self.assertEqual(len(context.items), 1)
        self.assertEqual(context.items[0], item)

    def test_context_rejects_invalid_items(self):
        with self.assertRaises(TypeError):
            Context(
                query="test",
                items=("not an InformationItem",),
            )

    def test_context_is_immutable(self):
        item = InformationItem(
            item_id="memory:1",
            content="test",
            source="memory",
        )

        context = Context(
            query="test",
            items=(item,),
        )

        with self.assertRaises(AttributeError):
            context.query = "changed"

    def test_context_round_trip(self):
        item = InformationItem(
            item_id="document:1",
            content={"answer": "yes"},
            source="knowledge",
            relevance=0.9,
            provenance={"page": 5},
        )

        context = Context(
            query="What is the answer?",
            items=(item,),
            metadata={"trace_id": "abc"},
        )

        restored = Context.from_json(context.to_json())

        self.assertEqual(
            restored.to_dict(),
            context.to_dict(),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
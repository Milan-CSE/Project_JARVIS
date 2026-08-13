import unittest

from ai_os.intelligence.context import (
    ContextItem,
    ContextSource,
    IntelligenceContext,
)


class IntelligenceContextTests(unittest.TestCase):

    def test_context_item_creation(self):
        item = ContextItem(
            kind="customer",
            source=ContextSource.USER,
            value="Alice",
        )

        self.assertEqual(
            item.kind,
            "customer",
        )

        self.assertEqual(
            item.source,
            ContextSource.USER,
        )

        self.assertEqual(
            item.value,
            "Alice",
        )

    def test_context_item_accepts_source_value(self):
        item = ContextItem(
            kind="customer",
            source="user",
            value="Alice",
        )

        self.assertEqual(
            item.source,
            ContextSource.USER,
        )

    def test_context_item_rejects_empty_kind(self):
        with self.assertRaises(ValueError):
            ContextItem(
                kind="",
                source=ContextSource.USER,
                value="Alice",
            )

    def test_context_item_is_immutable(self):
        item = ContextItem(
            kind="customer",
            source=ContextSource.USER,
            value="Alice",
        )

        with self.assertRaises(AttributeError):
            item.kind = "changed"

    def test_context_preserves_provenance(self):
        memory_item = ContextItem(
            kind="fact",
            source=ContextSource.MEMORY,
            value="historical",
        )

        document_item = ContextItem(
            kind="fact",
            source=ContextSource.DOCUMENT,
            value="document",
        )

        context = IntelligenceContext(
            input="test",
            items=(
                memory_item,
                document_item,
            ),
        )

        self.assertEqual(
            context.items[0].source,
            ContextSource.MEMORY,
        )

        self.assertEqual(
            context.items[1].source,
            ContextSource.DOCUMENT,
        )

    def test_context_items_are_immutable_tuple(self):
        item = ContextItem(
            kind="fact",
            source=ContextSource.USER,
            value="value",
        )

        context = IntelligenceContext(
            input="test",
            items=[item],
        )

        self.assertIsInstance(
            context.items,
            tuple,
        )

    def test_context_rejects_invalid_item(self):
        with self.assertRaises(TypeError):
            IntelligenceContext(
                input="test",
                items=("invalid",),
            )

    def test_nested_mapping_is_frozen(self):
        item = ContextItem(
            kind="profile",
            source=ContextSource.USER,
            value={
                "name": "Alice",
                "preferences": {
                    "language": "English",
                },
            },
        )

        with self.assertRaises(TypeError):
            item.value["name"] = "Bob"

        with self.assertRaises(TypeError):
            item.value["preferences"]["language"] = "Hindi"

    def test_nested_list_is_frozen(self):
        item = ContextItem(
            kind="tags",
            source=ContextSource.USER,
            value=[
                "a",
                "b",
            ],
        )

        self.assertIsInstance(
            item.value,
            tuple,
        )

        with self.assertRaises(AttributeError):
            item.value.append("c")

    def test_input_is_snapshot(self):
        original = {
            "user": {
                "name": "Alice",
            }
        }

        context = IntelligenceContext(
            input=original,
        )

        original["user"]["name"] = "Bob"

        self.assertEqual(
            context.input["user"]["name"],
            "Alice",
        )

    def test_context_metadata_is_immutable(self):
        context = IntelligenceContext(
            input="test",
            metadata={
                "request_source": "user",
            },
        )

        with self.assertRaises(TypeError):
            context.metadata["request_source"] = "system"

    def test_constraints_are_immutable(self):
        context = IntelligenceContext(
            input="test",
            constraints={
                "max_steps": 5,
            },
        )

        with self.assertRaises(TypeError):
            context.constraints["max_steps"] = 10

    def test_missing_optional_information_is_allowed(self):
        context = IntelligenceContext(
            input="test",
        )

        self.assertIsNone(
            context.identity,
        )

        self.assertEqual(
            context.items,
            (),
        )

    def test_context_is_immutable(self):
        context = IntelligenceContext(
            input="test",
        )

        with self.assertRaises(AttributeError):
            context.input = "changed"

    def test_context_does_not_contain_runtime_objects(self):
        context = IntelligenceContext(
            input="test",
        )

        self.assertFalse(
            hasattr(context, "scheduler")
        )

        self.assertFalse(
            hasattr(context, "task_executor")
        )

        self.assertFalse(
            hasattr(context, "task_registry")
        )

        self.assertFalse(
            hasattr(context, "runtime")
        )

    def test_context_does_not_contain_agent(self):
        context = IntelligenceContext(
            input="test",
        )

        self.assertFalse(
            hasattr(context, "agent")
        )

    def test_context_does_not_contain_model_provider(self):
        context = IntelligenceContext(
            input="test",
        )

        self.assertFalse(
            hasattr(context, "model")
        )

        self.assertFalse(
            hasattr(context, "provider")
        )

    def test_multiple_sources_can_coexist(self):
        context = IntelligenceContext(
            input="test",
            items=(
                ContextItem(
                    kind="request",
                    source=ContextSource.USER,
                    value="hello",
                ),
                ContextItem(
                    kind="policy",
                    source=ContextSource.SYSTEM,
                    value="safe",
                ),
                ContextItem(
                    kind="memory",
                    source=ContextSource.MEMORY,
                    value="previous fact",
                ),
                ContextItem(
                    kind="document",
                    source=ContextSource.DOCUMENT,
                    value="document fact",
                ),
                ContextItem(
                    kind="external",
                    source=ContextSource.EXTERNAL,
                    value="web fact",
                ),
                ContextItem(
                    kind="identity",
                    source=ContextSource.IDENTITY,
                    value="user-1",
                ),
            ),
        )

        self.assertEqual(
            len(context.items),
            6,
        )

    def test_context_is_per_instance(self):
        first = IntelligenceContext(
            input="first",
        )

        second = IntelligenceContext(
            input="second",
        )

        self.assertNotEqual(
            first.input,
            second.input,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
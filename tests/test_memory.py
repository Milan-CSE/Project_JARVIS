import unittest

from ai_os.cognition.context import InformationItem
from ai_os.cognition.memory import MemoryStore


class InMemoryTestStore:
    def __init__(self):
        self.items = []

    def query(self, query, *, limit=10, filters=None):
        return tuple(self.items[:limit])

    def retain(self, item):
        self.items.append(item)


class MemoryStoreTests(unittest.TestCase):

    def test_valid_implementation_matches_protocol(self):
        store = InMemoryTestStore()

        self.assertIsInstance(store, MemoryStore)

    def test_retain_accepts_information_item(self):
        store = InMemoryTestStore()

        item = InformationItem(
            item_id="memory:1",
            content="Random Forest was selected.",
            source="memory",
        )

        store.retain(item)

        self.assertEqual(len(store.items), 1)
        self.assertEqual(store.items[0], item)

    def test_query_returns_information_items(self):
        store = InMemoryTestStore()

        item = InformationItem(
            item_id="memory:1",
            content="Test memory",
            source="memory",
        )

        store.retain(item)

        results = store.query("test")

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], InformationItem)

    def test_query_respects_limit(self):
        store = InMemoryTestStore()

        for number in range(3):
            store.retain(
                InformationItem(
                    item_id=f"memory:{number}",
                    content=f"Memory {number}",
                    source="memory",
                )
            )

        results = store.query("memory", limit=2)

        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
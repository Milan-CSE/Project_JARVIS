import unittest

from ai_os.engines import EngineStatus, EngineType


class EngineTypesTests(unittest.TestCase):

    def test_engine_types(self):
        self.assertEqual(
            [item.value for item in EngineType],
            [
                "planning",
                "decision",
                "routing",
                "policy",
                "workflow",
            ],
        )

    def test_engine_statuses(self):
        self.assertEqual(
            [item.value for item in EngineStatus],
            [
                "success",
                "failed",
                "cancelled",
            ],
        )

    def test_engine_types_are_distinct(self):
        self.assertNotEqual(
            EngineType.PLANNING,
            EngineType.DECISION,
        )

    def test_engine_statuses_are_distinct(self):
        self.assertNotEqual(
            EngineStatus.SUCCESS,
            EngineStatus.FAILED,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
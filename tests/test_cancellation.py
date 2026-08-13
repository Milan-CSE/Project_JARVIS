import unittest

from ai_os.runtime.cancellation import (
    CancellationSource,
    CancellationToken,
)


class CancellationTests(unittest.TestCase):

    def test_new_source_is_not_cancelled(self):
        source = CancellationSource()

        self.assertFalse(
            source.token.is_cancelled
        )

    def test_cancel_changes_token_state(self):
        source = CancellationSource()

        source.cancel()

        self.assertTrue(
            source.token.is_cancelled
        )

    def test_repeated_cancel_is_idempotent(self):
        source = CancellationSource()

        source.cancel()
        source.cancel()
        source.cancel()

        self.assertTrue(
            source.token.is_cancelled
        )

    def test_token_matches_protocol(self):
        source = CancellationSource()

        self.assertIsInstance(
            source.token,
            CancellationToken,
        )

    def test_token_is_read_only(self):
        source = CancellationSource()

        with self.assertRaises(AttributeError):
            source.token.is_cancelled = True


if __name__ == "__main__":
    unittest.main(verbosity=2)
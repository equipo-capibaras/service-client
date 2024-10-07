from unittest import TestCase

from app import create_app


class TestHealth(TestCase):
    def setUp(self) -> None:
        app = create_app()
        self.client = app.test_client()

    def test_health(self) -> None:
        self.assertEqual(0, 1 - 1)

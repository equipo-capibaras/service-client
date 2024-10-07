from typing import cast
from unittest.mock import Mock

from unittest_parametrize import ParametrizedTestCase, parametrize

from app import create_app
from repositories import ClientRepository


class TestReset(ParametrizedTestCase):
    API_ENDPOINT = '/api/v1/reset/client'

    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.app.container.unwire()

    @parametrize(
        'arg,expected',
        [
            (None, False),
            ('true', True),
            ('false', False),
            ('foo', False),
        ],
    )
    def test_reset(self, arg: str | None, expected: bool) -> None:  # noqa: FBT001
        client_repo_mock = Mock(ClientRepository)
        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.client.post(self.API_ENDPOINT + (f'?demo={arg}' if arg is not None else ''))

        cast(Mock, client_repo_mock.reset).assert_called_once_with(load_demo_data=expected)

        self.assertEqual(resp.status_code, 200)

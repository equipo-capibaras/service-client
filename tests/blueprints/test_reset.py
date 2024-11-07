from typing import cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize

import demo
from app import create_app
from repositories import ClientRepository, EmployeeRepository


class TestReset(ParametrizedTestCase):
    API_ENDPOINT = '/api/v1/reset/client'

    def setUp(self) -> None:
        self.faker = Faker()

        self.domain = self.faker.domain_name()

        self.app = create_app()
        self.app.container.config.domain.override(self.domain)

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
        employee_repo_mock = Mock(EmployeeRepository)
        call_order = []

        cast(Mock, client_repo_mock.delete_all).side_effect = lambda: call_order.append('client:delete_all')
        cast(Mock, employee_repo_mock.delete_all).side_effect = lambda: call_order.append('employee:delete_all')
        cast(Mock, client_repo_mock.create).side_effect = lambda _x: call_order.append('client:create')
        cast(Mock, employee_repo_mock.create).side_effect = lambda _x: call_order.append('employee:create')

        with (
            self.app.container.client_repo.override(client_repo_mock),
            self.app.container.employee_repo.override(employee_repo_mock),
        ):
            resp = self.client.post(self.API_ENDPOINT + (f'?demo={arg}' if arg is not None else ''))

        cast(Mock, client_repo_mock.delete_all).assert_called_once()
        cast(Mock, employee_repo_mock.delete_all).assert_called_once()

        if not expected:
            self.assertEqual(call_order, ['employee:delete_all', 'client:delete_all'])
        else:
            self.assertEqual(
                call_order,
                ['employee:delete_all', 'client:delete_all']
                + ['client:create'] * len(demo.clients)
                + ['employee:create'] * len(demo.employees),
            )

        self.assertEqual(resp.status_code, 200)

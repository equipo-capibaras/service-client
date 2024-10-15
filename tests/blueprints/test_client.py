import base64
import json
from typing import cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Client, Plan, Role
from repositories import ClientRepository


class TestClient(ParametrizedTestCase):
    INFO_API_URL = '/api/v1/clients/me'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def gen_token(self, client_id: str, role: Role) -> dict[str, str]:
        return {
            'sub': cast(str, self.faker.uuid4()),
            'cid': client_id,
            'role': role.value,
            'aud': role.value,
        }

    def call_info_api(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.get(self.INFO_API_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(self.INFO_API_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def test_info_no_token(self) -> None:
        resp = self.call_info_api(None)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': 'Token is missing'})

    @parametrize(
        'missing_field',
        [
            ('sub',),
            ('cid',),
            ('role',),
            ('aud',),
        ],
    )
    def test_info_token_missing_fields(self, missing_field: str) -> None:
        token = self.gen_token(
            client_id=cast(str, self.faker.uuid4()),
            role=self.faker.random_element(list(Role)),
        )
        del token[missing_field]
        resp = self.call_info_api(token)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': f'{missing_field} is missing in token'})

    def test_list_clients(self) -> None:
        clients = [
            Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(list(Plan)),
                email_incidents=self.faker.unique.email(),
            )
            for _ in range(5)
        ]

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get_all).return_value = (c for c in clients)

        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.client.get('/api/v1/clients')

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(len(resp_data), len(clients))
        for i, client in enumerate(clients):
            self.assertEqual(resp_data[i]['id'], client.id)
            self.assertEqual(resp_data[i]['name'], client.name)
            self.assertEqual(resp_data[i]['emailIncidents'], client.email_incidents)
            self.assertNotIn('plan', resp_data[i])

    @parametrize(
        ('api_method', 'role', 'expect_plan'),
        [
            ('get', None, False),
            ('info', Role.ADMIN, True),
            ('info', Role.AGENT, False),
            ('info', Role.ANALYST, False),
        ],
    )
    def test_get_client_found(self, *, api_method: str, role: Role | None, expect_plan: bool) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = client

        with self.app.container.client_repo.override(client_repo_mock):
            if api_method == 'get':
                resp = self.client.get(f'/api/v1/clients/{client.id}')
            else:
                token = self.gen_token(client_id=client.id, role=cast(Role, role))
                resp = self.call_info_api(token)

        cast(Mock, client_repo_mock.get).assert_called_once_with(client.id)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], client.id)
        self.assertEqual(resp_data['name'], client.name)
        self.assertEqual(resp_data['emailIncidents'], client.email_incidents)
        if expect_plan:
            self.assertEqual(resp_data['plan'], client.plan.value)
        else:
            self.assertNotIn('plan', resp_data)

    @parametrize(
        ('api_method',),
        [
            ('get',),
            ('info',),
        ],
    )
    def test_get_client_missing(self, api_method: str) -> None:
        client_id = cast(str, self.faker.uuid4())
        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = None

        with self.app.container.client_repo.override(client_repo_mock):
            if api_method == 'get':
                resp = self.client.get(f'/api/v1/clients/{client_id}')
            else:
                token = self.gen_token(client_id=client_id, role=self.faker.random_element(list(Role)))
                resp = self.call_info_api(token)

        cast(Mock, client_repo_mock.get).assert_called_once_with(client_id)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 404)
        self.assertEqual(resp_data['message'], 'Client not found.')

    def test_get_client_invalid(self) -> None:
        client_id = self.faker.word()
        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = None

        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.client.get(f'/api/v1/clients/{client_id}')

        cast(Mock, client_repo_mock.get).assert_not_called()

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertEqual(resp_data['message'], 'Invalid client ID.')

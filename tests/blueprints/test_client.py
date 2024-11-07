import base64
import json
from datetime import UTC
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Client, Employee, InvitationStatus, Plan, Role
from repositories import ClientRepository, EmployeeRepository
from repositories.errors import DuplicateEmailError


class TestClient(ParametrizedTestCase):
    INFO_API_URL = '/api/v1/clients/me'
    PLAN_API_URL = '/api/v1/clients/me/plan'
    FIND_API_URL = '/api/v1/clients/detail'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def gen_token_client(self, *, client_id: str | None, role: Role, assigned: bool = True) -> dict[str, Any]:
        return {
            'sub': cast(str, self.faker.uuid4()),
            'cid': client_id,
            'role': role.value,
            'aud': ('' if assigned else 'unassigned_') + role.value,
        }

    def call_find_client_api(self, body: dict[str, Any] | str) -> TestResponse:
        return self.client.post(
            self.FIND_API_URL,
            data=body if isinstance(body, str) else json.dumps(body),
            content_type='application/json',
        )

    def call_info_api_client(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.get(self.INFO_API_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(self.INFO_API_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def call_register_api(self, body: dict[str, Any] | str, token: dict[str, str]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            '/api/v1/clients',
            data=body if isinstance(body, str) else json.dumps(body),
            content_type='application/json',
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
        )

    def call_select_plan_api(self, plan: str, token: dict[str, str]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(f'{self.PLAN_API_URL}/{plan}', headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def test_info_no_token(self) -> None:
        resp = self.call_info_api_client(None)

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
        token = self.gen_token_client(
            client_id=cast(str, self.faker.uuid4()),
            role=self.faker.random_element(list(Role)),
        )
        del token[missing_field]
        resp = self.call_info_api_client(token)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': f'{missing_field} is missing in token'})

    def test_list_clients(self) -> None:
        clients = [
            Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
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
            ('find', None, True),
        ],
    )
    def test_get_client_found(self, *, api_method: str, role: Role | None, expect_plan: bool) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = client
        cast(Mock, client_repo_mock.find_by_email).return_value = client

        with self.app.container.client_repo.override(client_repo_mock):
            if api_method == 'get':
                resp = self.client.get(f'/api/v1/clients/{client.id}')
            elif api_method == 'find':
                resp = self.call_find_client_api({'email': client.email_incidents})
            else:
                token = self.gen_token_client(client_id=client.id, role=cast(Role, role))
                resp = self.call_info_api_client(token)

        if api_method == 'find':
            cast(Mock, client_repo_mock.find_by_email).assert_called_once_with(client.email_incidents)
        else:
            cast(Mock, client_repo_mock.get).assert_called_once_with(client.id)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], client.id)
        self.assertEqual(resp_data['name'], client.name)
        self.assertEqual(resp_data['emailIncidents'], client.email_incidents)
        if expect_plan:
            self.assertEqual(resp_data['plan'], None if client.plan is None else client.plan.value)
        else:
            self.assertNotIn('plan', resp_data)

    @parametrize(
        ('api_method',),
        [
            ('get',),
            ('info',),
            ('find',),
        ],
    )
    def test_get_client_missing(self, api_method: str) -> None:
        client_id = cast(str, self.faker.uuid4())
        client_email = self.faker.email()
        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = None
        cast(Mock, client_repo_mock.find_by_email).return_value = None

        with self.app.container.client_repo.override(client_repo_mock):
            if api_method == 'get':
                resp = self.client.get(f'/api/v1/clients/{client_id}')
            elif api_method == 'find':
                resp = self.call_find_client_api({'email': client_email})
            else:
                token = self.gen_token_client(client_id=client_id, role=self.faker.random_element(list(Role)))
                resp = self.call_info_api_client(token)

        if api_method == 'find':
            cast(Mock, client_repo_mock.find_by_email).assert_called_once_with(client_email)
        else:
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

    def gen_register_data_with_bounds(self, field: str, length: int) -> dict[str, Any]:
        register_data = {
            'name': self.faker.company(),
            'prefixEmailIncidents': self.faker.email().split('@')[0].lower(),
        }

        register_data[field] = self.faker.pystr(min_chars=length, max_chars=length)

        return register_data

    @parametrize(
        ('api_method',),
        [
            ('register',),
            ('find',),
        ],
    )
    def test_register_invalid_json(self, api_method: str) -> None:
        token = self.gen_token_client(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=False)
        client_repo_mock = Mock(ClientRepository)
        with self.app.container.client_repo.override(client_repo_mock):
            body = 'invalid json'
            resp = self.call_register_api(body, token=token) if api_method == 'register' else self.call_find_client_api(body)

        cast(Mock, client_repo_mock.create).assert_not_called()
        cast(Mock, client_repo_mock.find_by_email).assert_not_called()

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertEqual(resp_data['message'], 'The request body could not be parsed as valid JSON.')

    @parametrize(
        'field',
        [
            ('name',),
            ('prefixEmailIncidents',),
        ],
    )
    def test_register_missing_field(self, field: str) -> None:
        token = self.gen_token_client(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=False)
        register_data = {
            'name': self.faker.name(),
            'prefixEmailIncidents': self.faker.email().split('@')[0].lower(),
        }

        del register_data[field]

        client_repo_mock = Mock(ClientRepository)
        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.call_register_api(register_data, token=token)

        cast(Mock, client_repo_mock.create).assert_not_called()

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertEqual(resp_data['message'], f'Invalid value for {field}: Missing data for required field.')

    @parametrize(
        ['field', 'length'],
        [
            ('name', 0),
            ('name', 61),
            ('prefixEmailIncidents', 61),
            ('prefixEmailIncidents', 0),
        ],
    )
    def test_register_bounds_fail(self, field: str, length: int) -> None:
        token = self.gen_token_client(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=False)
        register_data = self.gen_register_data_with_bounds(field, length)

        client_repo_mock = Mock(ClientRepository)
        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.call_register_api(register_data, token=token)

        cast(Mock, client_repo_mock.create).assert_not_called()

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertTrue(resp_data['message'].startswith(f'Invalid value for {field}:'))

    @parametrize(
        ['field', 'length'],
        [
            ('name', 1),
            ('name', 60),
            ('prefixEmailIncidents', 60),
            ('prefixEmailIncidents', 1),
        ],
    )
    def test_register_bounds_valid(self, field: str, length: int) -> None:
        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED,
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )

        token = self.gen_token_client(
            client_id=employee.client_id,
            role=employee.role,
            assigned=False,
        )

        register_data = self.gen_register_data_with_bounds(field, length)

        client_repo_mock = Mock(ClientRepository)
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee
        with (
            self.app.container.client_repo.override(client_repo_mock),
            self.app.container.employee_repo.override(employee_repo_mock),
        ):
            resp = self.call_register_api(register_data, token=token)

        cast(Mock, client_repo_mock.create).assert_called_once()
        repo_client: Client = cast(Mock, client_repo_mock.create).call_args[0][0]
        self.assertEqual(repo_client.name, register_data['name'])
        self.assertEqual(repo_client.email_incidents, (register_data['prefixEmailIncidents'] + '@capibaras.io').lower())

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], repo_client.id)
        self.assertEqual(resp_data['name'], repo_client.name)
        self.assertEqual(resp_data['emailIncidents'], repo_client.email_incidents)

    def test_register_duplicate_email(self) -> None:
        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED,
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )

        token = self.gen_token_client(
            client_id=employee.client_id,
            role=employee.role,
            assigned=False,
        )

        register_data = {
            'name': self.faker.name(),
            'prefixEmailIncidents': self.faker.email().split('@')[0].lower(),
        }

        client_repo_mock = Mock(ClientRepository)
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee
        cast(Mock, client_repo_mock.create).side_effect = DuplicateEmailError(
            (register_data['prefixEmailIncidents'] + '@capibaras.io').lower()
        )
        with (
            self.app.container.client_repo.override(client_repo_mock),
            self.app.container.employee_repo.override(employee_repo_mock),
        ):
            resp = self.call_register_api(register_data, token=token)

        cast(Mock, client_repo_mock.create).assert_called_once()
        repo_client: Client = cast(Mock, client_repo_mock.create).call_args[0][0]
        self.assertEqual(repo_client.name, register_data['name'])
        self.assertEqual(repo_client.email_incidents, (register_data['prefixEmailIncidents'] + '@capibaras.io').lower())

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 409)
        self.assertEqual(resp_data['message'], 'Email already registered.')

    def test_select_plan(self) -> None:
        new_plan: Plan = self.faker.random_element(list(Plan))

        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = client

        token = self.gen_token_client(client_id=client.id, role=Role.ADMIN)

        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.call_select_plan_api(plan=new_plan, token=token)

        client.plan = new_plan

        cast(Mock, client_repo_mock.get).assert_called_once_with(client.id)
        cast(Mock, client_repo_mock.update).assert_called_once_with(client)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['plan'], new_plan)

    def test_select_plan_invalid_plan(self) -> None:
        token = self.gen_token_client(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN)

        resp = self.call_select_plan_api(plan=self.faker.pystr(), token=token)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertEqual(resp_data['message'], 'Invalid plan.')

    def test_select_plan_not_admin(self) -> None:
        token = self.gen_token_client(
            client_id=cast(str, self.faker.uuid4()), role=self.faker.random_element([Role.ANALYST, Role.AGENT])
        )

        resp = self.call_select_plan_api(plan=self.faker.random_element(list(Plan)), token=token)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 403)
        self.assertEqual(resp_data['message'], 'You do not have access to this resource.')

    def test_select_plan_client_not_found(self) -> None:
        token = self.gen_token_client(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN)

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get).return_value = None

        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.call_select_plan_api(plan=self.faker.random_element(list(Plan)), token=token)

        cast(Mock, client_repo_mock.get).assert_called_once()

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 404)
        self.assertEqual(resp_data['message'], 'Client not found.')

    def test_find_invalid_email(self) -> None:
        client_repo_mock = Mock(ClientRepository)
        with self.app.container.client_repo.override(client_repo_mock):
            body = {
                'email': self.faker.word(),
            }
            resp = self.call_find_client_api(body)

        cast(Mock, client_repo_mock.create).assert_not_called()
        cast(Mock, client_repo_mock.find_by_email).assert_not_called()

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['code'], 400)
        self.assertEqual(resp_data['message'], 'Invalid value for email: Not a valid email address.')

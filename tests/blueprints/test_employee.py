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
from models import Employee, InvitationStatus, Role
from repositories import EmployeeRepository


class TestEmployee(ParametrizedTestCase):
    INFO_API_URL = '/api/v1/employees/me'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def gen_token(self, *, client_id: str | None, role: Role, assigned: bool) -> dict[str, Any]:
        return {
            'sub': cast(str, self.faker.uuid4()),
            'cid': client_id,
            'role': role.value,
            'aud': ('' if assigned else 'unassigned_') + role.value,
        }

    def call_info_api(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.get(self.INFO_API_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(self.INFO_API_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def test_info_employee_not_found(self) -> None:
        token = self.gen_token(
            client_id=cast(str, self.faker.uuid4()),
            role=self.faker.random_element(list(Role)),
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.get).return_value = None
        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_info_api(token)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 404, 'message': 'Employee not found'})

    @parametrize(
        'assigned',
        [
            (True,),
            (False,),
        ],
    )
    def test_info_employee_found(self, *, assigned: bool) -> None:
        invitation_status = (
            self.faker.random_element([InvitationStatus.ACCEPTED, InvitationStatus.UNINVITED])
            if assigned
            else InvitationStatus.UNINVITED
        )

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()) if assigned else None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=invitation_status,
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )

        token = self.gen_token(
            client_id=employee.client_id,
            role=employee.role,
            assigned=assigned,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.get).return_value = employee
        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_info_api(token)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], employee.id)
        self.assertEqual(resp_data['clientId'], employee.client_id)
        self.assertEqual(resp_data['name'], employee.name)
        self.assertEqual(resp_data['email'], employee.email)
        self.assertEqual(resp_data['role'], employee.role)

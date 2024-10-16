import json
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase
from werkzeug.test import TestResponse

from app import create_app
from models import Employee, Role
from repositories import EmployeeRepository
from repositories.errors import UnexpectedError


class TestEmployeeRegister(ParametrizedTestCase):
    REGISTER_API_URL = '/api/v1/employees'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def call_register_api(self, payload: dict[str, Any]) -> TestResponse:
        return self.client.post(self.REGISTER_API_URL, json=payload)

    def test_register_employee_success(self) -> None:
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {
                'name': self.faker.name(),
                'email': self.faker.email(),
                'password': self.faker.password(length=12),
                'role': self.faker.random_element([Role.ADMIN.value, Role.ANALYST.value, Role.AGENT.value]),
            }
            resp = self.call_register_api(payload)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['name'], payload['name'])
        self.assertEqual(resp_data['email'], payload['email'])
        self.assertEqual(resp_data['role'], payload['role'])
        self.assertIsNotNone(resp_data['id'])

    def test_register_employee_email_already_registered(self) -> None:
        employee_repo_mock = Mock(EmployeeRepository)
        existing_employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
        )
        cast(Mock, employee_repo_mock.find_by_email).return_value = existing_employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {
                'name': self.faker.name(),
                'email': existing_employee.email,
                'password': self.faker.password(length=12),
                'role': self.faker.random_element([Role.ADMIN.value, Role.ANALYST.value, Role.AGENT.value]),
            }
            resp = self.call_register_api(payload)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': 'Email already registered'})

    def test_register_employee_validation_error(self) -> None:
        invalid_payload = {
            'name': '',  # Name is required and cannot be empty
            'email': 'invalid-email',  # Invalid email format
            'password': 'short',  # Password too short
            'role': 'INVALID_ROLE',  # Invalid role
        }

        resp = self.call_register_api(invalid_payload)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertIn('message', resp_data)
        self.assertIn('Invalid value for name', resp_data['message'])
        self.assertIn('Invalid value for email', resp_data['message'])
        self.assertIn('Shorter than minimum length', resp_data['message'])
        self.assertIn('Must be one of', resp_data['message'])

    def test_register_employee_unexpected_error(self) -> None:
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None
        cast(Mock, employee_repo_mock.create).side_effect = UnexpectedError('An unexpected error occurred.')

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {
                'name': self.faker.name(),
                'email': self.faker.email(),
                'password': self.faker.password(length=12),
                'role': self.faker.random_element([Role.ADMIN.value, Role.ANALYST.value, Role.AGENT.value]),
            }
            resp = self.call_register_api(payload)

        self.assertEqual(resp.status_code, 500)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 500, 'message': 'An unexpected error occurred.'})

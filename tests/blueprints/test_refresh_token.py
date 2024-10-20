import base64
import json
from datetime import UTC
from typing import Any, cast
from unittest.mock import Mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from faker import Faker
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Employee, InvitationStatus, Role
from repositories import EmployeeRepository


class TestAuthRefreshToken(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.jwt_issuer = self.faker.uri()
        jwt_private_key = Ed25519PrivateKey.generate()
        self.jwt_public_key = jwt_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.app.container.config.jwt.issuer.override(self.jwt_issuer)
        self.app.container.config.jwt.private_key.override(
            jwt_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.app.container.unwire()

    def call_refresh_api(self, token: dict[str, Any]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            '/api/v1/auth/employee/refresh',
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
        )

    def test_refresh_token_employee_not_found(self) -> None:
        token = {
            'sub': cast(str, self.faker.uuid4()),
            'cid': cast(str, self.faker.uuid4()),
            'email': self.faker.email(),
            'role': self.faker.random_element(list(Role)).value,
            'aud': 'unassigned_' + self.faker.random_element(list(Role)).value,
        }

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_refresh_api(token)

        cast(Mock, employee_repo_mock.find_by_email).assert_called_once_with(token['email'])

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['code'], 404)
        self.assertEqual(resp_data['message'], 'Employee not found')

    @parametrize(
        'assigned',
        [
            (True,),
            (False,),
        ],
    )
    def test_refresh_token_success(self, assigned: bool) -> None:
        password = self.faker.password()
        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()) if assigned else None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(password),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.ACCEPTED,
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )

        token = {
            'sub': employee.id,
            'cid': employee.client_id,
            'email': employee.email,
            'role': employee.role.value,
            'aud': ('unassigned_' if employee.client_id is None else '') + employee.role.value,
        }

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_refresh_api(token)

        cast(Mock, employee_repo_mock.find_by_email).assert_called_once_with(employee.email)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertIn('token', resp_data)

        audience = ('unassigned_' if employee.client_id is None else '') + employee.role.value
        decoded_token = jwt.decode(resp_data['token'], self.jwt_public_key, algorithms=['EdDSA'], audience=audience)
        self.assertEqual(decoded_token['iss'], self.jwt_issuer)
        self.assertEqual(decoded_token['sub'], employee.id)
        self.assertEqual(decoded_token['cid'], employee.client_id)
        self.assertEqual(decoded_token['email'], employee.email)
        self.assertEqual(decoded_token['role'], employee.role.value)
        self.assertEqual(decoded_token['aud'], audience)

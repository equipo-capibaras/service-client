import base64
import json
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Employee, InvitationResponse, InvitationStatus, Role
from repositories import DuplicateEmailError, EmployeeRepository


class TestEmployee(ParametrizedTestCase):
    INFO_API_URL = '/api/v1/employees/me'
    REGISTER_API_URL = '/api/v1/employees'
    LIST_API_URL = '/api/v1/employees'
    INVITE_API_URL = '/api/v1/employees/invite'
    ANSWER_API_URL = '/api/v1/employees/invitation'
    DETAIL_API_URL = '/api/v1/employees/detail'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def gen_token_employee(self, *, client_id: str | None, role: Role, assigned: bool) -> dict[str, Any]:
        return {
            'sub': cast(str, self.faker.uuid4()),
            'cid': client_id,
            'role': role.value,
            'aud': ('' if assigned else 'unassigned_') + role.value,
        }

    def call_info_api_employee(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.get(self.INFO_API_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(self.INFO_API_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def call_register_api(self, payload: dict[str, Any]) -> TestResponse:
        return self.client.post(self.REGISTER_API_URL, json=payload)

    def call_list_api(self, token: dict[str, str] | None, params: dict[str, Any] | None = None) -> TestResponse:
        headers = {}
        if token is not None:
            token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
            headers = {'X-Apigateway-Api-Userinfo': token_encoded}

        return self.client.get(self.LIST_API_URL, headers=headers, query_string=params)

    def call_invite_api(self, payload: dict[str, Any], token: dict[str, str]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            self.INVITE_API_URL,
            json=payload,
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
        )

    def call_answer_api(self, payload: dict[str, Any], token: dict[str, str]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            self.ANSWER_API_URL,
            json=payload,
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
        )

    def call_detail_api(self, payload: dict[str, Any], token: dict[str, str]) -> TestResponse:
        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.post(
            self.DETAIL_API_URL,
            json=payload,
            headers={'X-Apigateway-Api-Userinfo': token_encoded},
        )

    def test_info_employee_not_found(self) -> None:
        token = self.gen_token_employee(
            client_id=cast(str, self.faker.uuid4()),
            role=self.faker.random_element(list(Role)),
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.get).return_value = None
        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_info_api_employee(token)

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

        token = self.gen_token_employee(
            client_id=employee.client_id,
            role=employee.role,
            assigned=assigned,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.get).return_value = employee
        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_info_api_employee(token)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], employee.id)
        self.assertEqual(resp_data['clientId'], employee.client_id)
        self.assertEqual(resp_data['name'], employee.name)
        self.assertEqual(resp_data['email'], employee.email)
        self.assertEqual(resp_data['role'], employee.role)

    def test_register_employee_success(self) -> None:
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {
                'name': self.faker.name(),
                'email': self.faker.email(),
                'password': self.faker.password(length=12),
                'role': self.faker.random_element(list(Role)),
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
        cast(Mock, employee_repo_mock.create).side_effect = DuplicateEmailError('Email already registered')

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {
                'name': self.faker.name(),
                'email': self.faker.email(),
                'password': self.faker.password(length=12),
                'role': self.faker.random_element(list(Role)),
            }
            resp = self.call_register_api(payload)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 409, 'message': 'Email already registered'})

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

    def test_list_employees_forbidden(self) -> None:
        # Probar acceso con usuario que no es administrador
        token = self.gen_token_employee(
            client_id=cast(str, self.faker.uuid4()),
            role=self.faker.random_element([Role.ANALYST, Role.AGENT]),
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_list_api(token)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 403, 'message': 'Forbidden: You do not have access to this resource.'})

    @parametrize(
        ('page_size', 'page_number', 'expected_count', 'total_pages'),
        [
            (5, 1, 5, 3),  # Página 1 con tamaño 5, espera 5 empleados y 3 páginas en total
            (5, 3, 2, 3),  # Página 3 con tamaño 5, espera 2 empleados y 3 páginas en total
            (10, 1, 10, 2),  # Página 1 con tamaño 10, espera 10 empleados y 2 páginas en total
            (5, 4, 0, 3),  # Página 4 con tamaño 5, espera 0 empleados y 3 páginas en total
        ],
    )
    def test_list_employees_pagination(self, page_size: int, page_number: int, expected_count: int, total_pages: int) -> None:
        client_id = cast(str, self.faker.uuid4())

        # Crear empleados de prueba
        employees = [
            Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client_id,
                name=self.faker.name(),
                email=self.faker.email(),
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
                invitation_status=self.faker.random_element([InvitationStatus.ACCEPTED, InvitationStatus.PENDING]),
                invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
            )
            for _ in range(12)
        ]
        employees.sort(key=lambda e: e.invitation_date, reverse=True)

        # Generar token de administrador
        token = self.gen_token_employee(
            client_id=client_id,
            role=Role.ADMIN,
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.count).return_value = len(employees)
        cast(Mock, employee_repo_mock.get_all).return_value = (e for e in employees[:expected_count])

        with self.app.container.employee_repo.override(employee_repo_mock):
            params = {'page_size': page_size, 'page_number': page_number}
            resp = self.call_list_api(token, params)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        # Validar empleados devueltos y el número de páginas totales
        self.assertEqual(len(resp_data['employees']), expected_count)
        self.assertEqual(resp_data['totalPages'], total_pages)
        self.assertEqual(resp_data['currentPage'], page_number)

    def test_invalid_page_size(self) -> None:
        # Probar con un page_size inválido
        token = self.gen_token_employee(
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        with self.app.container.employee_repo.override(employee_repo_mock):
            params = {'page_size': 15}  # Valor no permitido
            resp = self.call_list_api(token, params)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        allowed_page_sizes = [5, 10, 20]
        self.assertEqual(resp_data, {'code': 400, 'message': f'Invalid page_size. Allowed values are {allowed_page_sizes}.'})

    def test_invalid_page_number(self) -> None:
        # Simular un token válido con permisos de administrador
        token = self.gen_token_employee(
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.count).return_value = 0
        cast(Mock, employee_repo_mock.get_all).return_value = (e for e in list[Employee]())

        # Llamar al endpoint con el token simulado y con un page_number inválido
        with self.app.container.employee_repo.override(employee_repo_mock):
            params = {'page_number': 0}  # Valor no permitido (menor que 1)
            resp = self.call_list_api(token, params)

        # Verificar el código de estado de la respuesta y el mensaje de error esperado
        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 400, 'message': 'Invalid page_number. Page number must be 1 or greater.'})

    def setup_employee(
        self, client_id: str | None = None, invitation_status: InvitationStatus | None = InvitationStatus.UNINVITED
    ) -> Employee:
        return Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED if invitation_status is None else invitation_status,
            invitation_date=datetime.now(UTC).replace(microsecond=0),
        )

    def setup_invite_test(self, employee: Employee, token: dict[str, Any]) -> TestResponse:
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {'email': employee.email}
            return self.call_invite_api(payload, token)

    def test_invite_employee_success(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=False)
        employee = self.setup_employee()
        resp = self.setup_invite_test(employee, token)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee invited successfully')
        self.assertEqual(resp_data['employee']['id'], employee.id)
        self.assertEqual(resp_data['employee']['email'], employee.email)
        self.assertEqual(resp_data['employee']['invitationStatus'], InvitationStatus.PENDING.value)
        self.assertIsNotNone(resp_data['employee']['invitationDate'])

    def test_invite_employee_not_admin(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ANALYST, assigned=True)
        payload = {'email': self.faker.email()}

        resp = self.call_invite_api(payload, token)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(
            resp_data['message'], 'Forbidden: You do not have access to this resource or must be linked to a company.'
        )

    def test_invite_employee_not_linked_to_company(self) -> None:
        token = self.gen_token_employee(client_id=None, role=Role.ADMIN, assigned=True)
        payload = {'email': self.faker.email()}

        resp = self.call_invite_api(payload, token)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(
            resp_data['message'], 'Forbidden: You do not have access to this resource or must be linked to a company.'
        )

    def test_invite_employee_already_linked_to_another_company(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        employee = self.setup_employee(client_id=cast(str, self.faker.uuid4()))
        resp = self.setup_invite_test(employee, token)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee already linked to another company.')

    def test_invite_employee_already_linked_to_same_company(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        token = self.gen_token_employee(client_id=client_id, role=Role.ADMIN, assigned=True)
        employee = self.setup_employee(client_id=client_id)
        resp = self.setup_invite_test(employee, token)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee already linked to your company')

    def test_invite_employee_already_invited(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=None,
            name=self.faker.name(),
            email=self.faker.email(),
            password=self.faker.password(),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.PENDING,
            invitation_date=datetime.now(UTC),
        )

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {'email': employee.email}
            resp = self.call_invite_api(payload, token)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee already invited.')

    def test_invite_employee_not_found(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            payload = {'email': self.faker.email()}
            resp = self.call_invite_api(payload, token)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee not found.')

    def test_accept_invitation_success(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        token = self.gen_token_employee(client_id=client_id, role=Role.AGENT, assigned=True)
        employee = self.setup_employee(client_id=client_id, invitation_status=InvitationStatus.PENDING)
        payload = {'response': InvitationResponse.ACCEPTED.value}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee
        cast(Mock, employee_repo_mock.delete).return_value = None
        cast(Mock, employee_repo_mock.create).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Invitation accepted successfully')
        self.assertEqual(resp_data['employee']['invitationStatus'], InvitationStatus.ACCEPTED.value)

    def test_decline_invitation_success(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.AGENT, assigned=True)
        employee = self.setup_employee(client_id=token['cid'], invitation_status=InvitationStatus.PENDING)
        payload = {'response': InvitationResponse.DECLINED.value}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee
        cast(Mock, employee_repo_mock.delete).return_value = None
        cast(Mock, employee_repo_mock.create).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 201)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Invitation declined successfully')
        self.assertEqual(resp_data['employee']['invitationStatus'], InvitationStatus.UNINVITED.value)
        self.assertIsNone(resp_data['employee']['clientId'])

    def test_invitation_not_found(self) -> None:
        token = self.gen_token_employee(client_id=None, role=Role.AGENT, assigned=True)
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = None
        payload = {'response': InvitationResponse.ACCEPTED.value}

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Employee not found')

    def test_invitation_already_accepted(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.AGENT, assigned=True)
        employee = self.setup_employee(client_id=token['cid'], invitation_status=InvitationStatus.ACCEPTED)
        payload = {'response': InvitationResponse.ACCEPTED.value}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 409)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'You are already linked to the organization')

    def test_no_invitation_to_respond(self) -> None:
        token = self.gen_token_employee(client_id=None, role=Role.AGENT, assigned=True)
        employee = self.setup_employee(client_id=None, invitation_status=InvitationStatus.UNINVITED)
        payload = {'response': InvitationResponse.ACCEPTED.value}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'No invitation to respond to')

    def test_invalid_response(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.AGENT, assigned=True)
        employee = self.setup_employee(client_id=token['cid'], invitation_status=InvitationStatus.PENDING)
        payload = {'response': 'INVALID_RESPONSE'}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_answer_api(payload, token)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data['message'], 'Invalid value for response: Must be one of: accepted, declined.')

    def test_employee_detail_success(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        employee = self.setup_employee()
        payload = {'email': employee.email}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = employee

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_detail_api(payload, token)

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], employee.id)
        self.assertEqual(resp_data['clientId'], employee.client_id)
        self.assertEqual(resp_data['name'], employee.name)
        self.assertEqual(resp_data['email'], employee.email)
        self.assertEqual(resp_data['role'], employee.role.value)
        self.assertEqual(resp_data['invitationStatus'], employee.invitation_status.value)

    def test_employee_detail_not_found(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        payload = {'email': self.faker.email()}

        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.find_by_email).return_value = None

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_detail_api(payload, token)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 404, 'message': 'Employee not found.'})

    def test_employee_detail_forbidden(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.AGENT, assigned=True)
        payload = {'email': self.faker.email()}

        employee_repo_mock = Mock(EmployeeRepository)

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_detail_api(payload, token)

        self.assertEqual(resp.status_code, 403)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 403, 'message': 'Forbidden: You do not have access to this resource.'})

    def test_employee_detail_invalid_body(self) -> None:
        token = self.gen_token_employee(client_id=cast(str, self.faker.uuid4()), role=Role.ADMIN, assigned=True)
        invalid_payload = {'email': 'invalid-email'}

        employee_repo_mock = Mock(EmployeeRepository)

        with self.app.container.employee_repo.override(employee_repo_mock):
            resp = self.call_detail_api(invalid_payload, token)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertIn('Invalid value for email', resp_data['message'])

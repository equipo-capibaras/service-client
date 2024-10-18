import base64
import json
from typing import Any, cast
from unittest.mock import Mock

from faker import Faker
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Employee, Role
from models.employee import InvitationStatus
from repositories import EmployeeRepository


class TestEmployeeList(ParametrizedTestCase):
    LIST_API_URL = '/api/v1/employees'

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

    def call_list_api(self, token: dict[str, str] | None, params: dict[str, Any] | None = None) -> TestResponse:
        headers = {}
        if token is not None:
            token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
            headers = {'X-Apigateway-Api-Userinfo': token_encoded}

        return self.client.get(self.LIST_API_URL, headers=headers, query_string=params)

    def test_list_employees_forbidden(self) -> None:
        # Probar acceso con usuario que no es administrador
        token = self.gen_token(
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
        ],
    )
    def test_list_employees_pagination(self, page_size: int, page_number: int, expected_count: int, total_pages: int) -> None:
        # Crear empleados de prueba
        employees = [
            Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=cast(str, self.faker.uuid4()),
                name=self.faker.name(),
                email=self.faker.email(),
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
                invitation_status=InvitationStatus.UNINVITED,
                invitation_date=self.faker.date_time_this_year(tzinfo=None),
            )
            for _ in range(12)
        ]

        # Generar token de administrador
        token = self.gen_token(
            client_id=employees[0].client_id,
            role=Role.ADMIN,
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        cast(Mock, employee_repo_mock.list_by_client_id).return_value = (employees[:expected_count], len(employees))

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
        token = self.gen_token(
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
        token = self.gen_token(
            client_id=cast(str, self.faker.uuid4()),
            role=Role.ADMIN,
            assigned=True,
        )

        employee_repo_mock = Mock(EmployeeRepository)

        # Mockear la respuesta del repositorio (no es necesario para esta prueba, pero se incluye para consistencia)
        employee_repo_mock.list_by_client_id.return_value = ([], 0)

        # Llamar al endpoint con el token simulado y con un page_number inválido
        with self.app.container.employee_repo.override(employee_repo_mock):
            params = {'page_number': 0}  # Valor no permitido (menor que 1)
            resp = self.call_list_api(token, params)

        # Verificar el código de estado de la respuesta y el mensaje de error esperado
        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())
        self.assertEqual(resp_data, {'code': 400, 'message': 'Invalid page_number. Page number must be 1 or greater.'})

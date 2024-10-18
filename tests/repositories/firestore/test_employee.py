import os
from dataclasses import asdict
from datetime import UTC, datetime
from typing import cast
from unittest import skipUnless

import requests
from faker import Faker
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import DocumentReference
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Client, Employee, Plan, Role
from models.employee import InvitationStatus
from repositories import DuplicateEmailError
from repositories.firestore import UUID_UNASSIGNED, FirestoreEmployeeRepository

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestEmployee(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreEmployeeRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

        self.emails = [self.faker.unique.email() for _ in range(4)]

    @parametrize(
        ('email_idx_map', 'find_idx', 'assigned', 'expected'),
        [
            ({0: 0, 1: 1, 2: 2}, 0, True, 0),  # Employee found
            ({0: 0, 1: 1, 2: 2}, 3, True, None),  # Employee not found
            ({0: 0, 1: 0, 2: 2}, 0, True, None),  # Multiple employees found
            ({0: 0, 1: 1, 2: 2}, 0, False, 0),  # Unassigned employee found
        ],
    )
    def test_find_by_email(
        self, *, email_idx_map: dict[int, int], find_idx: int, assigned: bool, expected: int | None
    ) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employees: list[Employee] = []
        for idx, _ in enumerate(range(3)):
            employee = Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client.id if assigned else None,
                name=self.faker.name(),
                email=self.emails[email_idx_map[idx]],
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
                invitation_status=InvitationStatus.UNINVITED,  # Set an initial invitation status
            )
            employees.append(employee)
            employee_dict = asdict(employee)
            del employee_dict['id']
            del employee_dict['client_id']

            # Convert the enum to string for Firestore
            employee_dict['invitation_status'] = employee.invitation_status.value
            employee_dict['role'] = employee.role.value

            client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id
            self.client.collection('clients').document(client_id).collection('employees').document(employee.id).set(
                employee_dict
            )

        duplicate_emails = len(set(email_idx_map.values())) != len(email_idx_map)

        if duplicate_emails:
            with self.assertLogs() as cm:
                employee_db = self.repo.find_by_email(self.emails[find_idx])
        else:
            with self.assertNoLogs():
                employee_db = self.repo.find_by_email(self.emails[find_idx])

        if expected is not None:
            self.assertIsNotNone(employee_db)
            self.assertEqual(employee_db, employees[expected])
        else:
            self.assertIsNone(employee_db)

            if duplicate_emails:
                self.assertEqual(cm.records[0].message, f'Multiple employees found with email {self.emails[find_idx]}')
                self.assertEqual(cm.records[0].levelname, 'ERROR')

    @parametrize(
        ('assigned',),
        [
            (True,),  # Assigned employee
            (False,),  # Unassigned employee
        ],
    )
    def test_get_found(self, *, assigned: bool) -> None:
        client_id = cast(str, self.faker.uuid4()) if assigned else None
        self.client.collection('clients').document(client_id).set({})

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED,  # Establecemos un estado de invitación inicial
        )
        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']

        # Convertir los valores del enum a cadenas para Firestore
        employee_dict['invitation_status'] = employee.invitation_status.value
        employee_dict['role'] = employee.role.value

        client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id
        self.client.collection('clients').document(client_id).collection('employees').document(employee.id).set(employee_dict)

        employee_db = self.repo.get(employee.id, employee.client_id)

        self.assertEqual(employee_db, employee)

    def test_get_not_found(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        employee_id = cast(str, self.faker.uuid4())
        employee = self.repo.get(employee_id, client_id)

        self.assertIsNone(employee)

    @parametrize(
        ('assigned',),
        [
            (True,),  # Assigned employee
            (False,),  # Unassigned employee
        ],
    )
    def test_create(self, *, assigned: bool) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        # Establecemos una fecha de invitación inicial
        invitation_date = datetime.now(UTC)

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client.id if assigned else None,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED,  # Estado inicial de la invitación
            invitation_date=invitation_date,  # Nueva fecha de invitación
        )

        self.repo.create(employee)

        client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id
        employee_ref = cast(
            DocumentReference,
            self.client.collection('clients').document(client_id).collection('employees').document(employee.id),
        )
        doc = employee_ref.get()

        self.assertTrue(doc.exists)

        # Convertir el diccionario obtenido desde Firestore de vuelta al formato del objeto Employee
        employee_dict_from_firestore = doc.to_dict()

        # Verificar que el diccionario no sea None
        if employee_dict_from_firestore is None:
            raise ValueError(f'Document with ID {employee.id} not found in Firestore')

        # Convertir valores de enums desde Firestore a los objetos correctos
        employee_dict_from_firestore['role'] = Role(employee_dict_from_firestore['role'])
        employee_dict_from_firestore['invitation_status'] = InvitationStatus(employee_dict_from_firestore['invitation_status'])

        # Convertir la fecha de invitación de Firestore a datetime
        employee_dict_from_firestore['invitation_date'] = (
            datetime.fromisoformat(employee_dict_from_firestore['invitation_date'])
            if employee_dict_from_firestore['invitation_date']
            else None
        )

        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']

        self.assertEqual(employee_dict_from_firestore, employee_dict)

    def test_create_duplicate(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        employee1 = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.UNINVITED,  # Set an initial invitation status
        )
        employee_dict = asdict(employee1)
        del employee_dict['id']
        del employee_dict['client_id']

        # Convert the enum to string for Firestore
        employee_dict['invitation_status'] = employee1.invitation_status.value
        employee_dict['role'] = employee1.role.value

        self.client.collection('clients').document(client_id).collection('employees').document(employee1.id).set(employee_dict)

        employee2 = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=employee1.email,
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
            invitation_status=InvitationStatus.PENDING,  # Set an initial invitation status
        )

        with self.assertRaises(DuplicateEmailError) as context:
            self.repo.create(employee2)

        self.assertEqual(str(context.exception), f"A user with the email '{employee2.email}' already exists.")

        employee_ref = cast(
            DocumentReference,
            self.client.collection('clients').document(client_id).collection('employees').document(employee2.id),
        )
        doc = employee_ref.get()
        self.assertFalse(doc.exists)

    def test_delete_all(self) -> None:
        employees: list[Employee] = []

        # Add 3 clients with 3 employees each to Firestore
        for _ in range(3):
            client = Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(list(Plan)),
                email_incidents=self.faker.unique.email(),
            )

            client_dict = asdict(client)
            del client_dict['id']
            self.client.collection('clients').document(client.id).set(client_dict)

            for _ in range(3):
                employee = Employee(
                    id=cast(str, self.faker.uuid4()),
                    client_id=client.id,
                    name=self.faker.name(),
                    email=self.faker.unique.email(),
                    password=pbkdf2_sha256.hash(self.faker.password()),
                    role=self.faker.random_element(list(Role)),
                    invitation_status=InvitationStatus.PENDING,  # Set the initial status
                )
                employees.append(employee)
                employee_dict = asdict(employee)
                del employee_dict['id']
                del employee_dict['client_id']

                # Convert Enums to strings
                employee_dict['role'] = employee.role.value
                employee_dict['invitation_status'] = employee.invitation_status.value

                self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(
                    employee_dict
                )

        self.repo.delete_all()

        for employee in employees:
            employee_ref = cast(
                DocumentReference,
                self.client.collection('clients').document(employee.client_id).collection('employees').document(employee.id),
            )

            doc = employee_ref.get()

            self.assertFalse(doc.exists)

    def test_count_by_client_id(self) -> None:
        # Crear un cliente
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        # Contar empleados antes de agregar (debe ser cero)
        count = self.repo.count_by_client_id(client.id)
        self.assertEqual(count, 0)

        # Agregar empleados y verificar la cantidad
        employees: list[Employee] = []
        for _ in range(5):
            employee = Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client.id,
                name=self.faker.name(),
                email=self.faker.unique.email(),
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
                invitation_status=InvitationStatus.UNINVITED,
            )
            employees.append(employee)
            employee_dict = asdict(employee)
            del employee_dict['id']
            del employee_dict['client_id']

            # Convertir enums a valores para Firestore
            employee_dict['invitation_status'] = employee.invitation_status.value
            employee_dict['role'] = employee.role.value

            self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(
                employee_dict)

        # Contar empleados nuevamente (debe ser 5)
        count = self.repo.count_by_client_id(client.id)
        self.assertEqual(count, 5)

    @parametrize(
        ('page_size', 'page_number', 'expected_count'),
        [
            (5, 1, 5),  # Página 1 con tamaño 5 (espera 5 empleados)
            (5, 2, 5),  # Página 2 con tamaño 5 (espera 5 empleados más)
            (5, 3, 2),  # Página 3 con tamaño 5 (espera 2 empleados restantes)
            (10, 1, 10),  # Página 1 con tamaño 10 (espera 10 empleados)
        ],
    )
    def test_list_by_client_id(self, page_size: int, page_number: int, expected_count: int) -> None:
        # Crear un cliente
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        # Agregar empleados
        employees: list[Employee] = []
        for _ in range(12):
            employee = Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client.id,
                name=self.faker.name(),
                email=self.faker.unique.email(),
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
                invitation_status=InvitationStatus.UNINVITED,
                invitation_date=datetime.now(UTC),  # Agregar fecha de invitación
            )
            employees.append(employee)
            employee_dict = asdict(employee)
            del employee_dict['id']
            del employee_dict['client_id']

            # Convertir enums y fecha a valores para Firestore
            employee_dict['invitation_status'] = employee.invitation_status.value
            employee_dict['role'] = employee.role.value
            employee_dict['invitation_date'] = employee.invitation_date.isoformat()

            self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(
                employee_dict)

        # Listar empleados en la página indicada
        employees_listed, total_employees = self.repo.list_by_client_id(client.id, page_size, page_number)

        # Verificar la cantidad de empleados devuelta y el total
        self.assertEqual(len(employees_listed), expected_count)
        self.assertEqual(total_employees, 12)


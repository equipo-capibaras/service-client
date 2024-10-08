import os
from dataclasses import asdict
from typing import cast
from unittest import TestCase, skipUnless

import requests
from faker import Faker
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import DocumentReference
from passlib.hash import pbkdf2_sha256

from models import Client, Employee, Plan, Role
from repositories.firestore import FirestoreEmployeeRepository

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestEmployee(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreEmployeeRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

    def test_find_by_email(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client.id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
        )
        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']
        self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(employee_dict)

        employee_db = self.repo.find_by_email(employee.email)
        self.assertIsNotNone(employee_db)
        self.assertEqual(employee_db, employee)

    def test_find_by_email_not_found(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client.id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
        )
        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']
        self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(employee_dict)

        employee_db = self.repo.find_by_email(self.faker.unique.email())
        self.assertIsNone(employee_db)

    def test_find_by_email_multiple_found(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        email = self.faker.unique.email()

        for _ in range(2):
            employee = Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client.id,
                name=self.faker.name(),
                email=email,
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=self.faker.random_element(list(Role)),
            )
            employee_dict = asdict(employee)
            del employee_dict['id']
            del employee_dict['client_id']
            self.client.collection('clients').document(client.id).collection('employees').document(employee.id).set(
                employee_dict
            )

        with self.assertLogs() as cm:
            employee_db = self.repo.find_by_email(email)
        self.assertIsNone(employee_db)
        self.assertEqual(cm.records[0].message, f'Multiple employees found with email {email}')
        self.assertEqual(cm.records[0].levelname, 'ERROR')

    def test_create(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client.id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=self.faker.random_element(list(Role)),
        )

        self.repo.create(employee)

        employee_ref = cast(
            DocumentReference,
            self.client.collection('clients').document(client.id).collection('employees').document(employee.id),
        )
        doc = employee_ref.get()

        self.assertTrue(doc.exists)

        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']
        self.assertEqual(doc.to_dict(), employee_dict)

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
                )
                employees.append(employee)
                employee_dict = asdict(employee)
                del employee_dict['id']
                del employee_dict['client_id']
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

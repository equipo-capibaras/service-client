import os
from dataclasses import asdict
from datetime import UTC
from typing import cast
from unittest import skipUnless

import requests
from faker import Faker
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import DocumentReference
from passlib.hash import pbkdf2_sha256
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Client, Employee, InvitationStatus, Plan, Role
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

    def gen_add_employees(self, num: int, client_id: str | None, email: str | None = None) -> list[Employee]:
        employees: list[Employee] = []
        for _ in range(num):
            employee = Employee(
                id=cast(str, self.faker.uuid4()),
                client_id=client_id,
                name=self.faker.name(),
                email=self.faker.unique.email() if email is None else email,
                password=pbkdf2_sha256.hash(self.faker.password()),
                role=cast(Role, self.faker.random_element(list(Role))),
                invitation_status=cast(InvitationStatus, self.faker.random_element(list(InvitationStatus))),
                invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
            )
            employees.append(employee)
            employee_dict = asdict(employee)
            del employee_dict['id']
            del employee_dict['client_id']

            client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id
            self.client.collection('clients').document(client_id).collection('employees').document(employee.id).set(
                employee_dict
            )

        return employees

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
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        client_id = client.id if assigned else None

        employees = list[Employee]()
        for idx in range(3):
            employees.append(self.gen_add_employees(1, client_id, self.emails[email_idx_map[idx]])[0])

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

        employee = self.gen_add_employees(1, client_id)[0]

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
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employee = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client.id if assigned else None,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=cast(Role, self.faker.random_element(list(Role))),
            invitation_status=cast(InvitationStatus, self.faker.random_element(list(InvitationStatus))),
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )

        self.repo.create(employee)

        client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id
        employee_ref = cast(
            DocumentReference,
            self.client.collection('clients').document(client_id).collection('employees').document(employee.id),
        )
        doc = employee_ref.get()

        self.assertTrue(doc.exists)

        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']
        self.assertEqual(doc.to_dict(), employee_dict)

    def test_create_duplicate(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        employee1 = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.unique.email(),
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=cast(Role, self.faker.random_element(list(Role))),
            invitation_status=cast(InvitationStatus, self.faker.random_element(list(InvitationStatus))),
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
        )
        employee_dict = asdict(employee1)
        del employee_dict['id']
        del employee_dict['client_id']

        self.client.collection('clients').document(client_id).collection('employees').document(employee1.id).set(employee_dict)

        employee2 = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=employee1.email,
            password=pbkdf2_sha256.hash(self.faker.password()),
            role=cast(Role, self.faker.random_element(list(Role))),
            invitation_status=cast(InvitationStatus, self.faker.random_element(list(InvitationStatus))),
            invitation_date=self.faker.past_datetime(start_date='-30d', tzinfo=UTC),
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
                plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
                email_incidents=self.faker.unique.email(),
            )

            client_dict = asdict(client)
            del client_dict['id']
            self.client.collection('clients').document(client.id).set(client_dict)

            employees = employees + self.gen_add_employees(3, client.id)

        self.repo.delete_all()

        for employee in employees:
            employee_ref = cast(
                DocumentReference,
                self.client.collection('clients').document(employee.client_id).collection('employees').document(employee.id),
            )

            doc = employee_ref.get()

            self.assertFalse(doc.exists)

    def test_count(self) -> None:
        number_of_employees = self.faker.random_int(min=5, max=15)

        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        self.gen_add_employees(number_of_employees, client.id)

        count = self.repo.count(client.id)

        self.assertEqual(count, number_of_employees)

    def test_count_invalid(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        count = self.repo.count(client_id)

        self.assertEqual(count, 0)

    @parametrize(
        ('offset', 'limit'),
        [
            (False, False),  # No offset and limit
            (True, False),  # Offset but no limit
            (False, True),  # Limit but no offset
            (True, True),  # Offset and limit
        ],
    )
    def test_get_all(self, *, offset: bool, limit: bool) -> None:
        number_of_employees = self.faker.random_int(min=10, max=20)
        random_offset = self.faker.random_int(min=2, max=6)
        random_limit = self.faker.random_int(min=2, max=6)

        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client_dict = asdict(client)
        del client_dict['id']
        self.client.collection('clients').document(client.id).set(client_dict)

        employees = self.gen_add_employees(number_of_employees, client.id)

        employees_db = list(
            self.repo.get_all(
                client.id,
                offset=random_offset if offset else None,
                limit=random_limit if limit else None,
            )
        )

        employees.sort(key=lambda x: x.invitation_date, reverse=True)
        if offset:
            employees = employees[random_offset:]
        if limit:
            employees = employees[:random_limit]

        self.assertEqual(employees_db, employees)

    @parametrize(
        ('offset', 'limit'),
        [
            (None, None),
            (5, None),
            (None, 5),
            (5, 5),
        ],
    )
    def test_get_all_invalid(self, offset: int | None, limit: int | None) -> None:
        client_id = cast(str, self.faker.uuid4())
        employees = list(self.repo.get_all(client_id, offset=offset, limit=limit))

        self.assertEqual(employees, [])

    def test_delete(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        employee = self.gen_add_employees(1, client_id)[0]

        # Verify employee exists before deletion
        employee_ref = cast(
            DocumentReference,
            self.client.collection('clients').document(client_id).collection('employees').document(employee.id),
        )
        doc = employee_ref.get()
        self.assertTrue(doc.exists)

        # Delete the employee
        self.repo.delete(employee.id, employee.client_id)

        # Verify employee is deleted
        doc = employee_ref.get()
        self.assertFalse(doc.exists)

    def test_get_agents_by_client_no_agents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # No employees added to this client
        agents = self.repo.get_agents_by_client(client_id)

        # Assert no agents found
        self.assertEqual(agents, [])

    def test_get_agents_by_client_with_agents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # Add multiple agents
        agents = []
        for _ in range(3):
            agent = self.gen_add_employees(1, client_id)[0]
            agent.role = Role.AGENT
            agent.invitation_status = InvitationStatus.ACCEPTED
            agent_ref = self.client.collection('clients').document(client_id).collection('employees').document(agent.id)
            agent_ref.set(asdict(agent))
            agents.append(agent)

        # Get agents from repository
        agents_db = self.repo.get_agents_by_client(client_id)

        # Assert that all added agents are returned
        self.assertEqual(len(agents_db), len(agents))
        self.assertTrue(all(agent in agents for agent in agents_db))

    def test_get_agents_by_client_no_matching_role(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # Add employees with different roles, but not agents
        for _ in range(3):
            employee = self.gen_add_employees(1, client_id)[0]
            employee.role = Role.ADMIN  # No agent roles
            employee_ref = self.client.collection('clients').document(client_id).collection('employees').document(employee.id)
            employee_ref.set(asdict(employee))

        # Get agents from repository
        agents_db = self.repo.get_agents_by_client(client_id)

        # Assert that no agents are found
        self.assertEqual(agents_db, [])

    def test_get_random_agent_no_agents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # No employees added to this client
        agent = self.repo.get_random_agent(client_id)

        # Assert no agent found
        self.assertIsNone(agent)

    def test_get_random_agent_single_agent(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # Add a single agent
        agent = self.gen_add_employees(1, client_id)[0]
        agent.role = Role.AGENT
        agent.invitation_status = InvitationStatus.ACCEPTED
        agent_ref = self.client.collection('clients').document(client_id).collection('employees').document(agent.id)
        agent_ref.set(asdict(agent))

        # Get random agent
        agent_db = self.repo.get_random_agent(client_id)

        # Assert the returned agent is the same as the only one added
        self.assertIsNotNone(agent_db)
        self.assertEqual(agent_db, agent)

    def test_get_random_agent_multiple_agents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        self.client.collection('clients').document(client_id).set({})

        # Add multiple agents
        agents = []
        for _ in range(5):
            agent = self.gen_add_employees(1, client_id)[0]
            agent.role = Role.AGENT
            agent.invitation_status = InvitationStatus.ACCEPTED
            agent_ref = self.client.collection('clients').document(client_id).collection('employees').document(agent.id)
            agent_ref.set(asdict(agent))
            agents.append(agent)

        # Get random agent multiple times to test randomness
        for _ in range(10):
            agent_db = self.repo.get_random_agent(client_id)
            self.assertIsNotNone(agent_db)
            self.assertIn(agent_db, agents)

import contextlib
import os
from dataclasses import asdict
from typing import cast
from unittest import skipUnless

import requests
from faker import Faker
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import Client, Plan
from repositories.errors import DuplicateEmailError
from repositories.firestore import UUID_UNASSIGNED, FirestoreClientRepository

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestClient(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreClientRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

        self.emails = [self.faker.unique.email() for _ in range(4)]

    def add_random_clients(self, n: int) -> list[Client]:
        clients: list[Client] = []

        # Add n clients to Firestore
        for _ in range(n):
            client = Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
                email_incidents=self.faker.unique.email(),
            )

            clients.append(client)
            client_dict = asdict(client)
            del client_dict['id']
            self.client.collection('clients').document(client.id).set(client_dict)

        client_ref = self.client.collection('clients').document(UUID_UNASSIGNED)
        with contextlib.suppress(AlreadyExists):
            client_ref.create({})

        return clients

    @parametrize(
        ('email_idx_map', 'find_idx', 'expected'),
        [
            ({0: 0, 1: 1, 2: 2}, 0, 0),  # Client found
            ({0: 0, 1: 1, 2: 2}, 3, None),  # Client not found
            ({0: 0, 1: 0, 2: 2}, 0, None),  # Multiple clients found
        ],
    )
    def test_find_by_email(self, email_idx_map: dict[int, int], find_idx: int, expected: int | None) -> None:
        clients: list[Client] = []
        for idx in range(3):
            client = Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
                email_incidents=self.emails[email_idx_map[idx]],
            )
            clients.append(client)
            client_dict = asdict(client)
            del client_dict['id']
            self.client.collection('clients').document(client.id).set(client_dict)

        duplicate_emails = len(set(email_idx_map.values())) != len(email_idx_map)

        if duplicate_emails:
            with self.assertLogs() as cm:
                client_db = self.repo.find_by_email(self.emails[find_idx])
        else:
            with self.assertNoLogs():
                client_db = self.repo.find_by_email(self.emails[find_idx])

        if expected is not None:
            self.assertIsNotNone(client_db)
            self.assertEqual(client_db, clients[expected])
        else:
            self.assertIsNone(client_db)

            if duplicate_emails:
                self.assertEqual(cm.records[0].message, f'Multiple clients found with email {self.emails[find_idx]}')
                self.assertEqual(cm.records[0].levelname, 'ERROR')

    def test_create(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        self.repo.create(client)

        doc = self.client.collection('clients').document(client.id).get()
        self.assertTrue(doc.exists)
        client_dict = asdict(client)
        del client_dict['id']
        self.assertEqual(doc.to_dict(), client_dict)

    def test_create_duplicate(self) -> None:
        client1 = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=self.faker.unique.email(),
        )

        client2 = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(cast(list[Plan | None], [*list(Plan), None])),
            email_incidents=client1.email_incidents,
        )

        self.repo.create(client1)

        with self.assertRaises(DuplicateEmailError):
            self.repo.create(client2)

        doc = self.client.collection('clients').document(client1.id).get()
        self.assertTrue(doc.exists)
        client_dict = asdict(client1)
        del client_dict['id']
        self.assertEqual(doc.to_dict(), client_dict)

        doc = self.client.collection('clients').document(client2.id).get()
        self.assertFalse(doc.exists)

    def test_get_existing(self) -> None:
        client = self.add_random_clients(1)[0]

        client_repo = self.repo.get(client.id)

        self.assertEqual(client_repo, client)

    def test_get_unassigned(self) -> None:
        self.add_random_clients(1)
        client_repo = self.repo.get(UUID_UNASSIGNED)

        self.assertIsNone(client_repo)

    def test_get_missing(self) -> None:
        client_repo = self.repo.get(cast(str, self.faker.uuid4()))

        self.assertIsNone(client_repo)

    def test_get_all(self) -> None:
        clients = self.add_random_clients(5)

        retrieved_clients = list(self.repo.get_all())
        sorted_clients = sorted(clients, key=lambda c: c.name)

        for i, client in enumerate(sorted_clients):
            self.assertEqual(retrieved_clients[i], client)

    def test_delete_all(self) -> None:
        clients = self.add_random_clients(5)

        self.repo.delete_all()

        for client in clients:
            doc = self.client.collection('clients').document(client.id).get()

            self.assertFalse(doc.exists)

    def test_update(self) -> None:
        client = self.add_random_clients(1)[0]

        client.plan = cast(Plan, self.faker.random_element(list(Plan)))
        self.repo.update(client)

        doc = self.client.collection('clients').document(client.id).get()
        self.assertTrue(doc.exists)
        client_dict = asdict(client)
        del client_dict['id']
        self.assertEqual(doc.to_dict(), client_dict)

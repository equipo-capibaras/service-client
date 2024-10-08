import os
from dataclasses import asdict
from typing import cast
from unittest import TestCase, skipUnless

import requests
from faker import Faker
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]

from models import Client, Plan
from repositories.firestore import FirestoreClientRepository

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestClient(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreClientRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

    def test_create(self) -> None:
        client = Client(
            id=cast(str, self.faker.uuid4()),
            name=self.faker.company(),
            plan=self.faker.random_element(list(Plan)),
            email_incidents=self.faker.unique.email(),
        )

        self.repo.create(client)

        doc = self.client.collection('clients').document(client.id).get()
        self.assertTrue(doc.exists)
        client_dict = asdict(client)
        del client_dict['id']
        self.assertEqual(doc.to_dict(), client_dict)

    def test_delete_all(self) -> None:
        clients: list[Client] = []

        # Add 3 clients to Firestore
        for _ in range(3):
            client = Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(list(Plan)),
                email_incidents=self.faker.unique.email(),
            )

            clients.append(client)
            client_dict = asdict(client)
            del client_dict['id']
            self.client.collection('clients').document(client.id).set(client_dict)

        self.repo.delete_all()

        for client in clients:
            doc = self.client.collection('clients').document(client.id).get()

            self.assertFalse(doc.exists)

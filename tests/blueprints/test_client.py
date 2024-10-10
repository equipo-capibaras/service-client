import json
from typing import cast
from unittest import TestCase
from unittest.mock import Mock

from faker import Faker

from app import create_app
from models import Client, Plan
from repositories import ClientRepository


class TestClient(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def test_list_clients(self) -> None:
        clients = [
            Client(
                id=cast(str, self.faker.uuid4()),
                name=self.faker.company(),
                plan=self.faker.random_element(list(Plan)),
                email_incidents=self.faker.unique.email(),
            )
            for _ in range(5)
        ]

        client_repo_mock = Mock(ClientRepository)
        cast(Mock, client_repo_mock.get_all).return_value = (c for c in clients)

        with self.app.container.client_repo.override(client_repo_mock):
            resp = self.client.get('/api/v1/clients')

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(len(resp_data), len(clients))
        for i, client in enumerate(clients):
            self.assertEqual(resp_data[i]['id'], client.id)
            self.assertEqual(resp_data[i]['name'], client.name)

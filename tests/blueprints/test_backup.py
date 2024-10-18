import json
from typing import cast
from unittest import TestCase

import responses
from faker import Faker

from app import create_app


class TestBackup(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

        self.project_id = self.faker.pystr()
        self.database = self.faker.pystr()
        self.access_token = self.faker.pystr()

        self.app.container.config.project_id.override(self.project_id)
        self.app.container.config.firestore.database.override(self.database)
        self.app.container.access_token.override(self.access_token)

    def tearDown(self) -> None:
        self.app.container.unwire()

    def test_backup_success(self) -> None:
        with responses.RequestsMock() as rsps:
            rsps.post(
                f'https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database}:exportDocuments',
                status=200,
            )
            resp = self.client.post('/api/v1/backup/client')
            self.assertEqual(rsps.calls[0].request.headers['Authorization'], f'Bearer {self.access_token}')
            req_json = json.loads(cast(str, rsps.calls[0].request.body))
            self.assertTrue(
                cast(str, req_json['outputUriPrefix']).startswith(f'gs://{self.project_id}-backup/firestore/{self.database}/')
            )
        self.assertEqual(resp.status_code, 200)

    def test_backup_failure(self) -> None:
        with responses.RequestsMock() as rsps, self.assertLogs(level='ERROR'):
            rsps.post(
                f'https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database}:exportDocuments',
                status=500,
                json={'error': {'message': 'Internal Server Error'}},
            )
            resp = self.client.post('/api/v1/backup/client')

        self.assertEqual(resp.status_code, 500)

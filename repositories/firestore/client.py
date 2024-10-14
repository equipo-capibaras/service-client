import logging
from collections.abc import Generator  # pragma: no cover
from dataclasses import asdict
from enum import Enum
from typing import Any, cast

import dacite
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import (
    DocumentReference,
    DocumentSnapshot,
)

from models import Client
from repositories import ClientRepository

from .constants import UUID_UNASSIGNED


class FirestoreClientRepository(ClientRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def doc_to_user(self, doc: DocumentSnapshot) -> Client:
        return dacite.from_dict(
            data_class=Client,
            data={
                # Can never be None, as it's a Firestore DocumentSnapshot and therefore always exists
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def create(self, client: Client) -> None:
        client_dict = asdict(client)
        del client_dict['id']

        client_ref = self.db.collection('clients').document(client.id)
        client_ref.create(client_dict)

    def get(self, client_id: str) -> Client | None:
        if client_id == UUID_UNASSIGNED:
            return None

        client_doc = self.db.collection('clients').document(client_id).get()

        if not client_doc.exists:
            return None

        return self.doc_to_user(client_doc)

    def get_all(self) -> Generator[Client, None, None]:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection('clients').order_by('name').stream()
        for doc in stream:
            yield self.doc_to_user(doc)

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection('clients').stream()
        for client in stream:
            cast(DocumentReference, client.reference).delete()

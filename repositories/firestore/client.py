import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import DocumentReference

from models import Client
from repositories import ClientRepository

if TYPE_CHECKING:
    from collections.abc import Generator  # pragma: no cover

    from google.cloud.firestore_v1 import DocumentSnapshot  # pragma: no cover


class FirestoreClientRepository(ClientRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create(self, client: Client) -> None:
        client_dict = asdict(client)
        del client_dict['id']

        client_ref = self.db.collection('clients').document(client.id)
        client_ref.create(client_dict)

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection('clients').stream()
        for client in stream:
            cast(DocumentReference, client.reference).delete()

import logging
from collections.abc import Generator  # pragma: no cover
from dataclasses import asdict
from enum import Enum
from typing import Any, cast

import dacite
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore import transactional
from google.cloud.firestore_v1 import DocumentReference, DocumentSnapshot, Transaction
from google.cloud.firestore_v1.base_query import FieldFilter

from models import Client
from repositories import ClientRepository
from repositories.errors import DuplicateEmailError

from .constants import UUID_UNASSIGNED


class FirestoreClientRepository(ClientRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def doc_to_client(self, doc: DocumentSnapshot) -> Client:
        return dacite.from_dict(
            data_class=Client,
            data={
                # Can never be None, as it's a Firestore DocumentSnapshot and therefore always exists
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def _find_by_email(self, email: str, transaction: Transaction | None = None) -> DocumentSnapshot | None:
        docs = (
            self.db.collection('clients')
            .where(filter=FieldFilter('email_incidents', '==', email))  # type: ignore[no-untyped-call]
            .get(transaction=transaction)
        )

        if len(docs) == 0:
            return None

        if len(docs) > 1:
            self.logger.error('Multiple clients found with email %s', email)
            return None

        return cast(DocumentSnapshot, docs[0])

    def find_by_email(self, email: str) -> Client | None:
        doc = self._find_by_email(email)

        if doc is None:
            return None

        return self.doc_to_client(doc)

    def create(self, client: Client) -> None:
        client_dict = asdict(client)
        del client_dict['id']

        client_ref = self.db.collection('clients').document(client.id)

        @transactional  # type: ignore[misc]
        def create_client_transaction(transaction: Transaction, client_dict_trans: dict[str, Any]) -> None:
            if self._find_by_email(client_dict_trans['email_incidents'], transaction) is not None:
                raise DuplicateEmailError(client_dict_trans['email_incidents'])

            transaction.create(client_ref, client_dict_trans)

        create_client_transaction(self.db.transaction(), client_dict)

    def get(self, client_id: str) -> Client | None:
        if client_id == UUID_UNASSIGNED:
            return None

        client_doc = self.db.collection('clients').document(client_id).get()

        if not client_doc.exists:
            return None

        return self.doc_to_client(client_doc)

    def update(self, client: Client) -> None:
        client_dict = asdict(client)
        del client_dict['id']

        self.db.collection('clients').document(client.id).set(client_dict)

    def get_all(self) -> Generator[Client, None, None]:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection('clients').order_by('name').stream()
        for doc in stream:
            yield self.doc_to_client(doc)

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection('clients').stream()
        for client in stream:
            cast(DocumentReference, client.reference).delete()

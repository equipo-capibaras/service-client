import logging
from dataclasses import asdict
from enum import Enum
from typing import TYPE_CHECKING, cast

import dacite
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference, DocumentReference
from google.cloud.firestore_v1.base_query import FieldFilter

from models import Employee
from repositories import EmployeeRepository

if TYPE_CHECKING:
    from collections.abc import Generator  # pragma: no cover

    from google.cloud.firestore_v1 import DocumentSnapshot  # pragma: no cover


class FirestoreEmployeeRepository(EmployeeRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_by_email(self, email: str) -> Employee | None:
        docs = self.db.collection_group('employees').where(filter=FieldFilter('email', '==', email)).get()  # type: ignore[no-untyped-call]

        if len(docs) == 0:
            return None

        if len(docs) > 1:
            self.logger.error('Multiple employees found with email %s', email)
            return None

        doc = docs[0]
        return dacite.from_dict(
            data_class=Employee,
            data={
                **doc.to_dict(),
                'id': doc.id,
                'client_id': doc.reference.parent.parent.id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def create(self, employee: Employee) -> None:
        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']

        client_ref = self.db.collection('clients').document(employee.client_id)
        employee_ref = cast(CollectionReference, client_ref.collection('employees')).document(employee.id)
        employee_ref.create(employee_dict)

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection_group('employees').stream()
        for e in stream:
            cast(DocumentReference, e.reference).delete()

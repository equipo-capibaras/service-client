import contextlib
import logging
import secrets
from collections.abc import Generator
from dataclasses import asdict
from enum import Enum
from typing import Any, cast

import dacite
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore import transactional
from google.cloud.firestore_v1 import CollectionReference, DocumentReference, DocumentSnapshot, Query, Transaction
from google.cloud.firestore_v1.base_aggregation import AggregationResult
from google.cloud.firestore_v1.base_query import FieldFilter

from models import Employee
from repositories import DuplicateEmailError, EmployeeRepository

from .constants import UUID_UNASSIGNED


class FirestoreEmployeeRepository(EmployeeRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def doc_to_employee(self, doc: DocumentSnapshot) -> Employee:
        client_id = cast(DocumentReference, cast(CollectionReference, cast(DocumentReference, doc.reference).parent).parent).id
        if client_id == UUID_UNASSIGNED:
            client_id = None

        return dacite.from_dict(
            data_class=Employee,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
                'client_id': client_id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def get(self, employee_id: str, client_id: str | None) -> Employee | None:
        if client_id is None:
            client_id = UUID_UNASSIGNED

        client_ref = self.db.collection('clients').document(client_id)
        employee_ref = cast(CollectionReference, client_ref.collection('employees')).document(employee_id)
        doc = employee_ref.get()

        if not doc.exists:
            return None

        return self.doc_to_employee(doc)

    def get_all(self, client_id: str, offset: int | None, limit: int | None) -> Generator[Employee, None, None]:
        employees_ref = cast(CollectionReference, self.db.collection('clients').document(client_id).collection('employees'))
        query = employees_ref.order_by('invitation_date', direction=Query.DESCENDING)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        docs = query.stream()
        for doc in docs:
            yield self.doc_to_employee(doc)

    def _find_by_email(self, email: str, transaction: Transaction | None = None) -> DocumentSnapshot | None:
        docs = (
            self.db.collection_group('employees').where(filter=FieldFilter('email', '==', email)).get(transaction=transaction)  # type: ignore[no-untyped-call]
        )

        if len(docs) == 0:
            return None

        if len(docs) > 1:
            self.logger.error('Multiple employees found with email %s', email)
            return None

        return cast(DocumentSnapshot, docs[0])

    def find_by_email(self, email: str) -> Employee | None:
        doc = self._find_by_email(email)

        if doc is None:
            return None

        return self.doc_to_employee(doc)

    def create(self, employee: Employee) -> None:
        employee_dict = asdict(employee)
        del employee_dict['id']
        del employee_dict['client_id']

        client_id = UUID_UNASSIGNED if employee.client_id is None else employee.client_id

        client_ref = self.db.collection('clients').document(UUID_UNASSIGNED)
        with contextlib.suppress(AlreadyExists):
            client_ref.create({})

        client_ref = self.db.collection('clients').document(client_id)
        employee_ref = cast(CollectionReference, client_ref.collection('employees')).document(employee.id)

        @transactional  # type: ignore[misc]
        def create_employee_transaction(transaction: Transaction, employee_dict_trans: dict[str, Any]) -> None:
            if self._find_by_email(employee_dict_trans['email'], transaction) is not None:
                raise DuplicateEmailError(employee_dict_trans['email'])

            transaction.create(employee_ref, employee_dict_trans)

        create_employee_transaction(self.db.transaction(), employee_dict)

    def delete(self, employee_id: str, client_id: str | None) -> None:
        if client_id is None:
            client_id = UUID_UNASSIGNED

        client_ref = self.db.collection('clients').document(client_id)
        employee_ref = cast(CollectionReference, client_ref.collection('employees')).document(employee_id)

        employee_ref.delete()

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection_group('employees').stream()
        for e in stream:
            cast(DocumentReference, e.reference).delete()

    def count(self, client_id: str) -> int:
        client_ref = self.db.collection('clients').document(client_id)
        employees_ref = cast(CollectionReference, client_ref.collection('employees'))
        result = cast(AggregationResult, employees_ref.count().get()[0][0])  # type: ignore[no-untyped-call]
        return int(result.value)

    def get_agents_by_client(self, client_id: str) -> list[Employee]:
        # Obtain a reference to the client's collection of employees
        employees_ref = cast(CollectionReference, self.db.collection('clients').document(client_id).collection('employees'))

        # Query the employees collection for agents
        query = employees_ref.where('role', '==', 'agent')
        docs = query.stream()

        return [self.doc_to_employee(doc) for doc in docs]

    def get_random_agent(self, client_id: str) -> Employee | None:
        agents = self.get_agents_by_client(client_id)

        # If there are no agents, return None
        if not agents:
            return None

        return secrets.choice(agents)

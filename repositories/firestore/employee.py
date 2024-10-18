import contextlib
import logging
from collections.abc import Generator
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any, cast

import dacite
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore import transactional
from google.cloud.firestore_v1 import CollectionReference, DocumentReference, DocumentSnapshot, Query, Transaction
from google.cloud.firestore_v1.base_query import FieldFilter

from models import Employee
from models.employee import InvitationStatus
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

        # Obtiene invitation_status del documento y maneja el valor predeterminado si no está presente
        invitation_status_str = doc.get('invitation_status')
        if invitation_status_str is None:
            invitation_status = InvitationStatus.UNINVITED
        else:
            invitation_status = InvitationStatus(invitation_status_str)

        # Obtiene invitation_date y convierte al formato datetime si existe
        invitation_date_str = doc.get('invitation_date')
        invitation_date = datetime.fromisoformat(invitation_date_str) if invitation_date_str else None

        return dacite.from_dict(
            data_class=Employee,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
                'client_id': client_id,
                'invitation_status': invitation_status,
                'invitation_date': invitation_date,
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

        # Convert enums y fecha a valores adecuados para Firestore
        employee_dict['invitation_status'] = employee.invitation_status.value
        if employee.invitation_date is not None:
            employee_dict['invitation_date'] = employee.invitation_date.isoformat()

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

    def delete_all(self) -> None:
        stream: Generator[DocumentSnapshot, None, None] = self.db.collection_group('employees').stream()
        for e in stream:
            cast(DocumentReference, e.reference).delete()

    def count_by_client_id(self, client_id: str) -> int:
        """
        Cuenta el número total de empleados para un cliente específico.

        Args:
        client_id (str): ID del cliente para el cual contar los empleados.

        Returns:
        int: Número total de empleados.
        """
        client_ref = self.db.collection('clients').document(client_id)
        employees_ref = client_ref.collection('employees')
        total_employees = len(list(employees_ref.stream()))
        return total_employees

    def list_by_client_id(
        self, client_id: str, page_size: int, page_number: int = 1
    ) -> tuple[list[Employee], int]:
        """
        Lista los empleados de un cliente específico, ordenados por fecha de invitación descendente.

        La lista admite paginación por número de página.

        Args:
        client_id (str): ID del cliente para el cual listar los empleados.
        page_size (int): Cantidad de empleados por página (5, 10, 20).
        page_number (int): Número de la página a obtener (1 es la primera página).

        Returns:
        tuple[list[Employee], int]: Lista de empleados y el número total de empleados.
        """
        client_ref = self.db.collection('clients').document(client_id)
        query: Query = client_ref.collection('employees').order_by('invitation_date', direction=Query.DESCENDING)

        # Saltar los elementos para llegar a la página solicitada
        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)
        docs = query.stream()

        employees = [self.doc_to_employee(doc) for doc in docs]

        total_employees = self.count_by_client_id(client_id)
        return employees, total_employees

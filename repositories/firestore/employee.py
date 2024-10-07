import logging

from dacite import from_dict
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1.base_query import FieldFilter

from models import Employee
from repositories import EmployeeRepository


class FirestoreEmployeeRepository(EmployeeRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_employee_by_email(self, email: str) -> Employee | None:
        docs = self.db.collection_group('employees').where(filter=FieldFilter('email', '==', email)).get()  # type: ignore[no-untyped-call]

        if len(docs) == 0:
            return None

        if len(docs) > 1:
            self.logger.error('Multiple employees found with email %s', email)
            return None

        doc = docs[0]
        return from_dict(
            data_class=Employee,
            data={
                **doc.to_dict(),
                'id': doc.id,
                'client_id': doc.reference.parent.parent.id,
            },
        )

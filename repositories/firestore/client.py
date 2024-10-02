import logging
from google.cloud.firestore import Client as FirestoreClient  # type: ignore
from repositories import EmployeeRepository
from .util import delete_collection_recursive
import demo


class FirestoreClientRepository(EmployeeRepository):
    def __init__(self, database: str):
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def reset(self, load_demo_data: bool = False) -> None:
        delete_collection_recursive(self.db.collection('clients'))

        self.logger.info('Database cleared.')

        if load_demo_data:
            for c in demo.clients:
                client = c.copy()
                client_id = client.pop('id')
                employees = client.pop('employees')
                self.db.collection('clients').document(client_id).set(client)

                for e in employees:
                    employee = e.copy()
                    employee_id = employee.pop('id')
                    collection_employees = self.db.collection('clients').document(client_id).collection('employees')
                    collection_employees.document(employee_id).set(employee)

            self.logger.info('Demo data loaded.')

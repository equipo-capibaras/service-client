import os
from google.cloud.firestore import Client as FirestoreClient  # type: ignore

FIRESTORE_DB = os.getenv('FIRESTORE_DB') or '(default)'

db = FirestoreClient(database=FIRESTORE_DB)

print('#### Clients ####')
clients = db.collection('clients').stream()
for client in clients:
    print(f'{client.id}')

    for k, v in client.to_dict().items():
        print(f'    {k}: {v}')
    print('')

    print('    #### Employees ####')
    employees = db.collection('clients').document(client.id).collection('employees').stream()
    for employee in employees:
        print(f'    {employee.id}')

        for k, v in employee.to_dict().items():
            print(f'        {k}: {v}')
        print('')
    print('')

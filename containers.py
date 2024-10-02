from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from repositories.firestore import FirestoreClientRepository, FirestoreEmployeeRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=["blueprints"])
    config = providers.Configuration()

    client_repo = providers.ThreadSafeSingleton(FirestoreClientRepository, database=config.firestore.database)
    employee_repo = providers.ThreadSafeSingleton(FirestoreEmployeeRepository, database=config.firestore.database)

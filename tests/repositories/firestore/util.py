from google.auth.exceptions import GoogleAuthError
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]


def firestore_available(database: str) -> bool:
    try:
        FirestoreClient(database=database)
    except GoogleAuthError:
        return False

    return True

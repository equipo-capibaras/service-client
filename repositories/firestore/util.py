from typing import Generator
from google.cloud.firestore_v1 import CollectionReference, DocumentReference


def delete_collection_recursive(collection: CollectionReference) -> None:
    batch_size = 100

    while True:
        if batch_size == 0:
            break

        docs: Generator[DocumentReference, DocumentReference, None] = collection.list_documents(page_size=batch_size)
        deleted = 0

        for doc in docs:
            sub_collections: Generator[CollectionReference, CollectionReference, None] = doc.collections()
            for sub_collection in sub_collections:
                delete_collection_recursive(sub_collection)

            doc.delete()
            deleted = deleted + 1

        if deleted < batch_size:
            break

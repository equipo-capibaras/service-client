# ruff: noqa: INP001, T201
import os
from collections.abc import Generator
from typing import Any, cast

from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference, DocumentReference

FIRESTORE_DB = os.getenv('FIRESTORE_DB') or '(default)'

db = FirestoreClient(database=FIRESTORE_DB)


def print_collection(collection: CollectionReference, indent: int) -> None:
    print(f'{"    " * indent}#### {collection.id} ####')
    docs = collection.get()
    for doc in docs:
        print(f'{"    " * indent}{doc.id}')

        for k, v in cast(dict[str, Any], doc.to_dict()).items():
            print(f'{"    " * (indent + 1)}{k}: {v}')
        print()

        gen_subcollections: Generator[CollectionReference, None, None] = cast(DocumentReference, doc.reference).collections()
        for c in gen_subcollections:
            print_collection(c, indent + 1)


gen_collections: Generator[CollectionReference, None, None] = db.collections()
for collection in gen_collections:
    print_collection(collection, 0)

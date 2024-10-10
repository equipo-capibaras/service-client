from collections.abc import Generator

from models import Client


class ClientRepository:
    def create(self, client: Client) -> None:
        raise NotImplementedError  # pragma: no cover

    def get_all(self) -> Generator[Client, None, None]:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover

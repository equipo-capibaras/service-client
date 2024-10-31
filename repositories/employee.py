from collections.abc import Generator

from models import Employee


class EmployeeRepository:
    def get(self, employee_id: str, client_id: str | None) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

    def get_all(self, client_id: str, offset: int | None, limit: int | None) -> Generator[Employee, None, None]:
        raise NotImplementedError  # pragma: no cover

    def find_by_email(self, email: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

    def create(self, employee: Employee) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete(self, employee_id: str, client_id: str | None) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def count(self, client_id: str) -> int:
        raise NotImplementedError  # pragma: no cover

    def get_agents_by_client(self, client_id: str) -> list[Employee]:
        raise NotImplementedError  # pragma: no cover

    def get_random_agent(self, client_id: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

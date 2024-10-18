from models import Employee


class EmployeeRepository:
    def get(self, employee_id: str, client_id: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

    def find_by_email(self, email: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

    def create(self, employee: Employee) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def count_by_client_id(self, client_id: str) -> int:
        raise NotImplementedError  # pragma: no cover

    def list_by_client_id(
            self, client_id: str, page_size: int, page_number: int = 1
    ) -> tuple[list[Employee], int]:
        raise NotImplementedError  # pragma: no cover

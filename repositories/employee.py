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

    def list_by_client_id(
            self,
            client_id: str,
            page_size: int,
            page_token: str | None = None
    ) -> tuple[list[Employee], str | None]:
        raise NotImplementedError

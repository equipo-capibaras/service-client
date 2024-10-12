from models import Employee


class EmployeeRepository:
    def find_by_email(self, email: str) -> Employee | None:
        raise NotImplementedError  # pragma: no cover

    def create(self, employee: Employee) -> None:
        raise NotImplementedError  # pragma: no cover

    def delete_all(self) -> None:
        raise NotImplementedError  # pragma: no cover

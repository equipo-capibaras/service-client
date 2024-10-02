from models import Employee


class EmployeeRepository:
    def find_employee_by_email(self, email: str) -> Employee | None:
        raise NotImplementedError

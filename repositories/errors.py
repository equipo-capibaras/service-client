class DuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"A user with the email '{email}' already exists.")
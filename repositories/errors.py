class DuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"A user with the email '{email}' already exists.")


class UnexpectedError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f'An unexpected error occurred: {message}')

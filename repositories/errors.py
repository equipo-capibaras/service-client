class UnexpectedError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f'An unexpected error occurred: {message}')

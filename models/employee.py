from dataclasses import dataclass


@dataclass
class Employee:
    id: str
    client_id: str
    name: str
    email: str
    password: str
    role: str

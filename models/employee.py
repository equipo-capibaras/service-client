from dataclasses import dataclass

from .role import Role


@dataclass
class Employee:
    id: str
    client_id: str
    name: str
    email: str
    password: str
    role: Role

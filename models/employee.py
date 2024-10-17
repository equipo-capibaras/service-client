from dataclasses import dataclass
from enum import Enum

from .role import Role


class InvitationStatus(Enum):
    UNINVITED = 'uninvited'
    PENDING = 'pending'
    ACCEPTED = 'accepted'


@dataclass
class Employee:
    id: str
    client_id: str | None
    name: str
    email: str
    password: str
    role: Role
    invitation_status: InvitationStatus = InvitationStatus.UNINVITED

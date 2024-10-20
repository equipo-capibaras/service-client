from dataclasses import dataclass
from datetime import datetime

from .invitation_status import InvitationStatus
from .role import Role


@dataclass
class Employee:
    id: str
    client_id: str | None
    name: str
    email: str
    password: str
    role: Role
    invitation_status: InvitationStatus
    invitation_date: datetime

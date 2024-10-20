from dataclasses import dataclass

from .plan import Plan


@dataclass
class Client:
    id: str
    name: str
    plan: Plan | None
    email_incidents: str

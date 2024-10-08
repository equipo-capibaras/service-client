from dataclasses import dataclass

from .plan import Plan


@dataclass
class Client:
    id: str
    name: str
    plan: Plan
    email_incidents: str

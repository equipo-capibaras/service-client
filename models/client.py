from dataclasses import dataclass


@dataclass
class Client:
    id: str
    name: str
    plan: str
    emailIncidents: str

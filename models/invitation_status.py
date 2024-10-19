from enum import StrEnum


class InvitationStatus(StrEnum):
    UNINVITED = 'uninvited'
    PENDING = 'pending'
    ACCEPTED = 'accepted'

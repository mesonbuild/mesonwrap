import dataclasses
import enum


class TicketType(enum.Enum):
    WRAPDB_ISSUE = 'wrapdb_issue'
    PULL_REQUEST = 'pull_request'
    WRAP_ISSUE = 'wrap_issue'


@dataclasses.dataclass
class Reference:
    title: str
    url: str


@dataclasses.dataclass
class Ticket(Reference):
    project: Reference
    type: TicketType
    author: Reference
    created_at: str
    updated_at: str

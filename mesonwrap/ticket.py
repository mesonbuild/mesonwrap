import dataclasses
import enum


class TicketType(enum.Enum):
    # Must match tickets.css classes
    WRAPDB_ISSUE = 'wrapdb-issue'
    PULL_REQUEST = 'pull-request'
    WRAP_ISSUE = 'wrap-issue'


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

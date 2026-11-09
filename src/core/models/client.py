from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class Client:
    id: str
    company_name: str
    tax_id: str
    contact_name: str
    contact_phone: str
    contact_email: str
    address: str
    contract_number: str
    contract_start: str
    contract_end: str
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def name(self) -> str:
        return self.company_name

    @property
    def phone(self) -> str:
        return self.contact_phone

    @property
    def email(self) -> str:
        return self.contact_email

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Client:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class InstallationSite:
    id: str
    client_id: str
    name: str
    address: str
    contact_person: str
    contact_phone: str
    contact_email: str
    description: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> InstallationSite:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

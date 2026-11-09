"""
Technician Model for ControlHVAC CMMS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .enums import TechnicianStatus, TechnicianSpecialty


@dataclass
class Technician:
    id: str
    code: str  # RUT or worker identification code
    first_name: str
    last_name: str
    specialty: str = TechnicianSpecialty.HVAC.value
    phone: str = ""
    email: str = ""
    license_number: str = ""  # SEC license or certification
    status: str = TechnicianStatus.ACTIVE.value
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        return self.status == TechnicianStatus.ACTIVE.value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "specialty": self.specialty,
            "phone": self.phone,
            "email": self.email,
            "license_number": self.license_number,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Technician:
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            specialty=data.get("specialty", TechnicianSpecialty.HVAC.value),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            license_number=data.get("license_number", ""),
            status=data.get("status", TechnicianStatus.ACTIVE.value),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

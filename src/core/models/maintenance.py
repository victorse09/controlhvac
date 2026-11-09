from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional

@dataclass
class MaintenanceSchedule:
    id: str
    equipment_id: str
    equipment_tag: str
    site_id: str
    client_id: str
    title: str
    maintenance_type: str
    frequency: str
    is_one_time: bool = False
    scheduled_date: str = ""
    day_of_week: int = 0
    day_of_month: int = 1
    month_of_year: int = 1
    preferred_hour: int = 8
    assigned_technician: str = ""
    checklist_template: list = field(default_factory=list)
    is_active: bool = True
    last_execution: str = ""
    next_execution: str = ""
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
    def frequency_days(self) -> int:
        try:
            from src.core.models.enums import MaintenanceFrequency
            return MaintenanceFrequency(self.frequency).get_days()
        except Exception:
            return 30

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MaintenanceSchedule:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def calculate_next_execution(self, from_date: str) -> str:
        """
        Calculate next execution date based on frequency.
        from_date: ISO 8601 date string.
        Returns ISO 8601 date string.
        """
        try:
            date_obj = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError:
            date_obj = datetime.now(timezone.utc)
            
        freq = self.frequency
        if freq == "WEEKLY":
            next_date = date_obj + timedelta(days=7)
        elif freq == "BIWEEKLY":
            next_date = date_obj + timedelta(days=14)
        elif freq == "MONTHLY":
            next_date = date_obj + timedelta(days=30)
        elif freq == "QUARTERLY":
            next_date = date_obj + timedelta(days=90)
        elif freq == "SEMI_ANNUAL":
            next_date = date_obj + timedelta(days=180)
        elif freq == "ANNUAL":
            next_date = date_obj + timedelta(days=365)
        else:
            # Fallback for unknown frequency
            next_date = date_obj + timedelta(days=30)
            
        return next_date.isoformat()

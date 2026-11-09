from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.core.models.enums import (
    IncidentType, IncidentSeverity, IncidentStatus,
    INCIDENT_TYPE_LABELS, INCIDENT_SEVERITY_LABELS, INCIDENT_STATUS_LABELS
)

@dataclass
class Incident:
    id: str
    client_id: str
    site_id: str
    equipment_id: str
    equipment_tag: str = ""
    title: str = ""
    incident_type: IncidentType | str = IncidentType.AVERIA
    severity: IncidentSeverity | str = IncidentSeverity.MEDIA
    status: IncidentStatus | str = IncidentStatus.REPORTADA
    reported_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    description: str = ""
    diagnosis: str = ""
    action_taken: str = ""
    technician: str = ""
    parts_used: List[str] = field(default_factory=list)
    labor_hours: float = 0.0
    cost_estimate: float = 0.0
    resolved_date: str = ""
    work_order_id: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        if isinstance(self.incident_type, IncidentType):
            d['incident_type'] = self.incident_type.value
        if isinstance(self.severity, IncidentSeverity):
            d['severity'] = self.severity.value
        if isinstance(self.status, IncidentStatus):
            d['status'] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Incident":
        if not data:
            return None
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        
        # Parse enums safely
        if 'incident_type' in valid_fields and isinstance(valid_fields['incident_type'], str):
            try:
                valid_fields['incident_type'] = IncidentType(valid_fields['incident_type'])
            except ValueError:
                pass

        if 'severity' in valid_fields and isinstance(valid_fields['severity'], str):
            try:
                valid_fields['severity'] = IncidentSeverity(valid_fields['severity'])
            except ValueError:
                pass

        if 'status' in valid_fields and isinstance(valid_fields['status'], str):
            try:
                valid_fields['status'] = IncidentStatus(valid_fields['status'])
            except ValueError:
                pass

        return cls(**valid_fields)

    @property
    def type_display(self) -> str:
        itype = self.incident_type
        if isinstance(itype, IncidentType):
            return INCIDENT_TYPE_LABELS.get(itype, itype.value)
        return INCIDENT_TYPE_LABELS.get(IncidentType(itype), str(itype)) if str(itype) in [e.value for e in IncidentType] else str(itype)

    @property
    def severity_display(self) -> str:
        sev = self.severity
        if isinstance(sev, IncidentSeverity):
            return INCIDENT_SEVERITY_LABELS.get(sev, sev.value)
        return INCIDENT_SEVERITY_LABELS.get(IncidentSeverity(sev), str(sev)) if str(sev) in [e.value for e in IncidentSeverity] else str(sev)

    @property
    def status_display(self) -> str:
        st = self.status
        if isinstance(st, IncidentStatus):
            return INCIDENT_STATUS_LABELS.get(st, st.value)
        return INCIDENT_STATUS_LABELS.get(IncidentStatus(st), str(st)) if str(st) in [e.value for e in IncidentStatus] else str(st)

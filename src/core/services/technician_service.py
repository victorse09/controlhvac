"""
Technician Service for ControlHVAC CMMS.
"""
from __future__ import annotations

import os
import shutil
from typing import Dict, List, Optional

from src.core.models.enums import TechnicianStatus
from src.core.models.technician import Technician
from src.data.json_storage import JsonStorageEngine


class TechnicianService:
    """Service for managing technicians."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service

    def save_technician(self, technician: Technician) -> Technician:
        """Save or update a technician."""
        self.storage.save_document(
            "technicians", technician.id, "technician.json", technician.to_dict()
        )
        self.storage.update_index("technicians", technician.id, {
            "code": technician.code,
            "full_name": technician.full_name,
            "specialty": technician.specialty,
            "phone": technician.phone,
            "email": technician.email,
            "status": technician.status,
            "updated_at": technician.updated_at,
        })
        return technician

    def get_technician(self, technician_id: str) -> Optional[Technician]:
        """Get technician by ID."""
        data = self.storage.load_document("technicians", technician_id, "technician.json")
        return Technician.from_dict(data) if data else None

    def get_all_technicians(self) -> List[Technician]:
        """Get all technicians."""
        technicians = []
        index = self.storage.get_index("technicians")
        for tech_id in index:
            tech = self.get_technician(tech_id)
            if tech:
                technicians.append(tech)
        technicians.sort(key=lambda t: t.full_name.lower())
        return technicians

    def get_active_technicians(self) -> List[Technician]:
        """Get active technicians only."""
        return [t for t in self.get_all_technicians() if t.is_active]

    def get_technician_names(self) -> List[str]:
        """Get list of active technician names formatted as 'First Last (RUT)' or 'First Last'."""
        names = []
        for t in self.get_active_technicians():
            if t.code:
                names.append(f"{t.full_name} ({t.code})")
            else:
                names.append(t.full_name)
        return names

    def delete_technician(self, technician_id: str) -> bool:
        """Delete technician and send to recycle bin."""
        tech = self.get_technician(technician_id)
        if not tech:
            return False

        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(
                tech.id, "TECHNICIAN", tech.full_name, tech.to_dict()
            )

        tech_dir = os.path.join(self.storage.base_path, "technicians", technician_id)
        try:
            if os.path.exists(tech_dir):
                shutil.rmtree(tech_dir)
        except Exception:
            return False

        self.storage.remove_from_index("technicians", technician_id)
        return True

    def search_technicians(
        self,
        query: str = "",
        specialty: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Technician]:
        """Filter and search technicians."""
        results = self.get_all_technicians()
        query = query.strip().lower()

        if query:
            results = [
                t for t in results
                if (
                    query in t.full_name.lower() or
                    query in t.code.lower() or
                    query in (t.phone or "").lower() or
                    query in (t.email or "").lower() or
                    query in (t.license_number or "").lower() or
                    query in (t.notes or "").lower()
                )
            ]

        if specialty:
            results = [t for t in results if t.specialty == specialty]

        if status:
            results = [t for t in results if t.status == status]

        return results

    def get_stats(self) -> Dict[str, int]:
        """Get quick summary statistics for technicians."""
        all_techs = self.get_all_technicians()
        total = len(all_techs)
        active = sum(1 for t in all_techs if t.status == TechnicianStatus.ACTIVE.value)
        on_leave = sum(1 for t in all_techs if t.status in [TechnicianStatus.ON_LEAVE.value, TechnicianStatus.VACATION.value])
        inactive = sum(1 for t in all_techs if t.status == TechnicianStatus.INACTIVE.value)
        return {
            "total": total,
            "active": active,
            "on_leave": on_leave,
            "inactive": inactive,
        }

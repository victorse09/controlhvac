import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.core.models.incident import Incident
from src.core.models.enums import IncidentType, IncidentSeverity, IncidentStatus, EquipmentStatus
from src.data.json_storage import JsonStorageEngine

class IncidentService:
    """Service for managing equipment breakdowns, observations and repair logs."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service

    def _generate_id(self) -> str:
        year = datetime.now().year
        all_incidents = self.get_all_incidents()
        existing_nums = []
        for inc in all_incidents:
            if inc.id.startswith(f"INC-{year}-"):
                try:
                    num = int(inc.id.split("-")[-1])
                    existing_nums.append(num)
                except ValueError:
                    pass
        next_num = max(existing_nums, default=0) + 1
        return f"INC-{year}-{next_num:04d}"

    def save_incident(self, incident: Incident) -> Incident:
        if not incident.id:
            incident.id = self._generate_id()
        incident.updated_at = datetime.now().isoformat()
        
        self.storage.save_document("incidents", incident.id, "incident.json", incident.to_dict())
        
        type_val = incident.incident_type.value if hasattr(incident.incident_type, 'value') else str(incident.incident_type)
        sev_val = incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity)
        st_val = incident.status.value if hasattr(incident.status, 'value') else str(incident.status)

        self.storage.update_index("incidents", incident.id, {
            "title": incident.title,
            "equipment_tag": incident.equipment_tag,
            "equipment_id": incident.equipment_id,
            "site_id": incident.site_id,
            "client_id": incident.client_id,
            "incident_type": type_val,
            "severity": sev_val,
            "status": st_val,
            "reported_date": incident.reported_date,
            "resolved_date": incident.resolved_date,
            "work_order_id": getattr(incident, 'work_order_id', '') or "",
            "technician": incident.technician
        })
        return incident

    def resolve_incident_from_work_order(self, incident_id: str, work_order) -> bool:
        """Marks an incident as RESOLVED when associated work order completes."""
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        incident.status = IncidentStatus.RESUELTA
        incident.resolved_date = getattr(work_order, 'completed_date', '') or datetime.now().strftime("%Y-%m-%d")
        incident.work_order_id = work_order.id
        if getattr(work_order, 'work_performed', ''):
            incident.action_taken = work_order.work_performed
        if getattr(work_order, 'assigned_technician', ''):
            incident.technician = work_order.assigned_technician
        if getattr(work_order, 'materials_used', []):
            mat_names = []
            for m in work_order.materials_used:
                if isinstance(m, dict):
                    mat_names.append(f"{m.get('quantity', 1)} {m.get('unit', 'unid')} {m.get('name', '')}")
                else:
                    mat_names.append(str(m))
            incident.parts_used = mat_names
            
        current_notes = incident.notes or ""
        guide_note = f"[Avería resuelta y cerrada mediante Guía/OT {work_order.id} ({datetime.now().strftime('%Y-%m-%d %H:%M')})]"
        if guide_note not in current_notes:
            incident.notes = f"{current_notes}\n{guide_note}".strip()
        self.save_incident(incident)
        return True

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        data = self.storage.load_document("incidents", incident_id, "incident.json")
        return Incident.from_dict(data) if data else None

    def get_all_incidents(self) -> List[Incident]:
        incidents = []
        index = self.storage.get_index("incidents")
        for inc_id in index:
            inc = self.get_incident(inc_id)
            if inc:
                incidents.append(inc)
        
        # Sort by reported_date descending
        incidents.sort(key=lambda x: x.reported_date or "", reverse=True)
        return incidents

    def get_incidents_for_equipment(self, equipment_id: str) -> List[Incident]:
        return [inc for inc in self.get_all_incidents() if inc.equipment_id == equipment_id]

    def get_incidents_for_site(self, site_id: str) -> List[Incident]:
        return [inc for inc in self.get_all_incidents() if inc.site_id == site_id]

    def get_incidents_for_client(self, client_id: str) -> List[Incident]:
        return [inc for inc in self.get_all_incidents() if inc.client_id == client_id]

    def delete_incident(self, incident_id: str) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False

        if self.recycle_bin_service:
            try:
                self.recycle_bin_service.recycle_item(
                    original_id=incident_id,
                    item_type="incident",
                    display_name=f"{incident.id}: {incident.title or incident.equipment_tag}",
                    payload=incident.to_dict(),
                    extra_info={
                        "equipment_tag": incident.equipment_tag,
                        "type": incident.incident_type.value if hasattr(incident.incident_type, 'value') else str(incident.incident_type),
                        "status": incident.status.value if hasattr(incident.status, 'value') else str(incident.status)
                    }
                )
            except Exception as e:
                print(f"Error recycling incident: {e}")

        self.storage.delete_directory(f"incidents/{incident_id}")
        self.storage.remove_from_index("incidents", incident_id)
        return True

    def sync_equipment_status_from_incident(self, incident: Incident, equipment_service) -> None:
        """Updates the parent equipment status according to this incident's current status and severity."""
        if not equipment_service or not incident.equipment_id:
            return

        try:
            eq = equipment_service.get_equipment(incident.equipment_id)
            if not eq:
                return

            st_val = incident.status.value if hasattr(incident.status, 'value') else str(incident.status)
            sev_val = incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity)

            if st_val in ["RESUELTA", "CANCELADA"]:
                # Check if there are other open incidents on this equipment
                other_open = [
                    i for i in self.get_incidents_for_equipment(eq.id)
                    if i.id != incident.id and (i.status.value if hasattr(i.status, 'value') else str(i.status)) not in ["RESUELTA", "CANCELADA"]
                ]
                if not other_open:
                    eq.status = EquipmentStatus.OPERATIONAL
                    equipment_service.save_equipment(eq)
                else:
                    # Sync to highest priority open incident
                    top_inc = other_open[0]
                    top_st = top_inc.status.value if hasattr(top_inc.status, 'value') else str(top_inc.status)
                    top_sev = top_inc.severity.value if hasattr(top_inc.severity, 'value') else str(top_inc.severity)
                    if top_st in ["EN_REPARACION", "ESPERANDO_REPUESTOS"]:
                        eq.status = EquipmentStatus.IN_MAINTENANCE
                    elif top_sev == "CRITICA" or top_st == "REPORTADA":
                        eq.status = EquipmentStatus.FAULT
                    else:
                        eq.status = EquipmentStatus.WARNING
                    equipment_service.save_equipment(eq)
            elif st_val in ["EN_REPARACION", "ESPERANDO_REPUESTOS"]:
                eq.status = EquipmentStatus.IN_MAINTENANCE
                equipment_service.save_equipment(eq)
            elif st_val == "EN_DIAGNOSTICO":
                eq.status = EquipmentStatus.WARNING
                equipment_service.save_equipment(eq)
            elif st_val == "REPORTADA":
                if sev_val == "CRITICA":
                    eq.status = EquipmentStatus.FAULT
                elif sev_val in ["ALTA", "MEDIA"]:
                    eq.status = EquipmentStatus.WARNING
                else:
                    eq.status = EquipmentStatus.FAULT
                equipment_service.save_equipment(eq)
        except Exception as e:
            print(f"Error syncing equipment status from incident: {e}")

    def sync_incident_from_equipment_change(self, equipment, old_status: str = None) -> None:
        """When an equipment's status changes in equipment view/dialog, update or resolve associated incidents."""
        try:
            st_raw = equipment.status.value if hasattr(equipment.status, 'value') else str(equipment.status)
            open_incidents = [
                i for i in self.get_incidents_for_equipment(equipment.id)
                if (i.status.value if hasattr(i.status, 'value') else str(i.status)) not in ["RESUELTA", "CANCELADA"]
            ]

            now_date = datetime.now().strftime("%Y-%m-%d")

            if st_raw in ["OPERATIONAL", "Operativo"]:
                # Resolve all active incidents
                for inc in open_incidents:
                    inc.status = IncidentStatus.RESUELTA
                    if not inc.resolved_date:
                        inc.resolved_date = now_date
                    if not inc.action_taken:
                        inc.action_taken = "Equipo marcado como Operativo desde Ficha de Equipo."
                    self.save_incident(inc)

            elif st_raw in ["FAULT", "En Falla"]:
                if open_incidents:
                    for inc in open_incidents:
                        if (inc.status.value if hasattr(inc.status, 'value') else str(inc.status)) == "RESUELTA":
                            inc.status = IncidentStatus.REPORTADA
                        inc.severity = IncidentSeverity.CRITICA
                        self.save_incident(inc)
                else:
                    # Create new incident
                    notes_str = (getattr(equipment, 'notes', '') or '').strip()
                    new_inc = Incident(
                        id=self._generate_id(),
                        client_id=equipment.client_id,
                        site_id=equipment.site_id,
                        equipment_id=equipment.id,
                        equipment_tag=equipment.tag,
                        title=f"Avería en {equipment.tag}",
                        incident_type=IncidentType.AVERIA,
                        severity=IncidentSeverity.CRITICA,
                        status=IncidentStatus.REPORTADA,
                        reported_date=now_date,
                        description=f"Equipo cambiado a estado 'En Falla'. Ubicación: {equipment.location_description or getattr(equipment, 'floor_area', '') or 'Sin especificar'}",
                        diagnosis=notes_str,
                        notes=notes_str or "Generado automáticamente por cambio de estado a 'En Falla'."
                    )
                    self.save_incident(new_inc)

            elif st_raw in ["WARNING", "En Observación"]:
                if open_incidents:
                    for inc in open_incidents:
                        if (inc.status.value if hasattr(inc.status, 'value') else str(inc.status)) == "REPORTADA":
                            inc.status = IncidentStatus.EN_DIAGNOSTICO
                        inc.severity = IncidentSeverity.MEDIA
                        self.save_incident(inc)
                else:
                    notes_str = (getattr(equipment, 'notes', '') or '').strip()
                    new_inc = Incident(
                        id=self._generate_id(),
                        client_id=equipment.client_id,
                        site_id=equipment.site_id,
                        equipment_id=equipment.id,
                        equipment_tag=equipment.tag,
                        title=f"Observación en {equipment.tag}",
                        incident_type=IncidentType.OBSERVACION,
                        severity=IncidentSeverity.MEDIA,
                        status=IncidentStatus.EN_DIAGNOSTICO,
                        reported_date=now_date,
                        description=f"Equipo cambiado a estado 'En Observación'.",
                        diagnosis=notes_str,
                        notes=notes_str or "Generado automáticamente por cambio de estado a 'En Observación'."
                    )
                    self.save_incident(new_inc)

            elif st_raw in ["IN_MAINTENANCE", "En Mantenimiento"]:
                if open_incidents:
                    for inc in open_incidents:
                        inc.status = IncidentStatus.EN_REPARACION
                        self.save_incident(inc)
                else:
                    notes_str = (getattr(equipment, 'notes', '') or '').strip()
                    new_inc = Incident(
                        id=self._generate_id(),
                        client_id=equipment.client_id,
                        site_id=equipment.site_id,
                        equipment_id=equipment.id,
                        equipment_tag=equipment.tag,
                        title=f"Mantenimiento / Reparación en {equipment.tag}",
                        incident_type=IncidentType.AVERIA,
                        severity=IncidentSeverity.MEDIA,
                        status=IncidentStatus.EN_REPARACION,
                        reported_date=now_date,
                        description=f"Equipo colocado en estado 'En Mantenimiento'.",
                        diagnosis=notes_str,
                        notes=notes_str or "Generado automáticamente por estado 'En Mantenimiento'."
                    )
                    self.save_incident(new_inc)

            elif st_raw in ["DECOMMISSIONED", "Fuera de Servicio"]:
                if open_incidents:
                    for inc in open_incidents:
                        inc.severity = IncidentSeverity.ALTA
                        self.save_incident(inc)
                else:
                    notes_str = (getattr(equipment, 'notes', '') or '').strip()
                    new_inc = Incident(
                        id=self._generate_id(),
                        client_id=equipment.client_id,
                        site_id=equipment.site_id,
                        equipment_id=equipment.id,
                        equipment_tag=equipment.tag,
                        title=f"Equipo fuera de servicio: {equipment.tag}",
                        incident_type=IncidentType.AVERIA,
                        severity=IncidentSeverity.ALTA,
                        status=IncidentStatus.REPORTADA,
                        reported_date=now_date,
                        description=f"Equipo retirado o fuera de servicio.",
                        diagnosis=notes_str,
                        notes=notes_str or "Generado automáticamente al dejar fuera de servicio."
                    )
                    self.save_incident(new_inc)
        except Exception as e:
            print(f"Error syncing incident from equipment change: {e}")

    def sync_from_existing_equipment(self, equipment_service) -> int:
        """Auto-generate incident records for any existing equipment in FAULT, WARNING or DECOMMISSIONED status."""
        if not equipment_service:
            return 0

        existing_eqs = equipment_service.get_all_equipment()
        existing_incidents = self.get_all_incidents()
        
        # Map equipment_id to active incidents
        eq_incident_map = {}
        for inc in existing_incidents:
            eq_incident_map.setdefault(inc.equipment_id, []).append(inc)

        created_count = 0
        for eq in existing_eqs:
            st_raw = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
            eq_notes_str = (getattr(eq, 'notes', '') or '').strip()

            # If equipment has notes, ensure existing incidents for this equipment have them
            for existing_inc in eq_incident_map.get(eq.id, []):
                if eq_notes_str and (not existing_inc.notes or "Generado automáticamente" in existing_inc.notes):
                    existing_inc.notes = eq_notes_str
                    if not existing_inc.diagnosis:
                        existing_inc.diagnosis = eq_notes_str
                    self.save_incident(existing_inc)

            if st_raw in ["FAULT", "En Falla", "WARNING", "En Observación", "DECOMMISSIONED", "Fuera de Servicio"]:
                has_active = any(
                    (i.status.value if hasattr(i.status, 'value') else str(i.status)) not in ["RESUELTA", "CANCELADA"]
                    for i in eq_incident_map.get(eq.id, [])
                )
                if not has_active:
                    if st_raw in ["FAULT", "En Falla"]:
                        itype = IncidentType.AVERIA
                        sev = IncidentSeverity.CRITICA
                        title = f"Avería reportada en {eq.tag}"
                        desc = f"Equipo registrado con estado 'En Falla'. Ubicación: {eq.location_description or getattr(eq, 'floor_area', '') or 'Sin especificar'}"
                    elif st_raw in ["WARNING", "En Observación"]:
                        itype = IncidentType.OBSERVACION
                        sev = IncidentSeverity.MEDIA
                        title = f"Observación preventiva en {eq.tag}"
                        desc = f"Equipo registrado con estado 'En Observación'. Requiere revisión técnica."
                    else: # DECOMMISSIONED
                        itype = IncidentType.AVERIA
                        sev = IncidentSeverity.ALTA
                        title = f"Equipo fuera de servicio: {eq.tag}"
                        desc = f"Equipo retirado o fuera de servicio."

                    if eq_notes_str:
                        desc += f"\nNotas del equipo: {eq_notes_str}"

                    final_notes = eq_notes_str if eq_notes_str else "Generado automáticamente a partir del estado actual del equipo en el sistema."

                    new_inc = Incident(
                        id=self._generate_id(),
                        client_id=eq.client_id,
                        site_id=eq.site_id,
                        equipment_id=eq.id,
                        equipment_tag=eq.tag,
                        title=title,
                        incident_type=itype,
                        severity=sev,
                        status=IncidentStatus.REPORTADA,
                        reported_date=datetime.now().strftime("%Y-%m-%d"),
                        description=desc,
                        diagnosis=eq_notes_str,
                        notes=final_notes
                    )
                    self.save_incident(new_inc)
                    eq_incident_map.setdefault(eq.id, []).append(new_inc)
                    created_count += 1

        return created_count


import os
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.core.models.equipment import HVACEquipment
from src.core.models.enums import EquipmentStatus, SystemType
from src.data.json_storage import JsonStorageEngine


class EquipmentService:
    """Service for managing HVAC equipment."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service

    def save_equipment(self, equipment: HVACEquipment) -> HVACEquipment:
        self.storage.save_document("equipment", equipment.id, "equipment.json", equipment.to_dict())
        self.storage.update_index("equipment", equipment.id, {
            "tag": equipment.tag,
            "site_id": equipment.site_id,
            "client_id": equipment.client_id,
            "bms_id": getattr(equipment, 'bms_id', ''),
            "bms_status": getattr(equipment, 'bms_status', 'Operativo') or 'Operativo',
            "floor_area": getattr(equipment, 'floor_area', ''),
            "system_type": equipment.system_type.value if hasattr(equipment.system_type, 'value') else equipment.system_type,
            "status": equipment.status.value if hasattr(equipment.status, 'value') else equipment.status
        })
        return equipment

    def get_equipment(self, equipment_id: str) -> Optional[HVACEquipment]:
        data = self.storage.load_document("equipment", equipment_id, "equipment.json")
        return HVACEquipment.from_dict(data) if data else None

    def get_all_equipment(self) -> List[HVACEquipment]:
        equipment_list = []
        index = self.storage.get_index("equipment")
        for eq_id in index:
            eq = self.get_equipment(eq_id)
            if eq:
                equipment_list.append(eq)
        return equipment_list

    def get_equipment_for_site(self, site_id: str) -> List[HVACEquipment]:
        return [eq for eq in self.get_all_equipment() if eq.site_id == site_id]

    def get_equipment_for_client(self, client_id: str) -> List[HVACEquipment]:
        return [eq for eq in self.get_all_equipment() if eq.client_id == client_id]

    def get_equipment_by_type(self, system_type: str) -> List[HVACEquipment]:
        # Handle both enum and string
        sys_type_val = system_type.value if hasattr(system_type, 'value') else system_type
        return [eq for eq in self.get_all_equipment() 
                if (eq.system_type.value if hasattr(eq.system_type, 'value') else eq.system_type) == sys_type_val]

    def get_equipment_by_status(self, status: str) -> List[HVACEquipment]:
        status_val = status.value if hasattr(status, 'value') else status
        return [eq for eq in self.get_all_equipment() 
                if (eq.status.value if hasattr(eq.status, 'value') else eq.status) == status_val]

    def set_equipment_operational(self, equipment_id: str) -> bool:
        """Sets equipment status to OPERATIONAL and bms_status to Operativo."""
        eq = self.get_equipment(equipment_id)
        if not eq:
            return False
        eq.status = EquipmentStatus.OPERATIONAL
        eq.bms_status = "Operativo"
        self.save_equipment(eq)
        return True

    def delete_equipment(self, equipment_id: str) -> bool:
        eq = self.get_equipment(equipment_id)
        if not eq:
            return False
            
        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(eq.id, "EQUIPMENT", eq.tag, eq.to_dict())

        eq_dir = os.path.join(self.storage.base_path, "equipment", equipment_id)
        try:
            if os.path.exists(eq_dir):
                shutil.rmtree(eq_dir)
        except Exception:
            return False
            
        self.storage.remove_from_index("equipment", equipment_id)
        return True

    def search_equipment(self, query: str) -> List[HVACEquipment]:
        query = query.lower()
        results = []
        for eq in self.get_all_equipment():
            if (query in eq.tag.lower() or 
                query in eq.manufacturer.lower() or 
                query in eq.model.lower() or 
                query in eq.serial_number.lower()):
                results.append(eq)
        return results

    def get_equipment_stats(self) -> Dict[str, Any]:
        stats = {
            "total": 0,
            "by_type": {},
            "by_status": {},
            "overdue": len(self.get_overdue_equipment())
        }
        
        for eq in self.get_all_equipment():
            stats["total"] += 1
            
            sys_type = eq.system_type.value if hasattr(eq.system_type, 'value') else eq.system_type
            stats["by_type"][sys_type] = stats["by_type"].get(sys_type, 0) + 1
            
            status = eq.status.value if hasattr(eq.status, 'value') else eq.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
        return stats

    def get_overdue_equipment(self) -> List[HVACEquipment]:
        overdue = []
        today = datetime.now().date()
        for eq in self.get_all_equipment():
            if eq.next_service_due:
                try:
                    # Depending on how the date is formatted, assume ISO format YYYY-MM-DD
                    if isinstance(eq.next_service_due, str):
                        due_date = datetime.strptime(eq.next_service_due, "%Y-%m-%d").date()
                    else:
                        due_date = eq.next_service_due
                        
                    if due_date < today:
                        overdue.append(eq)
                except (ValueError, TypeError):
                    pass
        return overdue

    def update_service_date(self, equipment_id: str, service_date: str) -> bool:
        eq = self.get_equipment(equipment_id)
        if not eq:
            return False
            
        eq.last_service_date = service_date
        # Need to recalculate next_service_due based on maintenance schedule ideally,
        # but for this method, we simply update the last service date.
        self.save_equipment(eq)
        return True

    def add_photo(self, equipment_id: str, photo_source: str, compress: bool=True) -> str:
        eq = self.get_equipment(equipment_id)
        if not eq:
            raise ValueError("Equipment not found")
            
        try:
            filename = os.path.basename(photo_source)
            if compress:
                # Mock compress or just copy
                pass
                
            dest_path = self.storage.save_attachment("equipment", equipment_id, photo_source)
            
            if not hasattr(eq, 'photos'):
                eq.photos = []
            eq.photos.append(dest_path)
            self.save_equipment(eq)
            return dest_path
        except Exception as e:
            raise Exception(f"Failed to add photo: {e}")

    # --- SPARE PARTS HISTORY / LOG FOR EQUIPMENT ---

    def get_parts_history(self, equipment_id: str) -> List[Dict[str, Any]]:
        """Retrieves the spare parts installation and usage history for a specific equipment."""
        data = self.storage.load_document("equipment", equipment_id, "parts_history.json")
        if data and isinstance(data, list):
            # Sort by date descending
            try:
                data.sort(key=lambda x: x.get('date', ''), reverse=True)
            except Exception:
                pass
            return data
        return []

    def add_part_history_entry(self, equipment_id: str, entry: Dict[str, Any]) -> bool:
        """Adds a spare part usage/installation record to the equipment's parts_history.json."""
        if not equipment_id:
            return False
            
        history = self.get_parts_history(equipment_id)
        
        # Check duplicate by movement_id or id
        entry_id = entry.get('id') or entry.get('movement_id')
        if entry_id:
            for existing in history:
                if (existing.get('id') == entry_id) or (existing.get('movement_id') == entry_id):
                    return True # Already recorded
                    
        history.insert(0, entry)
        self.storage.save_document("equipment", equipment_id, "parts_history.json", history)
        return True

    def sync_all_parts_history_from_inventory(self, inventory_service) -> int:
        """Retroactively syncs existing inventory movements assigned to equipment into each equipment's parts_history.json."""
        if not inventory_service:
            return 0
            
        synced_count = 0
        try:
            movements = inventory_service.get_movements()
            all_equipments = {eq.id: eq for eq in self.get_all_equipment()}
            tag_to_id = {eq.tag.lower(): eq.id for eq in all_equipments.values()}

            for mov in movements:
                mov_type = getattr(mov, 'movement_type', None) or getattr(mov, 'type', 'IN')
                if mov_type != "OUT":
                    continue
                    
                target_eq_id = getattr(mov, 'equipment_id', '') or ""
                target_eq_tag = getattr(mov, 'equipment_tag', '') or ""

                if not target_eq_id and target_eq_tag:
                    target_eq_id = tag_to_id.get(target_eq_tag.lower(), "")

                if not target_eq_id:
                    # Check reference or reason or notes
                    combined = f"{mov.reference} {mov.notes} {mov.reason}".lower()
                    for tag_lower, eq_id in tag_to_id.items():
                        if tag_lower in combined:
                            target_eq_id = eq_id
                            break

                if target_eq_id and target_eq_id in all_equipments:
                    eq_obj = all_equipments[target_eq_id]
                    
                    # Fetch part info if available
                    part_id = getattr(mov, 'part_id', '')
                    part_name = getattr(mov, 'part_name', '')
                    part_code = ""
                    unit_str = "unid"
                    
                    if part_id:
                        p_obj = inventory_service.get_spare_part(part_id)
                        if p_obj:
                            part_name = part_name or p_obj.name
                            part_code = p_obj.part_number
                            unit_str = getattr(p_obj, 'unit', 'unid')

                    entry = {
                        "id": mov.id,
                        "movement_id": mov.id,
                        "part_id": part_id,
                        "part_name": part_name or "Repuesto",
                        "part_number": part_code,
                        "quantity": mov.quantity,
                        "unit": unit_str,
                        "reason": getattr(mov, 'reason', '') or "Salida de inventario",
                        "reference": getattr(mov, 'reference', ''),
                        "destination": getattr(mov, 'destination', ''),
                        "performed_by": getattr(mov, 'performed_by', 'Usuario'),
                        "date": mov.date,
                        "notes": getattr(mov, 'notes', '')
                    }
                    
                    if self.add_part_history_entry(target_eq_id, entry):
                        synced_count += 1
        except Exception as e:
            print(f"Error syncing parts history from inventory: {e}")
            
        return synced_count

    # --- SERVICE & MAINTENANCE GUIDES HISTORY (service_history.json) ---

    def get_service_history(self, equipment_id: str) -> List[Dict[str, Any]]:
        """Retrieves the service and maintenance guides history for a specific equipment."""
        data = self.storage.load_document("equipment", equipment_id, "service_history.json")
        if data and isinstance(data, list):
            try:
                data.sort(key=lambda x: x.get('date', '') or x.get('scheduled_date', ''), reverse=True)
            except Exception:
                pass
            return data
        return []

    def add_service_history_entry(self, equipment_id: str, entry: Dict[str, Any]) -> bool:
        """Adds or updates a service guide record in the equipment's service_history.json."""
        if not equipment_id:
            return False
            
        history = self.get_service_history(equipment_id)
        
        entry_id = entry.get('id') or entry.get('work_order_id')
        if entry_id:
            for idx, existing in enumerate(history):
                if (existing.get('id') == entry_id) or (existing.get('work_order_id') == entry_id):
                    history[idx] = entry # Update existing
                    self.storage.save_document("equipment", equipment_id, "service_history.json", history)
                    return True
                    
        history.insert(0, entry)
        self.storage.save_document("equipment", equipment_id, "service_history.json", history)
        return True

    def sync_all_service_history_from_work_orders(self, work_order_service) -> int:
        """Retroactively syncs existing work orders and service guides into each equipment's service_history.json."""
        if not work_order_service:
            return 0
            
        synced_count = 0
        try:
            wos = work_order_service.get_all_work_orders()
            for wo in wos:
                if wo.equipment_id:
                    tasks_summary = []
                    for t in (wo.checklist or []):
                        if isinstance(t, dict):
                            desc = t.get('description', '')
                        else:
                            desc = getattr(t, 'description', '')
                        if desc:
                            tasks_summary.append(desc)

                    entry = {
                        "id": wo.id,
                        "work_order_id": wo.id,
                        "guide_kind": getattr(wo, 'guide_kind', '') or ("SERVICE" if "OTS" in wo.id else "MAINTENANCE"),
                        "service_type": getattr(wo, 'service_type', '') or ("Reparación" if "OTS" in wo.id else "Mantenimiento Preventivo"),
                        "title": wo.title,
                        "status": wo.status.value if hasattr(wo.status, 'value') else str(wo.status),
                        "priority": wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority),
                        "date": wo.scheduled_date or (wo.created_at[:10] if wo.created_at else ""),
                        "scheduled_date": wo.scheduled_date,
                        "completed_date": getattr(wo, 'completed_date', ''),
                        "technician": getattr(wo, 'assigned_technician', '') or getattr(wo, 'assigned_to', ''),
                        "diagnosis": getattr(wo, 'diagnosis', '') or wo.description,
                        "work_performed": getattr(wo, 'work_performed', '') or getattr(wo, 'observations', ''),
                        "tasks": tasks_summary,
                        "materials_used": getattr(wo, 'materials_used', []) or getattr(wo, 'parts_used', []),
                        "notes": wo.observations
                    }
                    if self.add_service_history_entry(wo.equipment_id, entry):
                        synced_count += 1
        except Exception as e:
            print(f"Error syncing service history from work orders: {e}")
            
        return synced_count

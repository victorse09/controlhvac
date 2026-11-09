import os
import shutil
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.core.models.work_order import WorkOrder
from src.core.models.enums import WorkOrderStatus, WorkOrderType, Priority
from src.data.json_storage import JsonStorageEngine


class WorkOrderService:
    """Service for managing work orders and service guides (OTS / OTM)."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None, equipment_service=None, incident_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service
        self.equipment_service = equipment_service
        self.incident_service = incident_service
        self._migrate_legacy_uuid_orders()

    def _migrate_legacy_uuid_orders(self):
        """Converts any legacy work orders with UUIDs into sequential OTS / OTM correlatives."""
        try:
            index = self.storage.get_index("work_orders")
            uuid_ids = [wo_id for wo_id in index if len(str(wo_id)) > 20 and '-' in str(wo_id)]
            for old_id in uuid_ids:
                wo = self.get_work_order(old_id)
                if wo:
                    guide_kind = getattr(wo, 'guide_kind', '') or ("MAINTENANCE" if wo.work_order_type == "PREVENTIVE" else "SERVICE")
                    if guide_kind == "MAINTENANCE":
                        new_id = self.get_next_maintenance_code()
                    else:
                        new_id = self.get_next_service_code()
                    
                    wo.id = new_id
                    # Delete old document and remove old key
                    self.delete_work_order(old_id)
                    # Re-save under new sequential code
                    self.save_work_order(wo)
        except Exception as e:
            print(f"Error migrating legacy work orders: {e}")

    def get_next_service_code(self) -> str:
        """Generates the next sequential code for Service Guides (e.g. OTS00001, OTS00002)."""
        max_num = 0
        try:
            index = self.storage.get_index("work_orders")
            for wo_id in index:
                match = re.match(r"^OTS(\d+)$", str(wo_id), re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        except Exception:
            pass
        return f"OTS{max_num + 1:05d}"

    def get_next_maintenance_code(self) -> str:
        """Generates the next sequential code for Maintenance Guides (e.g. OTM00001, OTM00002)."""
        max_num = 0
        try:
            index = self.storage.get_index("work_orders")
            for wo_id in index:
                match = re.match(r"^(?:OTM|TOM)(\d+)$", str(wo_id), re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        except Exception:
            pass
        return f"OTM{max_num + 1:05d}"

    def save_work_order(self, wo: WorkOrder) -> WorkOrder:
        # Generate sequential ID if not set or if it has a UUID
        is_invalid_id = (not wo.id) or (len(wo.id) > 20 and '-' in wo.id) or (not wo.id.startswith("OTS") and not wo.id.startswith("OTM") and not wo.id.startswith("TOM"))
        if is_invalid_id:
            old_id = wo.id
            guide_kind = getattr(wo, 'guide_kind', '') or ("MAINTENANCE" if wo.work_order_type == "PREVENTIVE" else "SERVICE")
            if guide_kind == "MAINTENANCE":
                wo.id = self.get_next_maintenance_code()
            else:
                wo.id = self.get_next_service_code()
                
            if old_id and old_id != wo.id:
                try:
                    self.delete_work_order(old_id)
                except Exception:
                    pass

        # saves to work_orders/{year}/{id}.json
        # Assuming we extract year from scheduled_date or created_at
        try:
            if hasattr(wo, 'scheduled_date') and wo.scheduled_date:
                dt = datetime.strptime(wo.scheduled_date[:10], "%Y-%m-%d") if isinstance(wo.scheduled_date, str) else wo.scheduled_date
                year = str(dt.year)
            else:
                dt = datetime.fromisoformat(wo.created_at) if isinstance(wo.created_at, str) else wo.created_at
                year = str(dt.year)
        except Exception:
            year = str(datetime.now().year)

        path = f"work_orders/{year}"
        self.storage.save_document(path, wo.id, f"{wo.id}.json", wo.to_dict())
        self.storage.update_index("work_orders", wo.id, {
            "type": wo.type.value if hasattr(wo.type, 'value') else wo.type,
            "guide_kind": getattr(wo, 'guide_kind', 'SERVICE'),
            "service_type": getattr(wo, 'service_type', ''),
            "status": wo.status.value if hasattr(wo.status, 'value') else wo.status,
            "equipment_id": wo.equipment_id,
            "equipment_tag": wo.equipment_tag,
            "title": wo.title,
            "scheduled_date": wo.scheduled_date,
            "year": year
        })

        # Automatically sync to equipment service_history.json if equipment_id is present
        if wo.equipment_id and self.equipment_service:
            try:
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
                self.equipment_service.add_service_history_entry(wo.equipment_id, entry)
            except Exception as e:
                print(f"Error recording work order in equipment service history: {e}")

        # Automatically resolve incident and restore equipment status to OPERATIONAL if completed
        is_completed = (wo.status == WorkOrderStatus.COMPLETED or wo.status == WorkOrderStatus.COMPLETED.value or str(wo.status).upper() in ["COMPLETED", "COMPLETADA"])
        
        # 1. Update linked incident
        inc_id = getattr(wo, 'incident_id', '')
        if inc_id and self.incident_service:
            try:
                if is_completed:
                    self.incident_service.resolve_incident_from_work_order(inc_id, wo)
                else:
                    inc = self.incident_service.get_incident(inc_id)
                    if inc and str(getattr(inc, 'status', '')).upper() in ["REPORTADA", "PENDING"]:
                        inc.status = IncidentStatus.EN_REPARACION.value
                        inc.work_order_id = wo.id
                        self.incident_service.save_incident(inc)
            except Exception as e:
                print(f"Error updating incident status from work order: {e}")

        # 2. Restore equipment operational status if completed and equipment was associated
        if is_completed and wo.equipment_id and self.equipment_service:
            try:
                self.equipment_service.set_equipment_operational(wo.equipment_id)
            except Exception as e:
                print(f"Error restoring equipment operational status: {e}")

        return wo

    def _get_year_from_index(self, wo_id: str) -> Optional[str]:
        index = self.storage.get_index("work_orders")
        if wo_id in index:
            return index[wo_id].get("year")
        return None

    def get_work_order(self, wo_id: str) -> Optional[WorkOrder]:
        year = self._get_year_from_index(wo_id)
        if not year:
            # Need to search through years if not in index (fallback)
            wo_dir = os.path.join(self.storage.base_path, "work_orders")
            if os.path.exists(wo_dir):
                for y in os.listdir(wo_dir):
                    if os.path.isdir(os.path.join(wo_dir, y)):
                        data = self.storage.load_document(f"work_orders/{y}", wo_id, f"{wo_id}.json")
                        if data:
                            return WorkOrder.from_dict(data)
            return None
            
        data = self.storage.load_document(f"work_orders/{year}", wo_id, f"{wo_id}.json")
        return WorkOrder.from_dict(data) if data else None

    def get_all_work_orders(self) -> List[WorkOrder]:
        wos = []
        index = self.storage.get_index("work_orders")
        for wo_id in index:
            wo = self.get_work_order(wo_id)
            if wo:
                wos.append(wo)
        return wos

    def get_work_orders_by_status(self, status: str) -> List[WorkOrder]:
        status_val = status.value if hasattr(status, 'value') else status
        return [wo for wo in self.get_all_work_orders() 
                if (wo.status.value if hasattr(wo.status, 'value') else wo.status) == status_val]

    def get_work_orders_by_type(self, wo_type: str) -> List[WorkOrder]:
        type_val = wo_type.value if hasattr(wo_type, 'value') else wo_type
        return [wo for wo in self.get_all_work_orders() 
                if (wo.type.value if hasattr(wo.type, 'value') else wo.type) == type_val]

    def get_work_orders_for_equipment(self, equipment_id: str) -> List[WorkOrder]:
        return [wo for wo in self.get_all_work_orders() if wo.equipment_id == equipment_id]

    def get_work_orders_for_date(self, date_str: str) -> List[WorkOrder]:
        return [wo for wo in self.get_all_work_orders() if wo.scheduled_date == date_str]

    def get_work_orders_for_date_range(self, start_date: str, end_date: str) -> List[WorkOrder]:
        wos = []
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return wos
            
        for wo in self.get_all_work_orders():
            if wo.scheduled_date:
                try:
                    wo_date = datetime.strptime(wo.scheduled_date, "%Y-%m-%d").date()
                    if start <= wo_date <= end:
                        wos.append(wo)
                except ValueError:
                    pass
        return wos

    def get_overdue_work_orders(self) -> List[WorkOrder]:
        overdue = []
        today = datetime.now().date()
        for wo in self.get_all_work_orders():
            status_val = wo.status.value if hasattr(wo.status, 'value') else wo.status
            # If not completed or cancelled
            if status_val not in (WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value):
                if wo.scheduled_date:
                    try:
                        wo_date = datetime.strptime(wo.scheduled_date, "%Y-%m-%d").date()
                        if wo_date < today:
                            overdue.append(wo)
                    except ValueError:
                        pass
        return overdue

    def get_upcoming_work_orders(self, days: int = 7) -> List[WorkOrder]:
        upcoming = []
        today = datetime.now().date()
        future = today + timedelta(days=days)
        
        for wo in self.get_all_work_orders():
            status_val = wo.status.value if hasattr(wo.status, 'value') else wo.status
            if status_val not in (WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value):
                if wo.scheduled_date:
                    try:
                        wo_date = datetime.strptime(wo.scheduled_date, "%Y-%m-%d").date()
                        if today <= wo_date <= future:
                            upcoming.append(wo)
                    except ValueError:
                        pass
        return upcoming

    def start_work_order(self, wo_id: str) -> bool:
        wo = self.get_work_order(wo_id)
        if not wo:
            return False
            
        wo.status = WorkOrderStatus.IN_PROGRESS
        wo.start_date = datetime.now().isoformat()
        self.save_work_order(wo)
        return True

    def complete_work_order(self, wo_id: str, observations: str = '') -> bool:
        wo = self.get_work_order(wo_id)
        if not wo:
            return False
            
        wo.status = WorkOrderStatus.COMPLETED
        wo.completed_date = datetime.now().isoformat()
        if observations:
            wo.observations = observations
        self.save_work_order(wo)
        return True

    def cancel_work_order(self, wo_id: str) -> bool:
        wo = self.get_work_order(wo_id)
        if not wo:
            return False
            
        wo.status = WorkOrderStatus.CANCELLED
        self.save_work_order(wo)
        return True

    def delete_work_order(self, wo_id: str) -> bool:
        wo = self.get_work_order(wo_id)
        if not wo:
            return False
            
        if self.recycle_bin_service:
            display_title = f"OT #{wo.id[:8]} - {wo.title}"
            self.recycle_bin_service.recycle_item(wo.id, "WORK_ORDER", display_title, wo.to_dict())

        year = self._get_year_from_index(wo_id)
        if year:
            wo_dir = os.path.join(self.storage.base_path, f"work_orders/{year}", wo_id)
            try:
                if os.path.exists(wo_dir):
                    shutil.rmtree(wo_dir)
            except Exception:
                return False
                
        self.storage.remove_from_index("work_orders", wo_id)
        return True

    def add_photo(self, wo_id: str, photo_source: str, compress: bool=True) -> str:
        wo = self.get_work_order(wo_id)
        if not wo:
            raise ValueError("Work order not found")
            
        year = self._get_year_from_index(wo_id) or str(datetime.now().year)
        dest_path = self.storage.save_attachment(f"work_orders/{year}", wo_id, photo_source)
        
        if not hasattr(wo, 'photos'):
            wo.photos = []
        wo.photos.append(dest_path)
        self.save_work_order(wo)
        return dest_path

    def add_attachment(self, wo_id: str, file_source: str) -> str:
        wo = self.get_work_order(wo_id)
        if not wo:
            raise ValueError("Work order not found")
            
        year = self._get_year_from_index(wo_id) or str(datetime.now().year)
        dest_path = self.storage.save_attachment(f"work_orders/{year}", wo_id, file_source)
        
        if not hasattr(wo, 'attachments'):
            wo.attachments = []
        wo.attachments.append(dest_path)
        self.save_work_order(wo)
        return dest_path

    def get_work_order_stats(self) -> Dict[str, Any]:
        stats = {
            "total": 0,
            "by_status": {},
            "by_type": {},
            "by_priority": {}
        }
        
        for wo in self.get_all_work_orders():
            stats["total"] += 1
            
            status = wo.status.value if hasattr(wo.status, 'value') else wo.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            wtype = wo.type.value if hasattr(wo.type, 'value') else wo.type
            stats["by_type"][wtype] = stats["by_type"].get(wtype, 0) + 1
            
            priority = wo.priority.value if hasattr(wo.priority, 'value') else wo.priority
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
        return stats

    def check_overdue(self) -> int:
        overdue_wos = self.get_overdue_work_orders()
        count = 0
        for wo in overdue_wos:
            # We might want to set a specific status or just return count
            # Currently just returning count per requirements, but could update them
            count += 1
        return count

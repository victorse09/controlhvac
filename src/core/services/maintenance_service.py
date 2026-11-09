import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.core.models.maintenance import MaintenanceSchedule
from src.core.models.work_order import WorkOrder
from src.core.models.enums import WorkOrderType, WorkOrderStatus, Priority
from src.core.services.work_order_service import WorkOrderService
from src.core.services.equipment_service import EquipmentService
from src.data.json_storage import JsonStorageEngine


class MaintenanceService:
    """Service for managing maintenance schedules."""

    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage

    def save_schedule(self, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        self.storage.save_document("maintenance", schedule.id, "schedule.json", schedule.to_dict())
        self.storage.update_index("maintenance", schedule.id, {
            "equipment_id": schedule.equipment_id,
            "frequency_days": schedule.frequency_days,
            "is_active": schedule.is_active
        })
        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[MaintenanceSchedule]:
        data = self.storage.load_document("maintenance", schedule_id, "schedule.json")
        return MaintenanceSchedule.from_dict(data) if data else None

    def get_all_schedules(self) -> List[MaintenanceSchedule]:
        schedules = []
        index = self.storage.get_index("maintenance")
        for sched_id in index:
            sched = self.get_schedule(sched_id)
            if sched:
                schedules.append(sched)
        return schedules

    def get_active_schedules(self) -> List[MaintenanceSchedule]:
        return [s for s in self.get_all_schedules() if s.is_active]

    def get_schedules_for_equipment(self, equipment_id: str) -> List[MaintenanceSchedule]:
        return [s for s in self.get_all_schedules() if s.equipment_id == equipment_id]

    def delete_schedule(self, schedule_id: str) -> bool:
        sched = self.get_schedule(schedule_id)
        if not sched:
            return False
            
        sched_dir = os.path.join(self.storage.base_path, "maintenance", schedule_id)
        try:
            if os.path.exists(sched_dir):
                shutil.rmtree(sched_dir)
        except Exception:
            return False
            
        self.storage.remove_from_index("maintenance", schedule_id)
        return True

    def deactivate_schedule(self, schedule_id: str) -> bool:
        sched = self.get_schedule(schedule_id)
        if not sched:
            return False
            
        sched.is_active = False
        self.save_schedule(sched)
        return True

    def generate_work_orders(self, work_order_service: WorkOrderService, equipment_service: EquipmentService) -> List[WorkOrder]:
        generated = []
        today = datetime.now().date()
        
        for schedule in self.get_active_schedules():
            if not schedule.next_date:
                continue
                
            try:
                next_date = datetime.strptime(schedule.next_date, "%Y-%m-%d").date()
                
                # If due within the next 7 days, generate a WO
                if today <= next_date <= today + timedelta(days=7) or next_date < today:
                    
                    # Avoid duplicates by checking existing work orders
                    existing_wos = work_order_service.get_work_orders_for_equipment(schedule.equipment_id)
                    already_scheduled = False
                    for wo in existing_wos:
                        status_val = wo.status.value if hasattr(wo.status, 'value') else wo.status
                        type_val = wo.type.value if hasattr(wo.type, 'value') else wo.type
                        
                        if (type_val == WorkOrderType.PREVENTIVE.value and 
                            status_val not in (WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value) and
                            wo.scheduled_date == schedule.next_date):
                            already_scheduled = True
                            break
                            
                    if not already_scheduled:
                        eq = equipment_service.get_equipment(schedule.equipment_id)
                        client_id = eq.client_id if eq else ""
                        site_id = eq.site_id if eq else ""
                        
                        new_wo = WorkOrder(
                            id=str(uuid.uuid4()),
                            title=f"Mantenimiento Preventivo: {eq.tag if eq else schedule.equipment_id}",
                            description=schedule.description or "Mantenimiento preventivo programado",
                            equipment_id=schedule.equipment_id,
                            client_id=client_id,
                            site_id=site_id,
                            type=WorkOrderType.PREVENTIVE,
                            status=WorkOrderStatus.PENDING,
                            priority=Priority.MEDIUM,
                            created_at=datetime.now().isoformat(),
                            created_by="System",
                            scheduled_date=schedule.next_date,
                            checklist=[item for item in schedule.checklist_template] if schedule.checklist_template else []
                        )
                        
                        work_order_service.save_work_order(new_wo)
                        generated.append(new_wo)
                        
                        # Update schedule's next date
                        next_dt = next_date + timedelta(days=schedule.frequency_days)
                        schedule.next_date = next_dt.strftime("%Y-%m-%d")
                        self.save_schedule(schedule)
            except ValueError:
                pass
                
        return generated

    def get_events_for_month(self, year: int, month: int) -> Dict[str, List[Dict[str, Any]]]:
        events = {}
        for schedule in self.get_active_schedules():
            if schedule.next_date:
                try:
                    dt = datetime.strptime(schedule.next_date, "%Y-%m-%d")
                    if dt.year == year and dt.month == month:
                        date_str = schedule.next_date
                        if date_str not in events:
                            events[date_str] = []
                        events[date_str].append({
                            "schedule_id": schedule.id,
                            "equipment_id": schedule.equipment_id,
                            "description": schedule.description
                        })
                except ValueError:
                    pass
        return events

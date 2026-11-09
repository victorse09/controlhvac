import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from src.core.models.inventory import (
    Tool, SparePart, InventoryMovement,
    PanolSupply, EppItem, PanolMovement,
    GasCylinder, GasUsageRecord
)
from src.core.models.enums import ToolStatus
from src.data.json_storage import JsonStorageEngine


class InventoryService:
    """Service for managing inventory (Tools and Spare Parts)."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None, equipment_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service
        self.equipment_service = equipment_service

    # --- TOOLS ---

    def save_tool(self, tool: Tool) -> Tool:
        self.storage.save_document("inventory/tools", tool.id, "tool.json", tool.to_dict())
        self.storage.update_index("inventory/tools", tool.id, {
            "name": tool.name,
            "status": tool.status.value if hasattr(tool.status, 'value') else tool.status,
            "assigned_to": tool.assigned_to
        })
        return tool

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        data = self.storage.load_document("inventory/tools", tool_id, "tool.json")
        return Tool.from_dict(data) if data else None

    def get_all_tools(self) -> List[Tool]:
        tools = []
        index = self.storage.get_index("inventory/tools")
        for tool_id in index:
            tool = self.get_tool(tool_id)
            if tool:
                tools.append(tool)
        return tools

    def delete_tool(self, tool_id: str) -> bool:
        tool = self.get_tool(tool_id)
        if not tool:
            return False
            
        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(tool.id, "TOOL", tool.name, tool.to_dict())

        tool_dir = os.path.join(self.storage.base_path, "inventory", "tools", tool_id)
        try:
            if os.path.exists(tool_dir):
                shutil.rmtree(tool_dir)
        except Exception:
            return False
            
        self.storage.remove_from_index("inventory/tools", tool_id)
        return True

    def search_tools(self, query: str) -> List[Tool]:
        query = query.lower()
        results = []
        for tool in self.get_all_tools():
            if (query in tool.name.lower() or 
                query in tool.brand.lower() or 
                query in tool.model.lower() or 
                query in tool.serial_number.lower()):
                results.append(tool)
        return results

    def assign_tool(self, tool_id: str, technician: str, recipient_type: str = "TECHNICIAN", performed_by: str = "Pañolero", notes: str = "") -> bool:
        tool = self.get_tool(tool_id)
        if not tool:
            return False
            
        tool.status = ToolStatus.IN_USE.value if hasattr(ToolStatus.IN_USE, 'value') else "IN_USE"
        tool.assigned_to = technician
        self.save_tool(tool)

        self.record_panol_movement(PanolMovement(
            item_id=tool.id,
            item_name=tool.name,
            item_code=tool.serial_number or tool.model or "",
            item_category="TOOL",
            movement_type="ASSIGN",
            quantity=1,
            unit="unid",
            recipient_type=recipient_type,
            recipient_name=technician,
            reason="Asignación de Herramienta",
            performed_by=performed_by,
            notes=notes
        ))
        return True

    def return_tool(self, tool_id: str, performed_by: str = "Pañolero", notes: str = "", new_status: str = "AVAILABLE") -> bool:
        tool = self.get_tool(tool_id)
        if not tool:
            return False

        prev_assigned = tool.assigned_to or "Sin especificar"
        tool.status = new_status
        tool.assigned_to = ""
        self.save_tool(tool)

        self.record_panol_movement(PanolMovement(
            item_id=tool.id,
            item_name=tool.name,
            item_code=tool.serial_number or tool.model or "",
            item_category="TOOL",
            movement_type="RETURN",
            quantity=1,
            unit="unid",
            recipient_name=prev_assigned,
            reason="Devolución de Herramienta a Pañol",
            performed_by=performed_by,
            notes=notes
        ))
        return True

    def get_tools_needing_calibration(self) -> List[Tool]:
        tools = []
        today = datetime.now().date()
        for tool in self.get_all_tools():
            if tool.requires_calibration and tool.next_calibration_date:
                try:
                    cal_date = datetime.strptime(tool.next_calibration_date, "%Y-%m-%d").date()
                    if cal_date < today:
                        tools.append(tool)
                except ValueError:
                    pass
        return tools

    # --- SPARE PARTS ---

    def save_spare_part(self, part: SparePart) -> SparePart:
        self.storage.save_document("inventory/parts", part.id, "part.json", part.to_dict())
        self.storage.update_index("inventory/parts", part.id, {
            "name": part.name,
            "part_number": part.part_number,
            "quantity": part.quantity
        })
        return part

    def get_spare_part(self, part_id: str) -> Optional[SparePart]:
        data = self.storage.load_document("inventory/parts", part_id, "part.json")
        return SparePart.from_dict(data) if data else None

    def get_all_spare_parts(self) -> List[SparePart]:
        parts = []
        index = self.storage.get_index("inventory/parts")
        for part_id in index:
            part = self.get_spare_part(part_id)
            if part:
                parts.append(part)
        return parts

    def delete_spare_part(self, part_id: str) -> bool:
        part = self.get_spare_part(part_id)
        if not part:
            return False
            
        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(part.id, "SPARE_PART", part.name, part.to_dict())

        part_dir = os.path.join(self.storage.base_path, "inventory", "parts", part_id)
        try:
            if os.path.exists(part_dir):
                shutil.rmtree(part_dir)
        except Exception:
            return False
            
        self.storage.remove_from_index("inventory/parts", part_id)
        return True

    def search_spare_parts(self, query: str) -> List[SparePart]:
        query = query.lower()
        results = []
        for part in self.get_all_spare_parts():
            if (query in part.name.lower() or 
                query in part.part_number.lower() or 
                query in part.manufacturer.lower()):
                results.append(part)
        return results

    def get_low_stock_parts(self) -> List[SparePart]:
        return [p for p in self.get_all_spare_parts() if p.quantity <= p.minimum_quantity]

    def register_movement(
        self,
        part_id: str,
        movement_type: str,
        quantity: int,
        reason: str = "",
        reference: str = "",
        equipment_id: str = "",
        equipment_tag: str = "",
        destination: str = "",
        performed_by: str = "Usuario",
        notes: str = ""
    ) -> bool:
        if quantity <= 0:
            return False
            
        part = self.get_spare_part(part_id)
        if not part:
            return False
            
        if movement_type == "OUT":
            if part.quantity < quantity:
                return False
            part.quantity -= quantity
        else:
            part.quantity += quantity
            
        self.save_spare_part(part)
        
        movement = InventoryMovement(
            id=str(uuid.uuid4()),
            part_id=part_id,
            part_name=part.name,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            reference=reference,
            equipment_id=equipment_id,
            equipment_tag=equipment_tag,
            destination=destination,
            performed_by=performed_by,
            date=datetime.now().isoformat(),
            notes=notes
        )
        self.record_movement(movement)

        # If this is an OUT movement assigned to an equipment, record in equipment's parts_history.json
        if movement_type == "OUT" and equipment_id and self.equipment_service:
            try:
                entry = {
                    "id": movement.id,
                    "movement_id": movement.id,
                    "part_id": part_id,
                    "part_name": part.name,
                    "part_number": part.part_number,
                    "quantity": quantity,
                    "unit": getattr(part, 'unit', 'unid'),
                    "reason": reason or "Asignado a Equipo",
                    "reference": reference,
                    "performed_by": performed_by,
                    "date": movement.date,
                    "notes": notes
                }
                self.equipment_service.add_part_history_entry(equipment_id, entry)
            except Exception as e:
                print(f"Error recording part movement in equipment history: {e}")

        return True

    def add_stock(self, part_id: str, quantity: int, reference: str = "", performed_by: str = "Usuario", reason: str = "Ingreso de stock", notes: str = "") -> bool:
        return self.register_movement(
            part_id=part_id,
            movement_type="IN",
            quantity=quantity,
            reason=reason,
            reference=reference,
            performed_by=performed_by,
            notes=notes or f"Entrada de stock: {quantity}"
        )

    def remove_stock(self, part_id: str, quantity: int, work_order_id: str = "", performed_by: str = "Usuario", reason: str = "Salida de stock", equipment_id: str = "", equipment_tag: str = "", destination: str = "", notes: str = "") -> bool:
        return self.register_movement(
            part_id=part_id,
            movement_type="OUT",
            quantity=quantity,
            reason=reason,
            reference=work_order_id,
            equipment_id=equipment_id,
            equipment_tag=equipment_tag,
            destination=destination,
            performed_by=performed_by,
            notes=notes or f"Salida de stock: {quantity}"
        )

    def record_movement(self, movement: InventoryMovement) -> InventoryMovement:
        self.storage.save_document("inventory/movements", movement.id, "movement.json", movement.to_dict())
        self.storage.update_index("inventory/movements", movement.id, {
            "part_id": movement.part_id,
            "type": movement.type,
            "date": movement.date
        })
        return movement

    def get_movements(self, part_id: str = None) -> List[InventoryMovement]:
        movements = []
        index = self.storage.get_index("inventory/movements")
        for m_id in index:
            data = self.storage.load_document("inventory/movements", m_id, "movement.json")
            if data:
                mov = InventoryMovement.from_dict(data)
                if part_id is None or mov.part_id == part_id:
                    movements.append(mov)
                    
        # Sort by date descending
        movements.sort(key=lambda x: x.date, reverse=True)
        return movements

    # --- PAÑOL: INSUMOS (SUPPLIES) ---

    def save_supply(self, supply: PanolSupply) -> PanolSupply:
        supply.updated_at = datetime.now().isoformat()
        self.storage.save_document("inventory/supplies", supply.id, "supply.json", supply.to_dict())
        self.storage.update_index("inventory/supplies", supply.id, {
            "name": supply.name,
            "code": supply.code,
            "category": supply.category,
            "quantity": supply.quantity
        })
        return supply

    def get_supply(self, supply_id: str) -> Optional[PanolSupply]:
        data = self.storage.load_document("inventory/supplies", supply_id, "supply.json")
        return PanolSupply.from_dict(data) if data else None

    def get_all_supplies(self) -> List[PanolSupply]:
        supplies = []
        index = self.storage.get_index("inventory/supplies")
        for s_id in index:
            s = self.get_supply(s_id)
            if s:
                supplies.append(s)
        supplies.sort(key=lambda x: (x.name or "").lower())
        return supplies

    def delete_supply(self, supply_id: str) -> bool:
        s = self.get_supply(supply_id)
        if not s:
            return False

        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(s.id, "PANOL_SUPPLY", s.name, s.to_dict())

        s_dir = os.path.join(self.storage.base_path, "inventory", "supplies", supply_id)
        try:
            if os.path.exists(s_dir):
                shutil.rmtree(s_dir)
        except Exception:
            return False

        self.storage.remove_from_index("inventory/supplies", supply_id)
        return True

    def register_supply_movement(
        self,
        supply_id: str,
        movement_type: str,  # "IN" or "OUT"
        quantity: int,
        recipient_type: str = "",  # "TECHNICIAN", "EXTERNAL", "SITE"
        recipient_name: str = "",
        reason: str = "",
        reference: str = "",
        performed_by: str = "Pañolero",
        notes: str = ""
    ) -> bool:
        if quantity <= 0:
            return False

        supply = self.get_supply(supply_id)
        if not supply:
            return False

        if movement_type == "OUT":
            if supply.quantity < quantity:
                return False
            supply.quantity -= quantity
        else:
            supply.quantity += quantity

        self.save_supply(supply)

        mov = PanolMovement(
            item_id=supply.id,
            item_name=supply.name,
            item_code=supply.code,
            item_category="SUPPLY",
            movement_type=movement_type,
            quantity=quantity,
            unit=supply.unit,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            reason=reason or ("Ingreso a Pañol" if movement_type == "IN" else "Entrega de Insumo"),
            reference=reference,
            performed_by=performed_by,
            notes=notes
        )
        self.record_panol_movement(mov)
        return True

    # --- PAÑOL: EPP (ELEMENTOS DE PROTECCIÓN PERSONAL) ---

    def save_epp(self, epp: EppItem) -> EppItem:
        epp.updated_at = datetime.now().isoformat()
        self.storage.save_document("inventory/epp", epp.id, "epp.json", epp.to_dict())
        self.storage.update_index("inventory/epp", epp.id, {
            "name": epp.name,
            "code": epp.code,
            "epp_type": epp.epp_type,
            "category": epp.category,
            "quantity": epp.quantity,
            "status": epp.status,
            "assigned_to": epp.assigned_to
        })
        return epp

    def get_epp(self, epp_id: str) -> Optional[EppItem]:
        data = self.storage.load_document("inventory/epp", epp_id, "epp.json")
        return EppItem.from_dict(data) if data else None

    def get_all_epp(self, epp_type: Optional[str] = None) -> List[EppItem]:
        items = []
        index = self.storage.get_index("inventory/epp")
        for e_id in index:
            item = self.get_epp(e_id)
            if item:
                if epp_type is None or item.epp_type == epp_type:
                    items.append(item)
        items.sort(key=lambda x: (x.name or "").lower())
        return items

    def delete_epp(self, epp_id: str) -> bool:
        item = self.get_epp(epp_id)
        if not item:
            return False

        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(item.id, "EPP_ITEM", item.name, item.to_dict())

        e_dir = os.path.join(self.storage.base_path, "inventory", "epp", epp_id)
        try:
            if os.path.exists(e_dir):
                shutil.rmtree(e_dir)
        except Exception:
            return False

        self.storage.remove_from_index("inventory/epp", epp_id)
        return True

    def register_epp_stock_movement(
        self,
        epp_id: str,
        movement_type: str,  # "IN" or "OUT"
        quantity: int,
        recipient_type: str = "",  # "TECHNICIAN", "EXTERNAL", "SITE"
        recipient_name: str = "",
        reason: str = "",
        reference: str = "",
        performed_by: str = "Pañolero",
        notes: str = ""
    ) -> bool:
        """Registra el ingreso a pañol o la entrega de EPP de consumo/entrega directa."""
        if quantity <= 0:
            return False

        epp = self.get_epp(epp_id)
        if not epp:
            return False

        if movement_type == "OUT":
            if epp.quantity < quantity:
                return False
            epp.quantity -= quantity
        else:
            epp.quantity += quantity

        self.save_epp(epp)

        mov = PanolMovement(
            item_id=epp.id,
            item_name=f"{epp.name} ({epp.size_or_model})" if epp.size_or_model else epp.name,
            item_code=epp.code,
            item_category="EPP_DELIVERY",
            movement_type=movement_type,
            quantity=quantity,
            unit=epp.unit,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            reason=reason or ("Ingreso EPP a Pañol" if movement_type == "IN" else "Entrega de EPP"),
            reference=reference,
            performed_by=performed_by,
            notes=notes
        )
        self.record_panol_movement(mov)
        return True

    def assign_epp(
        self,
        epp_id: str,
        recipient_name: str,
        recipient_type: str = "TECHNICIAN",
        reason: str = "Asignación de EPP de Cargo",
        reference: str = "",
        performed_by: str = "Pañolero",
        notes: str = ""
    ) -> bool:
        """Asigna un EPP de cargo (Arnés, línea de vida, carro y estrobo, polainas/coletos, etc.) a un destinatario."""
        epp = self.get_epp(epp_id)
        if not epp:
            return False

        epp.status = "ASSIGNED"
        epp.assigned_to = recipient_name
        epp.assigned_type = recipient_type
        epp.assigned_date = datetime.now().strftime("%Y-%m-%d")
        self.save_epp(epp)

        mov = PanolMovement(
            item_id=epp.id,
            item_name=epp.name,
            item_code=epp.serial_number or epp.code or "",
            item_category="EPP_ASSIGNMENT",
            movement_type="ASSIGN",
            quantity=1,
            unit=epp.unit or "unid",
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            reason=reason,
            reference=reference,
            performed_by=performed_by,
            notes=notes
        )
        self.record_panol_movement(mov)
        return True

    def return_epp(
        self,
        epp_id: str,
        new_status: str = "AVAILABLE",
        performed_by: str = "Pañolero",
        notes: str = ""
    ) -> bool:
        """Registra la devolución a pañol de un EPP por asignación."""
        epp = self.get_epp(epp_id)
        if not epp:
            return False

        prev_recipient = epp.assigned_to or "Sin especificar"
        prev_type = epp.assigned_type or ""
        epp.status = new_status
        epp.assigned_to = ""
        epp.assigned_type = ""
        epp.assigned_date = ""
        self.save_epp(epp)

        mov = PanolMovement(
            item_id=epp.id,
            item_name=epp.name,
            item_code=epp.serial_number or epp.code or "",
            item_category="EPP_ASSIGNMENT",
            movement_type="RETURN",
            quantity=1,
            unit=epp.unit or "unid",
            recipient_type=prev_type,
            recipient_name=prev_recipient,
            reason="Devolución de EPP a Pañol",
            performed_by=performed_by,
            notes=notes
        )
        self.record_panol_movement(mov)
        return True

    # --- PAÑOL: MOVIMIENTOS UNIFICADOS ---

    def record_panol_movement(self, movement: PanolMovement) -> PanolMovement:
        self.storage.save_document("inventory/panol_movements", movement.id, "movement.json", movement.to_dict())
        self.storage.update_index("inventory/panol_movements", movement.id, {
            "item_id": movement.item_id,
            "item_category": movement.item_category,
            "movement_type": movement.movement_type,
            "recipient_name": movement.recipient_name,
            "date": movement.date
        })
        return movement

    def get_panol_movements(
        self,
        item_id: Optional[str] = None,
        item_category: Optional[str] = None
    ) -> List[PanolMovement]:
        movements = []
        index = self.storage.get_index("inventory/panol_movements")
        for m_id in index:
            data = self.storage.load_document("inventory/panol_movements", m_id, "movement.json")
            if data:
                mov = PanolMovement.from_dict(data)
                if item_id and mov.item_id != item_id:
                    continue
                if item_category and mov.item_category != item_category:
                    continue
                movements.append(mov)

        movements.sort(key=lambda x: x.date, reverse=True)
        return movements

    # --- PAÑOL: CONTROL DE GASES (SOLDADURA, REFRIGERANTES, RECUPERADO, LIMPIEZA R-141b, NITRÓGENO) ---

    def save_gas_cylinder(self, cylinder: GasCylinder) -> GasCylinder:
        cylinder.updated_at = datetime.now().isoformat()
        if cylinder.gas_category != "RECOVERED" and cylinder.current_amount <= 0 and cylinder.status not in ("EMPTY", "RETURNED"):
            cylinder.status = "EMPTY"
        self.storage.save_document("inventory/gases", cylinder.id, "cylinder.json", cylinder.to_dict())
        self.storage.update_index("inventory/gases", cylinder.id, {
            "code": cylinder.code,
            "gas_category": cylinder.gas_category,
            "gas_type": cylinder.gas_type,
            "current_amount": cylinder.current_amount,
            "unit": cylinder.unit,
            "status": cylinder.status,
            "assigned_to": cylinder.assigned_to
        })
        return cylinder

    def get_gas_cylinder(self, cylinder_id: str) -> Optional[GasCylinder]:
        data = self.storage.load_document("inventory/gases", cylinder_id, "cylinder.json")
        return GasCylinder.from_dict(data) if data else None

    def get_all_gas_cylinders(self, gas_category: Optional[str] = None) -> List[GasCylinder]:
        cylinders = []
        index = self.storage.get_index("inventory/gases")
        for c_id in index:
            c = self.get_gas_cylinder(c_id)
            if c:
                if gas_category is None or c.gas_category == gas_category:
                    cylinders.append(c)
        cylinders.sort(key=lambda x: ((x.gas_type or "").lower(), (x.code or "").lower()))
        return cylinders

    def delete_gas_cylinder(self, cylinder_id: str) -> bool:
        c = self.get_gas_cylinder(cylinder_id)
        if not c:
            return False

        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(
                c.id, "GAS_CYLINDER", f"{c.gas_type} ({c.code})", c.to_dict()
            )

        c_dir = os.path.join(self.storage.base_path, "inventory", "gases", cylinder_id)
        try:
            if os.path.exists(c_dir):
                shutil.rmtree(c_dir)
        except Exception:
            return False

        self.storage.remove_from_index("inventory/gases", cylinder_id)
        return True

    def register_gas_movement(
        self,
        cylinder_id: str,
        movement_type: str,  # "OUT" (Uso/Carga en equipo), "IN" (Recarga/Ingreso/Recuperación hacia cilindro)
        amount: float,
        equipment_id: str = "",
        equipment_tag: str = "",
        recipient_type: str = "TECHNICIAN",
        recipient_name: str = "",
        work_order_ref: str = "",
        reason: str = "",
        notes: str = ""
    ) -> bool:
        if amount <= 0:
            return False

        cyl = self.get_gas_cylinder(cylinder_id)
        if not cyl:
            return False

        if movement_type == "OUT":
            if cyl.current_amount < amount:
                return False
            cyl.current_amount = round(cyl.current_amount - amount, 3)
            if cyl.current_amount <= 0:
                cyl.current_amount = 0.0
                cyl.status = "EMPTY"
        else:
            cyl.current_amount = round(cyl.current_amount + amount, 3)
            if cyl.current_amount > cyl.initial_amount and cyl.gas_category != "RECOVERED":
                cyl.initial_amount = cyl.current_amount
            if cyl.status == "EMPTY" and cyl.current_amount > 0:
                cyl.status = "AVAILABLE"

        self.save_gas_cylinder(cyl)

        rec = GasUsageRecord(
            cylinder_id=cyl.id,
            cylinder_code=cyl.code,
            gas_category=cyl.gas_category,
            gas_type=cyl.gas_type,
            movement_type=movement_type,
            amount=amount,
            unit=cyl.unit,
            remaining_after=cyl.current_amount,
            equipment_id=equipment_id,
            equipment_tag=equipment_tag,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            work_order_ref=work_order_ref,
            reason=reason or ("Uso / Carga en Equipo" if movement_type == "OUT" else "Ingreso / Recuperación de Gas"),
            notes=notes
        )
        self.storage.save_document("inventory/gas_movements", rec.id, "gas_movement.json", rec.to_dict())
        self.storage.update_index("inventory/gas_movements", rec.id, {
            "cylinder_id": rec.cylinder_id,
            "gas_category": rec.gas_category,
            "gas_type": rec.gas_type,
            "equipment_tag": rec.equipment_tag,
            "date": rec.date
        })

        # Also record in general panol_movements for unified traceability
        dest_str = f"Equipo {equipment_tag}" if equipment_tag else recipient_name
        if equipment_tag and recipient_name:
            dest_str = f"{recipient_name} -> Equipo {equipment_tag}"
        self.record_panol_movement(PanolMovement(
            item_id=cyl.id,
            item_name=f"Gas {cyl.gas_type}",
            item_code=cyl.code,
            item_category="GAS",
            movement_type=movement_type,
            quantity=amount,  # type: ignore
            unit=cyl.unit,
            recipient_type=recipient_type,
            recipient_name=dest_str,
            reason=rec.reason,
            reference=work_order_ref,
            notes=notes
        ))

        # If linked to an equipment, record in the equipment's parts_history.json
        if equipment_id and self.equipment_service:
            try:
                action_label = "Carga/Uso de Gas" if movement_type == "OUT" else "Recuperación de Gas"
                entry = {
                    "id": rec.id,
                    "movement_id": rec.id,
                    "part_id": cyl.id,
                    "part_name": f"Gas {cyl.gas_type} (Cilindro {cyl.code})",
                    "part_number": cyl.code,
                    "quantity": amount,
                    "unit": cyl.unit,
                    "reason": f"{action_label}: {rec.reason}",
                    "reference": work_order_ref,
                    "performed_by": recipient_name or "Técnico",
                    "date": rec.date,
                    "notes": notes
                }
                self.equipment_service.add_part_history_entry(equipment_id, entry)
            except Exception as e:
                print(f"Error recording gas usage in equipment history: {e}")

        return True

    def get_gas_movements(self, cylinder_id: Optional[str] = None, gas_category: Optional[str] = None) -> List[GasUsageRecord]:
        records = []
        index = self.storage.get_index("inventory/gas_movements")
        for r_id in index:
            data = self.storage.load_document("inventory/gas_movements", r_id, "gas_movement.json")
            if data:
                rec = GasUsageRecord.from_dict(data)
                if cylinder_id and rec.cylinder_id != cylinder_id:
                    continue
                if gas_category and rec.gas_category != gas_category:
                    continue
                records.append(rec)
        records.sort(key=lambda x: x.date, reverse=True)
        return records



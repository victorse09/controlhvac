import os
import shutil
from typing import List, Optional

from src.core.models.recycle_bin import RecycledItem
from src.data.json_storage import JsonStorageEngine

ITEM_TYPE_LABELS = {
    "CLIENT": "Cliente",
    "SITE": "Instalación",
    "EQUIPMENT": "Equipo",
    "WORK_ORDER": "Orden de Trabajo",
    "TOOL": "Herramienta",
    "SPARE_PART": "Repuesto",
    "PANOL_SUPPLY": "Insumo de Pañol",
    "EPP_ITEM": "Elemento EPP",
    "GAS_CYLINDER": "Cilindro de Gas",
    "INCIDENT": "Avería / Incidencia",
    "TECHNICIAN": "Técnico",
    "LIBRARY_DOCUMENT": "Documento Librería",
}

class RecycleBinService:
    """Service for managing the Recycle Bin (trash, restore, purge)."""

    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage

    def recycle_item(self, original_id: str, item_type: str, display_name: str, payload: dict, extra_info: dict = None) -> RecycledItem:
        item = RecycledItem.create(original_id, item_type, display_name, payload, extra_info)
        self.storage.save_document("recycle_bin", item.id, "item.json", item.to_dict())
        self.storage.update_index("recycle_bin", item.id, {
            "original_id": item.original_id,
            "item_type": item.item_type,
            "display_name": item.display_name,
            "deleted_at": item.deleted_at
        })
        return item

    def get_all_recycled_items(self) -> List[RecycledItem]:
        items = []
        index = self.storage.get_index("recycle_bin")
        for item_id in index:
            data = self.storage.load_document("recycle_bin", item_id, "item.json")
            if data:
                items.append(RecycledItem.from_dict(data))
        # Sort newest deleted first
        items.sort(key=lambda x: x.deleted_at, reverse=True)
        return items

    def get_recycled_item(self, item_id: str) -> Optional[RecycledItem]:
        data = self.storage.load_document("recycle_bin", item_id, "item.json")
        return RecycledItem.from_dict(data) if data else None

    def purge_item(self, item_id: str) -> bool:
        item = self.get_recycled_item(item_id)
        if item and item.item_type in ("LIBRARY_DOCUMENT", "library_document") and item.payload:
            f_path = item.payload.get("file_path", "")
            if f_path:
                abs_f = f_path if os.path.isabs(f_path) else os.path.join(self.storage.base_path, f_path)
                if os.path.isfile(abs_f):
                    try:
                        os.remove(abs_f)
                    except Exception:
                        pass
        item_dir = os.path.join(self.storage.base_path, "recycle_bin", item_id)
        try:
            if os.path.exists(item_dir):
                shutil.rmtree(item_dir)
        except Exception:
            return False
        self.storage.remove_from_index("recycle_bin", item_id)
        return True

    def empty_bin(self) -> bool:
        for item in self.get_all_recycled_items():
            self.purge_item(item.id)
        return True

    def restore_item(self, item_id: str, services_map: dict) -> bool:
        item = self.get_recycled_item(item_id)
        if not item or not item.payload:
            return False

        try:
            itype = item.item_type
            payload = item.payload
            
            if itype == "CLIENT" and "client_service" in services_map:
                from src.core.models.client import Client
                client = Client.from_dict(payload)
                services_map["client_service"].save_client(client)
                
            elif itype == "SITE" and "client_service" in services_map:
                from src.core.models.client import InstallationSite
                site = InstallationSite.from_dict(payload)
                services_map["client_service"].save_site(site)
                
            elif itype == "EQUIPMENT" and "equipment_service" in services_map:
                from src.core.models.equipment import HVACEquipment
                eq = HVACEquipment.from_dict(payload)
                services_map["equipment_service"].save_equipment(eq)
                
            elif itype == "WORK_ORDER" and "work_order_service" in services_map:
                from src.core.models.work_order import WorkOrder
                wo = WorkOrder.from_dict(payload)
                services_map["work_order_service"].save_work_order(wo)
                
            elif itype == "TOOL" and "inventory_service" in services_map:
                from src.core.models.inventory import Tool
                tool = Tool.from_dict(payload)
                services_map["inventory_service"].save_tool(tool)
                
            elif (itype == "SPARE_PART" or itype == "spare_part") and "inventory_service" in services_map:
                from src.core.models.inventory import SparePart
                part = SparePart.from_dict(payload)
                services_map["inventory_service"].save_spare_part(part)

            elif itype == "PANOL_SUPPLY" and "inventory_service" in services_map:
                from src.core.models.inventory import PanolSupply
                supply = PanolSupply.from_dict(payload)
                services_map["inventory_service"].save_supply(supply)

            elif itype == "EPP_ITEM" and "inventory_service" in services_map:
                from src.core.models.inventory import EppItem
                epp = EppItem.from_dict(payload)
                services_map["inventory_service"].save_epp(epp)

            elif itype == "GAS_CYLINDER" and "inventory_service" in services_map:
                from src.core.models.inventory import GasCylinder
                cyl = GasCylinder.from_dict(payload)
                services_map["inventory_service"].save_gas_cylinder(cyl)
                
            elif (itype == "INCIDENT" or itype == "incident") and "incident_service" in services_map:
                from src.core.models.incident import Incident
                inc = Incident.from_dict(payload)
                services_map["incident_service"].save_incident(inc)
                
            elif (itype == "TECHNICIAN" or itype == "technician") and "technician_service" in services_map:
                from src.core.models.technician import Technician
                tech = Technician.from_dict(payload)
                services_map["technician_service"].save_technician(tech)

            elif (itype == "LIBRARY_DOCUMENT" or itype == "library_document") and "library_service" in services_map:
                from src.core.models.library import LibraryDocument
                doc = LibraryDocument.from_dict(payload)
                services_map["library_service"].save_document_metadata(doc)

            else:
                return False

            # After restoring, purge from bin
            self.purge_item(item.id)
            return True
        except Exception as e:
            print(f"Error restoring item {item_id}: {e}")
            return False

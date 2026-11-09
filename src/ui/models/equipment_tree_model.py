import re
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QSize
from PySide6.QtGui import QColor, QBrush, QFont
from typing import List, Dict, Any
from src.core.models.enums import SYSTEM_TYPE_LABELS
from src.ui.icon_manager import IconManager
from src.ui.theme import get_current_palette


class TreeItem:
    def __init__(self, data: list, parent=None, node_type: str = "ROOT", item_data: Any = None):
        self.parent_item = parent
        self.item_data_list = data
        self.child_items = []
        self.node_type = node_type
        self.raw_data = item_data

    def append_child(self, item):
        self.child_items.append(item)

    def child(self, row):
        if row < 0 or row >= len(self.child_items):
            return None
        return self.child_items[row]

    def child_count(self):
        return len(self.child_items)

    def column_count(self):
        return len(self.item_data_list)

    def data(self, column):
        if column < 0 or column >= len(self.item_data_list):
            return None
        return self.item_data_list[column]

    def row(self):
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def parent(self):
        return self.parent_item

    @property
    def equipment(self):
        return self.raw_data if self.node_type == "EQUIPMENT" else None

    @property
    def name(self):
        return self.item_data_list[0] if self.item_data_list else ""

    @property
    def node_key(self) -> str:
        """Returns a unique persistent key for this tree node to preserve expansion and selection."""
        if self.node_type == "CLIENT" and self.raw_data:
            return f"CLIENT:{getattr(self.raw_data, 'id', self.name)}"
        elif self.node_type == "SITE" and self.raw_data:
            return f"SITE:{getattr(self.raw_data, 'id', self.name)}"
        elif self.node_type == "AREA" and isinstance(self.raw_data, dict):
            site = self.raw_data.get("site")
            sid = getattr(site, "id", "") if site else ""
            fname = self.raw_data.get("floor_name", self.name)
            return f"AREA:{sid}:{fname}"
        elif self.node_type == "EQUIPMENT" and self.raw_data:
            return f"EQUIPMENT:{getattr(self.raw_data, 'id', self.name)}"
        return f"{self.node_type}:{self.name}"


class EquipmentTreeModel(QAbstractItemModel):
    def __init__(self, equipment_service=None, client_service=None, parent=None):
        if not hasattr(equipment_service, 'get_all_equipment') and parent is None:
            parent = equipment_service
            equipment_service = None
            client_service = None
        super().__init__(parent)
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.headers = ["Nombre / Tag", "Tipo", "Estado Operativo", "Estado BMS/Ctrl", "ID BMS", "Piso / Área", "Próximo Servicio"]
        self.root_item = TreeItem(self.headers)
        if self.equipment_service and self.client_service:
            self.refresh()

    def _natural_sort_key(self, text: str):
        if not text:
            return []
        return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

    def _bms_sort_key(self, eq):
        bms = getattr(eq, 'bms_id', '') or ''
        if bms:
            return (0, self._natural_sort_key(bms), eq.tag.lower())
        return (1, [eq.tag.lower()], eq.tag.lower())

    def _format_eq_row(self, eq) -> list:
        raw_stype = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
        stype_label = SYSTEM_TYPE_LABELS.get(eq.system_type, SYSTEM_TYPE_LABELS.get(raw_stype, raw_stype))

        status_raw = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
        if status_raw == "FAULT":
            status_label = "En Falla"
        elif status_raw == "OPERATIONAL":
            status_label = "Operativo"
        elif status_raw == "WARNING":
            status_label = "En Observación"
        elif status_raw == "IN_MAINTENANCE":
            status_label = "En Mantenimiento"
        elif status_raw == "DECOMMISSIONED":
            status_label = "Fuera de Servicio"
        else:
            status_label = status_raw

        bms_status_str = getattr(eq, 'bms_status', '') or "Operativo"

        return [
            eq.tag,
            stype_label,
            status_label,
            bms_status_str,
            getattr(eq, 'bms_id', '') or "",
            getattr(eq, 'floor_area', '') or "",
            eq.last_service_date or ""
        ]

    def set_data(self, clients, sites, equipment):
        self.beginResetModel()
        # Keep reference to previous root until after endResetModel() so Qt/proxy internalPointers stay alive during reset
        self._old_root_item = getattr(self, "root_item", None)
        self.root_item = TreeItem(self.headers)
        
        # Build tree structure
        for client in clients:
            client_name = getattr(client, 'company_name', '') or getattr(client, 'name', '')
            client_sites = [s for s in sites if s.client_id == client.id]
            client_eq_count = sum(1 for e in equipment if e.client_id == client.id)
            client_item = TreeItem(
                [client_name, "Cliente", f"{len(client_sites)} sedes · {client_eq_count} equipos", "", "", "", ""],
                self.root_item,
                "CLIENT",
                client
            )
            self.root_item.append_child(client_item)
            
            for site in client_sites:
                site_eqs = [e for e in equipment if e.site_id == site.id]
                site_item = TreeItem(
                    [site.name, "Instalación", f"{len(site_eqs)} equipos", "", "", "", ""],
                    client_item,
                    "SITE",
                    site
                )
                client_item.append_child(site_item)
                
                has_floors = any(getattr(e, 'floor_area', '').strip() for e in site_eqs)

                if has_floors:
                    floors = {}
                    for eq in site_eqs:
                        f = getattr(eq, 'floor_area', '').strip() or "Sin Nivel / General"
                        floors.setdefault(f, []).append(eq)

                    for floor_name in sorted(floors.keys(), key=self._natural_sort_key):
                        f_eqs = floors[floor_name]
                        floor_item = TreeItem(
                            [floor_name, "Piso / Nivel", f"{len(f_eqs)} equipos", "", "", floor_name, ""],
                            site_item,
                            "AREA",
                            {"floor_name": floor_name, "site": site}
                        )
                        site_item.append_child(floor_item)
                        
                        f_eqs.sort(key=self._bms_sort_key)
                        for eq in f_eqs:
                            eq_item = TreeItem(self._format_eq_row(eq), floor_item, "EQUIPMENT", eq)
                            floor_item.append_child(eq_item)
                else:
                    site_eqs.sort(key=self._bms_sort_key)
                    for eq in site_eqs:
                        eq_item = TreeItem(self._format_eq_row(eq), site_item, "EQUIPMENT", eq)
                        site_item.append_child(eq_item)
                    
        self.endResetModel()
        
    def refresh(self):
        if self.equipment_service and self.client_service:
            clients = self.client_service.get_all_clients()
            sites = self.client_service.get_all_sites()
            equipment = self.equipment_service.get_all_equipment()
            self.set_data(clients, sites, equipment)
        else:
            self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.child_count()

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return parent.internalPointer().column_count()
        return self.root_item.column_count()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            val = item.data(col)
            if item.node_type == "EQUIPMENT" and col in (2, 3) and val:
                return f"●  {val}"
            return val

        elif role == Qt.ItemDataRole.DecorationRole:
            if col == 0:
                if item.node_type == "CLIENT":
                    return IconManager.get_icon("nav/clients.svg", "#38BDF8", 16)
                elif item.node_type == "SITE":
                    return IconManager.get_icon("actions/folder.svg", "#F59E0B", 16)
                elif item.node_type == "AREA":
                    return IconManager.get_icon("actions/folder.svg", "#A78BFA", 15)
                elif item.node_type == "EQUIPMENT" and item.equipment:
                    raw_st = item.equipment.system_type.value if hasattr(item.equipment.system_type, 'value') else str(item.equipment.system_type)
                    return IconManager.get_equipment_icon(raw_st, "#38BDF8")

        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if item.node_type == "CLIENT":
                font.setBold(True)
                font.setPointSize(10)
                return font
            elif item.node_type == "SITE":
                font.setBold(True)
                font.setPointSize(10)
                return font
            elif item.node_type == "AREA":
                font.setBold(True)
                return font
            elif item.node_type == "EQUIPMENT":
                if col in (0, 2, 3):
                    font.setWeight(QFont.Weight.DemiBold)
                    return font

        elif role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            text_pri = pal.get("TEXT_PRIMARY", "#F8FAFC")
            text_sec = pal.get("TEXT_SECONDARY", "#CBD5E1")
            text_mut = pal.get("TEXT_MUTED", "#94A3B8")
            accent = pal.get("ACCENT_PRIMARY", "#38BDF8")
            st_ok = pal.get("STATUS_OK", "#10B981")
            st_warn = pal.get("STATUS_WARN", "#F59E0B")
            st_err = pal.get("STATUS_ERROR", "#EF4444")

            if item.node_type == "CLIENT":
                return QBrush(QColor(accent)) if col == 0 else QBrush(QColor(text_mut))
            elif item.node_type == "SITE":
                return QBrush(QColor(text_pri)) if col == 0 else QBrush(QColor(text_mut))
            elif item.node_type == "AREA":
                if col == 0:
                    return QBrush(QColor(st_warn))
                elif col == 2:
                    return QBrush(QColor(accent))
                return QBrush(QColor(text_mut))
            elif item.node_type == "EQUIPMENT":
                if col == 0:
                    return QBrush(QColor(text_pri))
                elif col == 1:
                    return QBrush(QColor(text_sec))
                elif col == 2:
                    status = str(item.data(2))
                    if status in ("Operativo", "OPERATIONAL"):
                        return QBrush(QColor(st_ok))
                    elif status in ("En Observación", "En Advertencia", "WARNING"):
                        return QBrush(QColor(st_warn))
                    elif status in ("En Falla", "FAULT"):
                        return QBrush(QColor(st_err))
                    elif status in ("En Mantenimiento", "IN_MAINTENANCE"):
                        return QBrush(QColor("#3B82F6"))
                    return QBrush(QColor(text_mut))
                elif col == 3:
                    bms_st = str(item.data(3))
                    if bms_st == "Operativo":
                        return QBrush(QColor(st_ok))
                    elif bms_st in ("En Falla", "Sin Control"):
                        return QBrush(QColor(st_err))
                    elif bms_st == "Sin Grafica":
                        return QBrush(QColor(st_warn))
                    else:
                        return QBrush(QColor(text_mut))
                elif col == 4:
                    return QBrush(QColor(accent))

        elif role == Qt.ItemDataRole.BackgroundRole:
            pal = get_current_palette()
            if item.node_type == "CLIENT":
                return QBrush(QColor(pal.get("TREE_CLIENT_BG", "#17223B")))
            elif item.node_type == "SITE":
                return QBrush(QColor(pal.get("TREE_SITE_BG", "#151F34")))
            elif item.node_type == "AREA":
                return QBrush(QColor(pal.get("TREE_AREA_BG", "#131C2E")))
            elif item.node_type == "EQUIPMENT":
                if item.row() % 2 == 1:
                    return QBrush(QColor(pal.get("ROW_ALT", "#0D1526")))
                return QBrush(QColor(pal.get("BG_PRIMARY", "#0B1120")))

        elif role == Qt.ItemDataRole.SizeHintRole:
            if item.node_type in ("CLIENT", "SITE"):
                return QSize(-1, 34)
            elif item.node_type == "AREA":
                return QSize(-1, 31)
            return QSize(-1, 29)

        elif role == Qt.ItemDataRole.UserRole:
            return item.node_key

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.root_item.data(section)
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

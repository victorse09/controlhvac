from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSize
from PySide6.QtGui import QColor, QBrush, QFont
from src.ui.icon_manager import IconManager
from src.ui.theme import get_current_palette

class GenericTableModel(QAbstractTableModel):
    def __init__(self, headers, data=None, parent=None):
        if not isinstance(data, list) and parent is None and data is not None:
            parent = data
            data = None
        super().__init__(parent)
        self.headers = headers
        self._data = data if data is not None else []

    def set_data(self, data):
        self.beginResetModel()
        self._data = data if data is not None else []
        self.endResetModel()

    def update_data(self, data):
        self.set_data(data)

    @property
    def clients(self):
        return self._data

    @property
    def work_orders(self):
        return self._data

    @property
    def tools(self):
        return self._data

    @property
    def spare_parts(self):
        return self._data

    @property
    def sites(self):
        return self._data

    def add_item(self, item):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def remove_item(self, index):
        if 0 <= index < len(self._data):
            self.beginRemoveRows(QModelIndex(), index, index)
            self._data.pop(index)
            self.endRemoveRows()

    def refresh(self):
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def get_item(self, row):
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

class WorkOrderTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["N° Guía / OT", "Equipo / Destino", "Tipo de Guía / Servicio", "Prioridad", "Estado", "Fecha Programada", "Técnico Responsable"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        wo = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: 
                return wo.id
            if col == 1: 
                if getattr(wo, 'is_manual_equipment', False) and getattr(wo, 'manual_equipment_tag', ''):
                    return f"{wo.manual_equipment_tag} (Manual)"
                return wo.equipment_tag or getattr(wo, 'manual_equipment_tag', '') or "Sin equipo"
            if col == 2:
                g_kind = getattr(wo, 'guide_kind', '')
                s_type = getattr(wo, 'service_type', '')
                if g_kind == "SERVICE" or "OTS" in wo.id:
                    return f"Servicio: {s_type}" if s_type else "Guía de Servicio (OTS)"
                elif g_kind == "MAINTENANCE" or "OTM" in wo.id or "TOM" in wo.id:
                    return "Mantenimiento Preventivo (OTM)"
                return wo.work_order_type or "Servicio"
            if col == 3: 
                p_map = {"URGENT": "Urgente", "HIGH": "Alta", "NORMAL": "Normal", "LOW": "Baja"}
                p_val = wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority)
                return f"●  {p_map.get(p_val, p_val)}"
            if col == 4: 
                s_map = {"SCHEDULED": "Programada", "IN_PROGRESS": "En Progreso", "COMPLETED": "Completada", "OVERDUE": "Atrasada", "CANCELLED": "Cancelada"}
                s_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
                return f"●  {s_map.get(s_val, s_val)}"
            if col == 5: 
                return wo.scheduled_date
            if col == 6: 
                return getattr(wo, 'assigned_technician', '') or getattr(wo, 'assigned_to', '') or "Sin asignar"

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            g_kind = getattr(wo, 'guide_kind', '')
            if g_kind == "SERVICE" or "OTS" in (wo.id or ""):
                return IconManager.get_icon("tools.svg", "#38BDF8", 15)
            return IconManager.get_icon("calendar.svg", "#10B981", 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 3, 4):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            p_val = wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority)
            s_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
            if col == 0:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 3: # Priority
                if p_val == "URGENT": return QBrush(QColor("#EF4444"))
                if p_val == "HIGH": return QBrush(QColor("#F59E0B"))
                if p_val == "NORMAL": return QBrush(QColor("#38BDF8"))
                return QBrush(QColor(pal.get("TEXT_MUTED", "#94A3B8")))
            if col == 4: # Status
                if s_val == "COMPLETED": return QBrush(QColor("#10B981"))
                if s_val == "IN_PROGRESS": return QBrush(QColor("#3B82F6"))
                if s_val == "OVERDUE": return QBrush(QColor("#EF4444"))
                if s_val == "SCHEDULED": return QBrush(QColor("#F59E0B"))

        return None

class ClientTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Empresa", "RUT", "Contacto", "Teléfono", "Email", "Contrato"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        client = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return client.company_name
            if col == 1: return client.tax_id
            if col == 2: return client.contact_name
            if col == 3: return client.contact_phone
            if col == 4: return client.contact_email
            if col == 5: return client.contract_number
            return None

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            return IconManager.get_icon("nav/clients.svg", "#38BDF8", 15)

        if role == Qt.ItemDataRole.FontRole and col == 0:
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 0:
                return QBrush(QColor(pal.get("TEXT_PRIMARY", "#F8FAFC")))
            if col == 1:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 5 and getattr(client, 'contract_number', ''):
                return QBrush(QColor(pal.get("STATUS_OK", "#10B981")))

        return None

class ToolTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Nombre", "Marca", "Modelo", "Serial", "Estado", "Asignado A", "Calibración"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        tool = self._data[index.row()]
        col = index.column()

        st_val = tool.status.value if hasattr(tool.status, 'value') else str(tool.status)

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return tool.name
            if col == 1: return tool.brand
            if col == 2: return tool.model
            if col == 3: return tool.serial_number
            if col == 4:
                st_map = {
                    "AVAILABLE": "Disponible",
                    "IN_USE": "En Uso / Asignada",
                    "IN_CALIBRATION": "En Calibración",
                    "OUT_OF_SERVICE": "Fuera de Servicio"
                }
                return f"●  {st_map.get(st_val, st_val)}"
            if col == 5: return getattr(tool, 'assigned_to', '') or "Disponible en Pañol"
            if col == 6: return tool.next_calibration

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            return IconManager.get_icon("tools.svg", "#818CF8", 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 4):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 4:
                if st_val == "AVAILABLE": return QBrush(QColor("#10B981"))
                if st_val == "IN_USE": return QBrush(QColor("#F59E0B"))
                if st_val == "OUT_OF_SERVICE": return QBrush(QColor("#EF4444"))

        return None


class PanolSupplyTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Insumo", "Código", "Categoría", "Stock Actual", "Stock Mín.", "Unidad", "Ubicación", "Proveedor"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        item = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return item.name
            if col == 1: return item.code or "-"
            if col == 2: return item.category
            if col == 3: return f"●  {item.quantity}"
            if col == 4: return str(item.minimum_quantity)
            if col == 5: return item.unit
            if col == 6: return item.location or "Pañol"
            if col == 7: return item.supplier or "-"

        if role == Qt.ItemDataRole.FontRole and col in (0, 3):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 1:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 3:
                if item.quantity <= 0:
                    return QBrush(QColor("#EF4444"))
                elif item.quantity <= item.minimum_quantity:
                    return QBrush(QColor("#F59E0B"))
                else:
                    return QBrush(QColor("#10B981"))
        return None


class EppDeliveryTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Elemento EPP", "Código", "Categoría", "Talla / Modelo", "Marca", "Stock Actual", "Stock Mín.", "Ubicación"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        epp = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return epp.name
            if col == 1: return epp.code or "-"
            if col == 2: return epp.category
            if col == 3: return epp.size_or_model or "Estándar"
            if col == 4: return epp.brand or "-"
            if col == 5: return f"●  {epp.quantity} {epp.unit}"
            if col == 6: return str(epp.minimum_quantity)
            if col == 7: return epp.location or "Pañol"

        if role == Qt.ItemDataRole.FontRole and col in (0, 5):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 1:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 5:
                if epp.quantity <= 0:
                    return QBrush(QColor("#EF4444"))
                elif epp.quantity <= epp.minimum_quantity:
                    return QBrush(QColor("#F59E0B"))
                else:
                    return QBrush(QColor("#10B981"))
        return None


class EppAssignmentTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Equipo / Elemento", "Código / Serie", "Categoría", "Marca / Modelo", "Estado", "Asignado A (Cargo)", "Fecha Asignación", "Venc. / Inspección"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        epp = self._data[index.row()]
        col = index.column()
        st = (epp.status or "AVAILABLE").upper()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return epp.name
            if col == 1: return epp.serial_number or epp.code or "-"
            if col == 2: return epp.category
            if col == 3: return f"{epp.brand or ''} {epp.size_or_model or ''}".strip() or "-"
            if col == 4:
                st_map = {
                    "AVAILABLE": "Disponible en Pañol",
                    "ASSIGNED": "Asignado (En Cargo)",
                    "IN_INSPECTION": "En Revisión / Mantención",
                    "OUT_OF_SERVICE": "Dado de Baja / Fuera de Servicio"
                }
                return f"●  {st_map.get(st, st)}"
            if col == 5: return epp.assigned_to or "Sin asignar (Pañol)"
            if col == 6: return epp.assigned_date or "-"
            if col == 7: return epp.expiration_date or "-"

        if role == Qt.ItemDataRole.FontRole and col in (0, 4):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 1:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 4:
                if st == "AVAILABLE": return QBrush(QColor("#10B981"))
                if st == "ASSIGNED": return QBrush(QColor("#38BDF8"))
                if st == "IN_INSPECTION": return QBrush(QColor("#F59E0B"))
                if st == "OUT_OF_SERVICE": return QBrush(QColor("#EF4444"))
        return None


class PanolMovementTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Fecha y Hora", "Sección", "Operación", "Elemento / Ítem", "Cant.", "Destinatario / Origen", "Tipo Destinatario", "Motivo / Referencia", "Responsable"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        mov = self._data[index.row()]
        col = index.column()

        m_type = (mov.movement_type or "IN").upper()
        cat = (mov.item_category or "SUPPLY").upper()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                dt_str = mov.date or ""
                if "T" in dt_str:
                    return dt_str[:16].replace("T", " ")
                return dt_str
            if col == 1:
                cat_map = {
                    "SUPPLY": "Insumos",
                    "EPP_DELIVERY": "EPP (Entrega)",
                    "EPP_ASSIGNMENT": "EPP (Asignación)",
                    "TOOL": "Herramientas",
                    "GAS": "Gases / Cilindros"
                }
                return cat_map.get(cat, cat)
            if col == 2:
                op_map = {
                    "IN": "Ingreso (+)",
                    "OUT": "Entrega (-)",
                    "ASSIGN": "Asignación (Cargo)",
                    "RETURN": "Devolución a Pañol"
                }
                return f"●  {op_map.get(m_type, m_type)}"
            if col == 3:
                return f"{mov.item_name} ({mov.item_code})" if mov.item_code else mov.item_name
            if col == 4:
                sign = "+" if m_type in ("IN", "RETURN") else "-"
                return f"{sign}{mov.quantity} {mov.unit}"
            if col == 5:
                return mov.recipient_name or ("Ingreso Bodega/Pañol" if m_type == "IN" else "-")
            if col == 6:
                rt_map = {
                    "TECHNICIAN": "Técnico Interno",
                    "EXTERNAL": "Personal Externo",
                    "SITE": "Recinto / Instalación"
                }
                return rt_map.get(mov.recipient_type, "-")
            if col == 7:
                ref = f" [Ref: {mov.reference}]" if mov.reference else ""
                return f"{mov.reason}{ref}"
            if col == 8:
                return mov.performed_by or "Pañolero"

        if role == Qt.ItemDataRole.FontRole and col in (2, 3, 4):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            if col in (2, 4):
                if m_type in ("IN", "RETURN"):
                    return QBrush(QColor("#10B981"))
                if m_type == "OUT":
                    return QBrush(QColor("#F59E0B"))
                if m_type == "ASSIGN":
                    return QBrush(QColor("#38BDF8"))
        return None


class GasCylinderTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(
            ["N° Cilindro / Tubo", "Categoría", "Tipo de Gas", "Contenido Inicial", "Usado / Recuperado", "Queda en Cilindro", "Estado", "Ubicación / Asignado"],
            data,
            parent
        )

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        cyl = self._data[index.row()]
        col = index.column()
        cat = (cyl.gas_category or "REFRIGERANT").upper()
        st = (cyl.status or "AVAILABLE").upper()
        u = cyl.unit or "Kg"

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return cyl.code or "-"
            if col == 1:
                cat_map = {
                    "WELDING": "Soldadura / Presurización",
                    "REFRIGERANT": "Refrigerante (Bombona)",
                    "RECOVERED": "Refrigerante Recuperado",
                    "CLEANING": "Agente Limpieza (R-141b)"
                }
                return cat_map.get(cat, cat)
            if col == 2:
                return cyl.gas_type
            if col == 3:
                if cat == "RECOVERED":
                    return f"Cap. Máx: {cyl.initial_amount:g} {u}"
                return f"{cyl.initial_amount:g} {u}"
            if col == 4:
                if cat == "RECOVERED":
                    return f"Almacenado: {cyl.current_amount:g} {u}"
                return f"{cyl.used_amount:g} {u}"
            if col == 5:
                return f"{cyl.current_amount:g} {u}"
            if col == 6:
                st_map = {
                    "AVAILABLE": "En Pañol (Disponible)",
                    "IN_USE": "En Terreno / Uso",
                    "EMPTY": "Vacío",
                    "RETURNED": "Devuelto a Proveedor"
                }
                return f"●  {st_map.get(st, st)}"
            if col == 7:
                return cyl.assigned_to if cyl.assigned_to else (cyl.location or "Pañol")

        if role == Qt.ItemDataRole.FontRole and col in (0, 2, 5, 6):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 0:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 5:
                if cat != "RECOVERED" and cyl.current_amount <= 0:
                    return QBrush(QColor("#EF4444"))
                elif cat != "RECOVERED" and cyl.current_amount <= (cyl.initial_amount * 0.2):
                    return QBrush(QColor("#F59E0B"))
                return QBrush(QColor("#38BDF8"))
            if col == 6:
                if st == "AVAILABLE": return QBrush(QColor("#10B981"))
                if st == "IN_USE": return QBrush(QColor("#F59E0B"))
                if st == "EMPTY": return QBrush(QColor("#EF4444"))
        return None


class SparePartTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Nombre", "Código", "Categoría", "Cantidad", "Mínimo", "Ubicación", "Proveedor"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        part = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return part.name
            if col == 1: return part.part_number
            if col == 2: return part.category
            if col == 3: return f"●  {part.quantity}"
            if col == 4: return str(part.minimum_quantity)
            if col == 5: return part.location
            if col == 6: return part.supplier

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            return IconManager.get_icon("spare_parts.svg", "#38BDF8", 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 3):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 1:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 3:
                if part.quantity <= 0:
                    return QBrush(QColor("#EF4444"))
                elif part.quantity <= part.minimum_quantity:
                    return QBrush(QColor("#F59E0B"))
                return QBrush(QColor("#10B981"))
        return None

class SiteTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Nombre", "Dirección", "Contacto", "Teléfono", "Email"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 30)

        site = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return getattr(site, 'name', '')
            if col == 1: return getattr(site, 'address', '')
            if col == 2: return getattr(site, 'contact_person', '')
            if col == 3: return getattr(site, 'contact_phone', '')
            if col == 4: return getattr(site, 'contact_email', '')
            return None

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            return IconManager.get_icon("actions/folder.svg", "#F59E0B", 15)

        if role == Qt.ItemDataRole.FontRole and col == 0:
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        return None

class EquipmentTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["Tag / Equipo", "Tipo", "Estado", "ID BMS", "Piso / Área", "Ubicación", "Fabricante / Modelo"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        eq = self._data[index.row()]
        col = index.column()
        status_val = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
        stype_val = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return eq.tag
            if col == 1:
                from src.core.models.enums import SYSTEM_TYPE_LABELS
                return SYSTEM_TYPE_LABELS.get(eq.system_type, SYSTEM_TYPE_LABELS.get(stype_val, stype_val))
            if col == 2: 
                if status_val == "FAULT": return "●  En Falla"
                if status_val == "OPERATIONAL": return "●  Operativo"
                if status_val == "WARNING": return "●  En Observación"
                if status_val == "IN_MAINTENANCE": return "●  En Mantenimiento"
                if status_val == "DECOMMISSIONED": return "●  Fuera de Servicio"
                return f"●  {status_val}"
            if col == 3: return getattr(eq, 'bms_id', '') or ""
            if col == 4: return getattr(eq, 'floor_area', '') or ""
            if col == 5: return getattr(eq, 'location_description', '') or ""
            if col == 6: return f"{eq.manufacturer or ''} {eq.model_number or ''}".strip() or "N/A"

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            return IconManager.get_equipment_icon(stype_val, "#38BDF8")

        if role == Qt.ItemDataRole.FontRole and col in (0, 2):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 2: # Status
                if status_val == "FAULT": return QBrush(QColor("#EF4444"))
                if status_val == "OPERATIONAL": return QBrush(QColor("#10B981"))
                if status_val == "WARNING": return QBrush(QColor("#F59E0B"))
                if status_val == "IN_MAINTENANCE": return QBrush(QColor("#3B82F6"))
            if col == 3:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))

        return None

class IncidentTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None, equipment_service=None):
        super().__init__(["Código", "Fecha", "Equipo", "ID BMS", "Estado BMS / Ctrl", "Tipo / Especialidad", "Severidad", "Estado", "Título / Trabajo", "Notas / Falla", "Técnico Responsable"], data, parent)
        self.equipment_service = equipment_service

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        inc = self._data[index.row()]
        col = index.column()

        # Cache eq retrieval if needed
        eq_obj = None
        if self.equipment_service and inc.equipment_id:
            eq_obj = self.equipment_service.get_equipment(inc.equipment_id)

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return inc.id
            if col == 1: return inc.reported_date
            if col == 2: return inc.equipment_tag
            if col == 3:
                bms = getattr(inc, 'bms_id', '') or ""
                if not bms and eq_obj:
                    bms = getattr(eq_obj, 'bms_id', '') or ""
                return bms
            if col == 4:
                bms_st = ""
                if eq_obj:
                    bms_st = getattr(eq_obj, 'bms_status', '') or ""
                return f"●  {bms_st or 'Operativo'}"
            if col == 5: return inc.type_display
            if col == 6: return f"●  {inc.severity_display}"
            if col == 7: return f"●  {inc.status_display}"
            if col == 8: return inc.title
            if col == 9: return inc.notes or inc.diagnosis or inc.description or "-"
            if col == 10: return inc.technician or "Sin asignar"

        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
            c_hex = "#EF4444" if sev_val == "CRITICA" else ("#F59E0B" if sev_val == "ALTA" else "#38BDF8")
            return IconManager.get_icon("fault.svg", c_hex, 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 2, 4, 6, 7):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ToolTipRole:
            notes_str = inc.notes or "Sin notas"
            diag_str = inc.diagnosis or "Sin diagnóstico"
            desc_str = inc.description or "Sin descripción"
            bms_val = getattr(inc, 'bms_id', '') or ""
            bms_st_val = getattr(eq_obj, 'bms_status', '') if eq_obj else ""
            bms_line = f"ID BMS: {bms_val}\n" if bms_val else ""
            bms_st_line = f"Estado BMS/Ctrl: {bms_st_val}\n" if bms_st_val else ""
            return f"Incidencia: {inc.id} - {inc.title}\nEquipo: {inc.equipment_tag}\n{bms_line}{bms_st_line}Notas: {notes_str}\nDiagnóstico: {diag_str}\nDescripción: {desc_str}"

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
            st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)

            if col in (0, 3):
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))

            if col == 4: # Estado BMS
                bms_st = getattr(eq_obj, 'bms_status', '') if eq_obj else ""
                if bms_st in ["En Falla", "Sin Control", "Sin Grafica", "Fuera de Servicio", "Inexistente"]:
                    return QBrush(QColor("#EF4444"))
                elif not bms_st or bms_st == "Operativo":
                    return QBrush(QColor("#10B981"))
                elif bms_st:
                    return QBrush(QColor("#F59E0B"))

            if col == 6: # Severity
                if sev_val == "CRITICA": return QBrush(QColor("#EF4444"))
                if sev_val == "ALTA": return QBrush(QColor("#F59E0B"))
                if sev_val == "MEDIA": return QBrush(QColor("#38BDF8"))
                if sev_val == "BAJA": return QBrush(QColor("#94A3B8"))

            if col == 7: # Status
                if st_val == "RESUELTA": return QBrush(QColor("#10B981"))
                if st_val == "EN_REPARACION": return QBrush(QColor("#3B82F6"))
                if st_val == "ESPERANDO_REPUESTOS": return QBrush(QColor("#F59E0B"))
                if st_val == "REPORTADA": return QBrush(QColor("#EF4444"))

        return None

class TechnicianTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(["RUT / Código", "Nombre y Apellidos", "Especialidad", "Estado", "Teléfono", "Email", "Certificación / SEC"], data, parent)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        t = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return t.code
            if col == 1: return t.full_name
            if col == 2:
                from src.core.models.enums import TECHNICIAN_SPECIALTY_LABELS
                return TECHNICIAN_SPECIALTY_LABELS.get(t.specialty, t.specialty)
            if col == 3:
                from src.core.models.enums import TECHNICIAN_STATUS_LABELS
                lbl = TECHNICIAN_STATUS_LABELS.get(t.status, t.status)
                return f"●  {lbl}"
            if col == 4: return t.phone or "-"
            if col == 5: return t.email or "-"
            if col == 6: return t.license_number or "-"

        if role == Qt.ItemDataRole.DecorationRole and col == 1:
            return IconManager.get_icon("nav/technicians.svg", "#38BDF8", 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 1, 3):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ToolTipRole:
            notes = t.notes or "Sin notas"
            return f"Técnico: {t.full_name}\nRUT: {t.code}\nEspecialidad: {t.specialty}\nEstado: {t.status}\nNotas: {notes}"

        if role == Qt.ItemDataRole.ForegroundRole:
            pal = get_current_palette()
            if col == 0:
                return QBrush(QColor(pal.get("ACCENT_PRIMARY", "#38BDF8")))
            if col == 3: # Status
                st = t.status.upper() if t.status else ""
                if "ACTIVO" in st and "INACTIVO" not in st:
                    return QBrush(QColor("#10B981"))
                elif "INACTIVO" in st:
                    return QBrush(QColor("#EF4444"))
                elif "VACACIONES" in st or "LICENCIA" in st:
                    return QBrush(QColor("#F59E0B"))

        return None


class LibraryTableModel(GenericTableModel):
    def __init__(self, data=None, parent=None, equipment_service=None):
        super().__init__(["Categoría", "Título del Documento", "Archivo", "Tamaño", "Equipos Asociados", "Fecha Registro"], data, parent)
        self.equipment_service = equipment_service

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.SizeHintRole:
            return QSize(-1, 31)

        doc = self._data[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                from src.core.models.enums import LIBRARY_CATEGORY_LABELS
                lbl = LIBRARY_CATEGORY_LABELS.get(doc.category, doc.category)
                return f"●  {lbl}"
            if col == 1: return doc.title
            if col == 2: return doc.file_name or "-"
            if col == 3: return doc.formatted_size
            if col == 4:
                eq_count = len(doc.equipment_ids)
                if eq_count == 0:
                    return "Ninguno (General)"
                elif eq_count == 1:
                    if self.equipment_service:
                        eq = self.equipment_service.get_equipment(doc.equipment_ids[0])
                        if eq:
                            return f"{eq.tag} ({eq.name})"
                    return doc.equipment_ids[0]
                else:
                    return f"{eq_count} equipos vinculados"
            if col == 5:
                # Format date YYYY-MM-DD to DD-MM-YYYY
                dt = doc.created_at[:10] if doc.created_at else ""
                if len(dt) == 10 and dt[4] == '-' and dt[7] == '-':
                    parts = dt.split('-')
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
                return dt

        if role == Qt.ItemDataRole.DecorationRole and col == 1:
            return IconManager.get_icon("pdf.svg", "#38BDF8", 15)

        if role == Qt.ItemDataRole.FontRole and col in (0, 1):
            f = QFont()
            f.setWeight(QFont.Weight.DemiBold)
            return f

        if role == Qt.ItemDataRole.ToolTipRole:
            desc = doc.description or "Sin descripción"
            tags_str = ", ".join(doc.tags) if doc.tags else "Ninguna"
            return f"Título: {doc.title}\nArchivo: {doc.file_name} ({doc.formatted_size})\nDescripción: {desc}\nEtiquetas: {tags_str}"

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 0: # Category
                cat = doc.category.upper() if doc.category else ""
                if "MANUAL" in cat:
                    return QBrush(QColor("#38BDF8")) # Sky blue
                elif "DATASHEET" in cat:
                    return QBrush(QColor("#818CF8")) # Indigo
                elif "SAFETY" in cat:
                    return QBrush(QColor("#F59E0B")) # Amber
                elif "DIAGRAM" in cat:
                    return QBrush(QColor("#10B981")) # Emerald
                elif "IMAGE" in cat:
                    return QBrush(QColor("#EC4899")) # Pink

        return None

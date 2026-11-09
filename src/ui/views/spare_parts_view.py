import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView, 
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView, QInputDialog,
    QTabWidget, QListWidget, QListWidgetItem, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QCursor
from datetime import datetime

from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.models.table_models import SparePartTableModel
from src.ui.dialogs.spare_part_dialog import SparePartDialog
from src.ui.dialogs.stock_movement_dialog import StockMovementDialog
from src.ui.icon_manager import IconManager
from src.core.models.enums import SYSTEM_TYPE_LABELS


class SparePartsView(QWidget):
    def __init__(self, inventory_service, equipment_service=None, client_service=None, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.parts = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar repuestos por código, nombre, fabricante, modelo...")
        self.search_bar.textChanged.connect(self.on_search)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #334155; margin: 2px 2px;")
        
        self.btn_in = QPushButton()
        self.btn_in.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 18))
        self.btn_in.setIconSize(QSize(18, 18))
        self.btn_in.setFixedSize(36, 36)
        self.btn_in.setToolTip("Registrar Entrada de Stock (+)")
        self.btn_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_in.clicked.connect(self.on_stock_in)
        
        self.btn_out = QPushButton()
        self.btn_out.setIcon(IconManager.get_icon("arrow_up.svg", "#F59E0B", 18))
        self.btn_out.setIconSize(QSize(18, 18))
        self.btn_out.setFixedSize(36, 36)
        self.btn_out.setToolTip("Registrar Salida de Stock (-)")
        self.btn_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_out.clicked.connect(self.on_stock_out)

        self.btn_new = QPushButton()
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#FFFFFF", 18))
        self.btn_new.setIconSize(QSize(18, 18))
        self.btn_new.setFixedSize(36, 36)
        self.btn_new.setToolTip("Nuevo Repuesto")
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new)
        
        toolbar.addWidget(self.search_bar, 1)
        toolbar.addWidget(sep)
        toolbar.addWidget(self.btn_in)
        toolbar.addWidget(self.btn_out)
        toolbar.addWidget(self.btn_new)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Table (Left Side)
        self.table = QTableView()
        self.model = SparePartTableModel([])
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_edit_double_click)
        self.splitter.addWidget(self.table)

        # Detail Panel (Right Side)
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Detail header actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel("Seleccione un repuesto")
        self.lbl_title.setObjectName("detailTitleLabel")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar Repuesto seleccionado")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Repuesto seleccionado")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete)
        header_layout.addWidget(self.btn_delete)

        detail_layout.addLayout(header_layout)

        # Tabs for Detail: General / Equipos Asociados / Últimos Movimientos
        self.tabs = QTabWidget()

        # TAB 1: General Info
        tab_general = QWidget()
        tab_gen_layout = QVBoxLayout(tab_general)
        tab_gen_layout.setContentsMargins(8, 8, 8, 8)
        
        scroll_gen = QScrollArea()
        scroll_gen.setWidgetResizable(True)
        scroll_gen.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        gen_content = QWidget()
        self.detail_content_layout = QVBoxLayout(gen_content)
        self.detail_content_layout.setContentsMargins(0, 0, 4, 0)
        self.detail_content_layout.setSpacing(10)
        
        scroll_gen.setWidget(gen_content)
        tab_gen_layout.addWidget(scroll_gen)
        self.tabs.addTab(tab_general, "Ficha General")

        # TAB 2: Equipos que usan este repuesto
        tab_equipment = QWidget()
        tab_eq_layout = QVBoxLayout(tab_equipment)
        tab_eq_layout.setContentsMargins(8, 8, 8, 8)
        tab_eq_layout.setSpacing(6)

        self.lbl_eq_summary = QLabel("Equipos donde este repuesto está asignado o es compatible:")
        self.lbl_eq_summary.setObjectName("muted")
        tab_eq_layout.addWidget(self.lbl_eq_summary)

        self.list_equipment = QListWidget()
        self.list_equipment.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        tab_eq_layout.addWidget(self.list_equipment)
        self.tabs.addTab(tab_equipment, "Equipos Asignados (0)")

        # TAB 3: Últimos Movimientos
        tab_movements = QWidget()
        tab_mov_layout = QVBoxLayout(tab_movements)
        tab_mov_layout.setContentsMargins(8, 8, 8, 8)
        tab_mov_layout.setSpacing(6)

        self.lbl_mov_summary = QLabel("Historial de entradas y salidas de stock:")
        self.lbl_mov_summary.setObjectName("muted")
        tab_mov_layout.addWidget(self.lbl_mov_summary)

        self.list_movements = QListWidget()
        self.list_movements.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        tab_mov_layout.addWidget(self.list_movements)
        self.tabs.addTab(tab_movements, "Movimientos (0)")

        detail_layout.addWidget(self.tabs)

        self.splitter.addWidget(self.detail_frame)
        storage = getattr(self.inventory_service, "storage", None)
        setup_modern_table(
            self.table,
            storage=storage,
            settings_key="spare_parts_table",
            default_widths=[180, 105, 115, 85, 75, 115, 130],
            splitter=self.splitter,
            default_splitter_sizes=[540, 460],
        )

    def get_selected_part(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.get_item(indexes[0].row())

    def refresh_data(self):
        try:
            self.parts = self.inventory_service.get_all_spare_parts()
            self.model.set_data(self.parts)
            self.on_selection_changed()
        except Exception as e:
            print(f"Error refreshing spare parts: {e}")

    def on_search(self, text):
        query = text.strip().lower()
        if not query:
            self.model.set_data(self.parts)
            return

        filtered = [
            p for p in self.parts
            if query in (p.name or '').lower() or
               query in (p.part_number or '').lower() or
               query in (getattr(p, 'category', '') or '').lower() or
               query in (getattr(p, 'supplier', '') or '').lower() or
               query in (getattr(p, 'location', '') or '').lower()
        ]
        self.model.set_data(filtered)

    def on_selection_changed(self):
        part = self.get_selected_part()
        clear_layout_widgets(self.detail_content_layout)
        if not part:
            self.lbl_title.setText("Seleccione un repuesto")
            self.detail_content_layout.addWidget(
                build_empty_detail_card("Haga clic en un repuesto de la tabla para ver su stock disponible, ubicación, valorización e historial.")
            )
            self.detail_content_layout.addStretch()
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.list_equipment.clear()
            self.list_movements.clear()
            self.tabs.setTabText(1, "Equipos Asignados (0)")
            self.tabs.setTabText(2, "Movimientos (0)")
            return

        self.lbl_title.setText(part.name)
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        unit_str = getattr(part, 'unit', 'UNID')
        cost = getattr(part, 'unit_cost', 0.0) or 0.0
        currency = getattr(part, 'currency', 'CLP')
        total_val = part.quantity * cost

        if part.quantity <= 0:
            st_lbl, st_fg, st_bg = f"Sin Stock (0 {unit_str})", "#EF4444", "#450A0A"
        elif part.quantity <= part.minimum_quantity:
            st_lbl, st_fg, st_bg = f"Stock Bajo ({part.quantity} {unit_str})", "#F59E0B", "#451A03"
        else:
            st_lbl, st_fg, st_bg = f"Disponible ({part.quantity} {unit_str})", "#10B981", "#064E3B"

        self.detail_content_layout.addWidget(
            build_status_banner([
                ("ESTADO DE INVENTARIO", st_lbl, st_fg, st_bg),
                ("STOCK MÍNIMO", f"{part.minimum_quantity} {unit_str}", "#38BDF8", "#0C4A6E"),
            ])
        )

        info_rows = [
            ("Nombre del Repuesto", f"<b>{html.escape(part.name or '')}</b>"),
            ("Código / N° Parte", f"<b style='color: #38BDF8;'>{html.escape(part.part_number or 'N/A')}</b>"),
            ("Categoría", html.escape(getattr(part, 'category', 'General') or 'General')),
            ("Stock Disponible", f"<b style='color: {st_fg};'>{part.quantity} {html.escape(unit_str)}</b>"),
            ("Ubicación en Bodega", html.escape(part.location or 'N/A')),
            ("Proveedor / Fabricante", html.escape(part.supplier or 'N/A')),
        ]
        self.detail_content_layout.addWidget(
            build_section_card("Identificación y Ubicación", "#38BDF8", build_kv_widget(info_rows))
        )

        val_rows = [
            ("Costo Unitario", f"<b>${cost:,.0f} {html.escape(currency)}</b>"),
            ("Valorización Total Stock", f"<b style='color: #10B981;'>${total_val:,.0f} {html.escape(currency)}</b>"),
        ]
        self.detail_content_layout.addWidget(
            build_section_card("Valorización", "#10B981", build_kv_widget(val_rows))
        )

        notes_parts = []
        if hasattr(part, 'description') and part.description:
            notes_parts.append(f"<b>Descripción:</b> {html.escape(part.description)}")
        if hasattr(part, 'notes') and part.notes:
            notes_parts.append(f"<b>Notas:</b> {html.escape(part.notes)}")
        if notes_parts:
            self.detail_content_layout.addWidget(
                build_section_card("Descripción y Notas", "#A855F7", build_rich_label("<br>".join(notes_parts)))
            )

        self.detail_content_layout.addStretch()

        self._load_associated_equipment(part)
        self._load_movements(part)

    def _load_associated_equipment(self, part):
        self.list_equipment.clear()
        if not self.equipment_service:
            item = QListWidgetItem("Servicio de equipos no disponible")
            self.list_equipment.addItem(item)
            return

        part_name_norm = (part.name or '').strip().lower()
        part_code_norm = (part.part_number or '').strip().lower()
        
        all_equipment = self.equipment_service.get_all_equipment()
        matching_eqs = []

        for eq in all_equipment:
            is_match = False
            match_reason = ""

            eq_parts = getattr(eq, 'spare_parts', []) or []
            for sp in eq_parts:
                sp_str = ""
                if isinstance(sp, dict):
                    sp_str = sp.get('name', '') or sp.get('part_number', '') or ''
                else:
                    sp_str = str(sp)
                
                sp_str_norm = sp_str.strip().lower()
                if (part_name_norm and (part_name_norm in sp_str_norm or sp_str_norm in part_name_norm)) or \
                   (part_code_norm and part_code_norm in sp_str_norm):
                    is_match = True
                    match_reason = f"Asignado al equipo ({sp_str})"
                    break

            if not is_match and getattr(eq, 'technical_specs', None):
                specs = eq.technical_specs
                for k, v in specs.items():
                    if isinstance(v, str) and v.strip():
                        v_lower = v.strip().lower()
                        if (part_name_norm and part_name_norm in v_lower) or \
                           (part_code_norm and part_code_norm in v_lower):
                            is_match = True
                            match_reason = f"En especificación técnica ({k}: {v})"
                            break

            if not is_match and hasattr(part, 'compatible_equipment') and part.compatible_equipment:
                eq_type = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
                if eq_type in part.compatible_equipment:
                    is_match = True
                    type_label = SYSTEM_TYPE_LABELS.get(eq.system_type, eq_type) if hasattr(eq, 'system_type') else eq_type
                    match_reason = f"Compatible por tipo de sistema ({type_label})"

            if is_match:
                matching_eqs.append((eq, match_reason))

        self.tabs.setTabText(1, f"Equipos Asignados ({len(matching_eqs)})")

        if not matching_eqs:
            item = QListWidgetItem("No se encontraron equipos que utilicen este repuesto actualmente.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_equipment.addItem(item)
            return

        for eq, reason in matching_eqs:
            bms_txt = f" | ID BMS: {eq.bms_id}" if getattr(eq, 'bms_id', '') else ""
            floor_txt = f" | Piso/Área: {eq.floor_area}" if getattr(eq, 'floor_area', '') else ""
            loc_txt = f" ({eq.location_description})" if eq.location_description else ""
            
            title_text = f"⚙️ {eq.tag}{bms_txt} - {eq.manufacturer} {eq.model_number}"
            sub_text = f"    Ubicación: {floor_txt}{loc_txt} | Motivo: {reason}"
            
            item = QListWidgetItem(f"{title_text}\n{sub_text}")
            self.list_equipment.addItem(item)

    def _load_movements(self, part):
        self.list_movements.clear()
        try:
            movements = self.inventory_service.get_movements(part.id)
        except Exception:
            movements = []

        self.tabs.setTabText(2, f"Movimientos ({len(movements)})")

        if not movements:
            item = QListWidgetItem("No hay registros de movimientos para este repuesto.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_movements.addItem(item)
            return

        unit_str = getattr(part, 'unit', 'UNID')
        for mov in movements[:40]:
            mov_type = getattr(mov, 'movement_type', None) or getattr(mov, 'type', 'IN')
            is_in = (mov_type == "IN")
            
            type_symbol = "🟢 ENTRADA" if is_in else "🔴 SALIDA"
            qty_text = f"+{mov.quantity}" if is_in else f"-{mov.quantity}"
            
            date_str = mov.date
            if "T" in date_str:
                try:
                    dt = datetime.fromisoformat(date_str)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_str = date_str[:16].replace("T", " ")

            reason_str = getattr(mov, 'reason', '') or ("Ingreso de stock" if is_in else "Salida de stock")
            
            details_parts = []
            if getattr(mov, 'equipment_tag', ''):
                details_parts.append(f"Equipo: {mov.equipment_tag}")
            if getattr(mov, 'destination', ''):
                details_parts.append(f"Destino: {mov.destination}")
            if getattr(mov, 'reference', ''):
                details_parts.append(f"Ref/Doc: {mov.reference}")
            if getattr(mov, 'performed_by', ''):
                details_parts.append(f"Por: {mov.performed_by}")
            if getattr(mov, 'notes', ''):
                details_parts.append(f"Nota: {mov.notes}")
            
            details_str = " | ".join(details_parts)
            
            item_text = f"{type_symbol} {qty_text} {unit_str}  [{reason_str}]  —  {date_str}\n    {details_str if details_str else 'Sin detalles adicionales'}"
            item = QListWidgetItem(item_text)
            self.list_movements.addItem(item)

    def on_new(self):
        dialog = SparePartDialog(parent=self)
        if dialog.exec():
            p = dialog.get_spare_part()
            self.inventory_service.save_spare_part(p)
            self.refresh_data()

    def on_edit_clicked(self):
        part = self.get_selected_part()
        if part:
            dialog = SparePartDialog(parent=self, spare_part=part)
            if dialog.exec():
                updated = dialog.get_spare_part()
                self.inventory_service.save_spare_part(updated)
                self.refresh_data()

    def on_edit_double_click(self, index):
        part = self.model.get_item(index.row())
        if part:
            dialog = SparePartDialog(parent=self, spare_part=part)
            if dialog.exec():
                updated = dialog.get_spare_part()
                self.inventory_service.save_spare_part(updated)
                self.refresh_data()

    def on_delete(self):
        part = self.get_selected_part()
        if not part:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar Repuesto",
            f"¿Está seguro de que desea eliminar el repuesto '{part.name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.inventory_service.delete_spare_part(part.id):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el repuesto.")

    def on_stock_in(self):
        part = self.get_selected_part()
        if not part:
            QMessageBox.warning(self, "Entrada Stock", "Por favor seleccione un repuesto para ingresar stock.")
            return

        dialog = StockMovementDialog(
            spare_part=part, 
            movement_type="IN", 
            equipment_service=self.equipment_service, 
            client_service=self.client_service, 
            parent=self
        )
        if dialog.exec():
            data = dialog.get_movement_data()
            if self.inventory_service.register_movement(**data):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar la entrada de stock.")

    def on_stock_out(self):
        part = self.get_selected_part()
        if not part:
            QMessageBox.warning(self, "Salida Stock", "Por favor seleccione un repuesto para descontar stock.")
            return

        if part.quantity <= 0:
            QMessageBox.warning(self, "Salida Stock", f"El repuesto '{part.name}' no tiene stock disponible.")
            return

        dialog = StockMovementDialog(
            spare_part=part, 
            movement_type="OUT", 
            equipment_service=self.equipment_service, 
            client_service=self.client_service, 
            parent=self
        )
        if dialog.exec():
            data = dialog.get_movement_data()
            if self.inventory_service.register_movement(**data):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar la salida de stock.")

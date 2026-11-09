import os
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView, 
    QPushButton, QLabel, QFrame, QMessageBox, QComboBox, QHeaderView,
    QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.models.table_models import WorkOrderTableModel
from src.ui.dialogs.work_order_dialog import WorkOrderDialog
from src.core.models.enums import (
    WorkOrderStatus, WorkOrderType, Priority,
    WORK_ORDER_TYPE_LABELS, WORK_ORDER_STATUS_LABELS, PRIORITY_LABELS
)
from src.ui.icon_manager import IconManager


class WorkOrdersView(QWidget):
    def __init__(self, work_order_service, equipment_service, client_service, inventory_service, export_service, technician_service=None, parent=None):
        super().__init__(parent)
        self.work_order_service = work_order_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.export_service = export_service
        self.technician_service = technician_service
        self.all_wos = []
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
        self.search_bar.setPlaceholderText("Buscar por código OTS/OTM, título, equipo, responsable...")
        self.search_bar.textChanged.connect(self._apply_filters)
        
        self.cb_guide_kind = QComboBox()
        self.cb_guide_kind.setMinimumWidth(150)
        self.cb_guide_kind.addItem("Todas las guías", "")
        self.cb_guide_kind.addItem("Guías de Servicio (OTS)", "SERVICE")
        self.cb_guide_kind.addItem("Guías de Mantenimiento (OTM)", "MAINTENANCE")
        self.cb_guide_kind.currentIndexChanged.connect(self._apply_filters)
        
        self.cb_status = QComboBox()
        self.cb_status.setMinimumWidth(130)
        self.cb_status.addItem("Todos los estados", "")
        for status, label in WORK_ORDER_STATUS_LABELS.items():
            val = status.value if hasattr(status, 'value') else str(status)
            self.cb_status.addItem(label, val)
        self.cb_status.currentIndexChanged.connect(self._apply_filters)
        
        self.cb_priority = QComboBox()
        self.cb_priority.setMinimumWidth(130)
        self.cb_priority.addItem("Todas las prioridades", "")
        for priority, label in PRIORITY_LABELS.items():
            val = priority.value if hasattr(priority, 'value') else str(priority)
            self.cb_priority.addItem(label, val)
        self.cb_priority.currentIndexChanged.connect(self._apply_filters)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #334155; margin: 2px 2px;")
        
        self.btn_export_pdf = QPushButton()
        self.btn_export_pdf.setIcon(IconManager.get_icon("pdf.svg", "#38BDF8", 18))
        self.btn_export_pdf.setIconSize(QSize(18, 18))
        self.btn_export_pdf.setFixedSize(36, 36)
        self.btn_export_pdf.setToolTip("Exportar Orden / Guía a PDF")
        self.btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_pdf.clicked.connect(self.on_export_pdf)
        
        self.btn_new_service = QPushButton(" + Servicio (OTS)")
        self.btn_new_service.setObjectName("primaryButton")
        self.btn_new_service.setIcon(IconManager.get_icon("tools.svg", "#FFFFFF", 16))
        self.btn_new_service.setIconSize(QSize(16, 16))
        self.btn_new_service.setToolTip("Crear nueva Guía de Servicio Técnico (Correlativo OTS)")
        self.btn_new_service.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_service.clicked.connect(self.on_new_service)

        self.btn_new_maint = QPushButton(" + Mantenimiento (OTM)")
        self.btn_new_maint.setIcon(IconManager.get_icon("calendar.svg", "#38BDF8", 16))
        self.btn_new_maint.setIconSize(QSize(16, 16))
        self.btn_new_maint.setToolTip("Crear nueva Guía de Mantenimiento Preventivo (Correlativo OTM)")
        self.btn_new_maint.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_maint.clicked.connect(self.on_new_maintenance)
        
        toolbar.addWidget(self.search_bar, 1)
        toolbar.addWidget(self.cb_guide_kind)
        toolbar.addWidget(self.cb_status)
        toolbar.addWidget(self.cb_priority)
        toolbar.addWidget(sep)
        toolbar.addWidget(self.btn_export_pdf)
        toolbar.addWidget(self.btn_new_service)
        toolbar.addWidget(self.btn_new_maint)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Left Table
        self.table = QTableView()
        self.model = WorkOrderTableModel([])
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_edit)
        self.splitter.addWidget(self.table)

        # Right Detail Panel
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel("Seleccione una Guía u OT")
        self.lbl_title.setObjectName("detailTitleLabel")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar / Ver Guía")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Guía / OT")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete_wo)
        header_layout.addWidget(self.btn_delete)

        detail_layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        detail_content = QWidget()
        self.detail_content_layout = QVBoxLayout(detail_content)
        self.detail_content_layout.setContentsMargins(0, 0, 4, 0)
        self.detail_content_layout.setSpacing(10)
        scroll.setWidget(detail_content)
        detail_layout.addWidget(scroll, 1)

        self.splitter.addWidget(self.detail_frame)
        storage = getattr(self.work_order_service, "storage", None)
        setup_modern_table(
            self.table,
            storage=storage,
            settings_key="work_orders_table",
            default_widths=[115, 130, 175, 95, 115, 115, 135],
            splitter=self.splitter,
            default_splitter_sizes=[580, 420],
        )

    def get_selected_wo(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.get_item(indexes[0].row())

    def refresh_data(self):
        try:
            self.all_wos = self.work_order_service.get_all_work_orders()
            self._apply_filters()
        except Exception as e:
            print(f"Error refreshing work orders: {e}")

    def _apply_filters(self):
        query = self.search_bar.text().strip().lower()
        guide_kind_filter = self.cb_guide_kind.currentData()
        status_filter = self.cb_status.currentData()
        priority_filter = self.cb_priority.currentData()

        filtered = []
        for wo in self.all_wos:
            g_kind = getattr(wo, 'guide_kind', '') or ("SERVICE" if "OTS" in (wo.id or "") else "MAINTENANCE")
            sstatus = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
            spriority = wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority)

            if guide_kind_filter and g_kind != guide_kind_filter:
                continue
            if status_filter and sstatus != status_filter:
                continue
            if priority_filter and spriority != priority_filter:
                continue
            if query:
                text_match = (
                    query in (wo.title or '').lower() or 
                    query in (wo.equipment_tag or '').lower() or 
                    query in (getattr(wo, 'manual_equipment_tag', '') or '').lower() or
                    query in (wo.id or '').lower() or
                    query in (wo.description or '').lower() or
                    query in (getattr(wo, 'service_type', '') or '').lower() or
                    query in (wo.assigned_technician or '').lower()
                )
                if not text_match:
                    continue
            filtered.append(wo)

        self.model.set_data(filtered)
        self.on_selection_changed()

    def _get_status_style(self, status_val: str) -> tuple[str, str]:
        s = (status_val or "").upper()
        if s == "COMPLETED":
            return "#10B981", "#064E3B"
        elif s == "IN_PROGRESS":
            return "#3B82F6", "#1E3A8A"
        elif s == "OVERDUE":
            return "#EF4444", "#450A0A"
        elif s == "SCHEDULED":
            return "#F59E0B", "#451A03"
        return "#94A3B8", "#1E293B"

    def _get_priority_style(self, prio_val: str) -> tuple[str, str]:
        p = (prio_val or "").upper()
        if p in ("URGENT", "CRITICAL"):
            return "#EF4444", "#450A0A"
        elif p == "HIGH":
            return "#F59E0B", "#451A03"
        elif p in ("NORMAL", "MEDIUM"):
            return "#38BDF8", "#0C4A6E"
        return "#94A3B8", "#1E293B"

    def on_selection_changed(self):
        wo = self.get_selected_wo()
        clear_layout_widgets(self.detail_content_layout)
        if not wo:
            self.lbl_title.setText("Seleccione una Guía")
            self.detail_content_layout.addWidget(
                build_empty_detail_card("Haga clic en una Guía de Servicio (OTS) o Mantenimiento (OTM) para visualizar su ficha detallada.")
            )
            self.detail_content_layout.addStretch()
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            return

        status_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
        status_label = WORK_ORDER_STATUS_LABELS.get(wo.status, WORK_ORDER_STATUS_LABELS.get(status_val, status_val))
        prio_raw = wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority)
        priority_val = PRIORITY_LABELS.get(wo.priority, PRIORITY_LABELS.get(prio_raw, prio_raw))
        tech = getattr(wo, 'assigned_technician', '') or getattr(wo, 'assigned_to', '') or 'Sin asignar'

        is_service = getattr(wo, 'guide_kind', '') == "SERVICE" or (wo.id and wo.id.startswith("OTS"))
        type_str = getattr(wo, 'service_type', '') or ("Servicio Técnico" if is_service else "Mantenimiento Preventivo")
        
        is_manual = getattr(wo, 'is_manual_equipment', False)
        if is_manual:
            equip_display = f"<b>{html.escape(wo.manual_equipment_tag or wo.equipment_tag or 'N/A')}</b> <span style='color: #F59E0B;'>(Manual)</span>"
            client_display = html.escape(getattr(wo, 'manual_client', '') or wo.client_name or "-")
            loc_display = html.escape(getattr(wo, 'manual_location', '') or "-")
        else:
            equip_display = f"<b style='color: #38BDF8;'>{html.escape(wo.equipment_tag or 'N/A')}</b>"
            client_display = html.escape(wo.client_name or "-")
            loc_display = "-"

        self.lbl_title.setText(f"{wo.id}")
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        st_fg, st_bg = self._get_status_style(status_val)
        pr_fg, pr_bg = self._get_priority_style(prio_raw)
        self.detail_content_layout.addWidget(
            build_status_banner([
                ("ESTADO DE LA ORDEN", status_label, st_fg, st_bg),
                ("PRIORIDAD", priority_val, pr_fg, pr_bg),
            ])
        )

        guide_badge = "Guía de Servicio Técnico (OTS)" if is_service else "Guía de Mantenimiento Preventivo (OTM)"
        info_rows = [
            ("N° de Guía / OT", f"<b style='color: #38BDF8;'>{html.escape(wo.id)}</b>"),
            ("Tipo de Documento", f"<b>{html.escape(guide_badge)}</b>"),
            ("Título / Asunto", f"<b>{html.escape(wo.title or '')}</b>"),
            ("Modalidad", html.escape(type_str)),
            ("Equipo / Unidad", equip_display),
        ]
        if client_display and client_display != "-":
            info_rows.append(("Cliente / Sede", client_display))
        if loc_display and loc_display != "-":
            info_rows.append(("Ubicación", loc_display))
        info_rows.extend([
            ("Fecha Programada", f"<b>{html.escape(wo.scheduled_date or 'Sin fecha')}</b>"),
            ("Técnico Asignado", f"<b style='color: #10B981;'>{html.escape(tech)}</b>"),
        ])

        self.detail_content_layout.addWidget(
            build_section_card("Información de la Orden", "#38BDF8", build_kv_widget(info_rows))
        )

        # Diagnosis & Work Performed
        work_rows = []
        if getattr(wo, 'diagnosis', None):
            work_rows.append(("Diagnóstico / Motivo", html.escape(wo.diagnosis)))
        elif wo.description:
            work_rows.append(("Descripción", html.escape(wo.description)))
        if getattr(wo, 'work_performed', None):
            work_rows.append(("Trabajos Realizados", f"<span style='color: #10B981;'>{html.escape(wo.work_performed)}</span>"))

        if work_rows:
            self.detail_content_layout.addWidget(
                build_section_card("Detalle Técnico de Ejecución", "#F59E0B", build_kv_widget(work_rows))
            )

        # Materials used
        mats = getattr(wo, 'materials_used', []) or getattr(wo, 'parts_used', [])
        if mats:
            mat_strs = []
            for m in mats:
                if isinstance(m, dict):
                    qty = m.get('quantity', 1)
                    unit = html.escape(str(m.get('unit', 'unid')))
                    name = html.escape(str(m.get('name') or m.get('part_name', 'Repuesto')))
                    mat_strs.append(f"• <b>{qty} {unit}</b> — {name}")
                else:
                    mat_strs.append(f"• {html.escape(str(m))}")
            self.detail_content_layout.addWidget(
                build_section_card("Materiales y Repuestos Utilizados", "#10B981", build_rich_label("<br>".join(mat_strs)))
            )

        if getattr(wo, 'observations', None):
            self.detail_content_layout.addWidget(
                build_section_card("Observaciones", "#A855F7", build_rich_label(html.escape(wo.observations).replace("\n", "<br>")))
            )

        self.detail_content_layout.addStretch()

    def on_new_service(self):
        equipments = self.equipment_service.get_all_equipment()
        next_code = self.work_order_service.get_next_service_code()
        dialog = WorkOrderDialog(
            parent=self, 
            equipment_list=equipments, 
            guide_kind="SERVICE",
            preassigned_id=next_code,
            inventory_service=self.inventory_service,
            client_service=self.client_service,
            technician_service=self.technician_service
        )
        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)
            self.refresh_data()

    def on_new_maintenance(self):
        equipments = self.equipment_service.get_all_equipment()
        next_code = self.work_order_service.get_next_maintenance_code()
        dialog = WorkOrderDialog(
            parent=self, 
            equipment_list=equipments, 
            guide_kind="MAINTENANCE",
            preassigned_id=next_code,
            inventory_service=self.inventory_service,
            client_service=self.client_service,
            technician_service=self.technician_service
        )
        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)
            self.refresh_data()

    def on_new_wo(self):
        self.on_new_service()

    def on_edit_clicked(self):
        wo = self.get_selected_wo()
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(
                parent=self, 
                equipment_list=equipments, 
                work_order=wo,
                inventory_service=self.inventory_service,
                client_service=self.client_service,
                technician_service=self.technician_service,
                read_only=True
            )
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()

    def on_edit(self, index):
        wo = self.model.get_item(index.row())
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(
                parent=self, 
                equipment_list=equipments, 
                work_order=wo,
                inventory_service=self.inventory_service,
                client_service=self.client_service,
                technician_service=self.technician_service,
                read_only=True
            )
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()

    def on_delete_wo(self):
        wo = self.get_selected_wo()
        if not wo:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar Guía / Orden de Trabajo",
            f"¿Está seguro de que desea eliminar {wo.id} ({wo.title})?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.work_order_service.delete_work_order(wo.id):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la Guía / Orden de Trabajo.")

    def on_export_pdf(self):
        wo = self.get_selected_wo()
        if not wo:
            QMessageBox.warning(self, "Exportar PDF", "Por favor seleccione una Guía / Orden de Trabajo para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Guía en PDF",
            os.path.expanduser(f"~/{wo.id}.pdf"),
            "Archivos PDF (*.pdf)"
        )
        if file_path:
            try:
                from src.app.state_manager import StateManager
                logo_p = StateManager().get_logo_path()
                self.export_service.export_work_order_pdf(wo, file_path, logo_path=logo_p)
                QMessageBox.information(self, "Éxito", f"El PDF se guardó correctamente en:\n\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al generar el PDF: {e}")

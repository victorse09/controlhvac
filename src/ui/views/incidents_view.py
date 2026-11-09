import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QSplitter,
    QPushButton, QLabel, QFrame, QMessageBox, QComboBox,
    QHeaderView, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QSize
from PySide6.QtGui import QCursor

from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.models.table_models import IncidentTableModel
from src.ui.dialogs.incident_dialog import IncidentDialog
from src.core.models.enums import (
    IncidentType, IncidentSeverity, IncidentStatus,
    INCIDENT_TYPE_LABELS, INCIDENT_SEVERITY_LABELS, INCIDENT_STATUS_LABELS,
    EquipmentStatus, GuideKind, Priority
)
from src.core.services.export_service import format_chilean_date
from src.ui.icon_manager import IconManager


class IncidentFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.type_filter = ""
        self.severity_filter = ""
        self.status_filter = ""
        self.search_pattern = ""

    def set_filters(self, search="", itype="", severity="", status=""):
        self.search_pattern = search.lower()
        self.type_filter = itype
        self.severity_filter = severity
        self.status_filter = status
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        inc = model.get_item(source_row)
        if not inc:
            return False

        if self.type_filter:
            t_val = inc.incident_type.value if hasattr(inc.incident_type, 'value') else str(inc.incident_type)
            if t_val != self.type_filter:
                return False

        if self.severity_filter:
            s_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
            if s_val != self.severity_filter:
                return False

        if self.status_filter:
            st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
            if st_val != self.status_filter:
                return False

        if self.search_pattern:
            bms_val = getattr(inc, 'bms_id', '') or ""
            searchable = f"{inc.id} {inc.title} {inc.equipment_tag} {bms_val} {inc.technician} {inc.description} {inc.action_taken}".lower()
            if self.search_pattern not in searchable:
                return False

        return True


class IncidentsView(QWidget):
    """View for managing equipment breakdowns, observations, and repair histories."""

    def __init__(self, incident_service, equipment_service, client_service, inventory_service=None, export_service=None, work_order_service=None, technician_service=None, library_service=None, parent=None):
        super().__init__(parent)
        self.incident_service = incident_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.export_service = export_service
        self.work_order_service = work_order_service
        self.technician_service = technician_service
        self.library_service = library_service
        
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Top Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.stat_total = StatCard("Total Averías e Incidencias", "0", IconManager.get_icon("fault.svg", "#38BDF8"), accent_color="#38BDF8")
        self.stat_critical = StatCard("Averías Críticas", "0", IconManager.get_icon("warning.svg", "#EF4444"), accent_color="#EF4444")
        self.stat_bms = StatCard("Estado BMS / CTRL", "0", IconManager.get_icon("tools.svg", "#A855F7"), accent_color="#A855F7")
        self.stat_in_progress = StatCard("En Reparación / Pendientes", "0", IconManager.get_icon("tools.svg", "#F59E0B"), accent_color="#F59E0B")
        self.stat_resolved = StatCard("Resueltas / Reparadas", "0", IconManager.get_icon("check.svg", "#10B981"), accent_color="#10B981")

        stats_layout.addWidget(self.stat_total)
        stats_layout.addWidget(self.stat_critical)
        stats_layout.addWidget(self.stat_bms)
        stats_layout.addWidget(self.stat_in_progress)
        stats_layout.addWidget(self.stat_resolved)
        main_layout.addLayout(stats_layout)

        # 2. Toolbar & Filters
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar por código, equipo, título, notas...")
        self.search_bar.setMinimumWidth(180)
        self.search_bar.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self.search_bar, 1)

        self.combo_filter_type = QComboBox()
        self.combo_filter_type.setMinimumWidth(130)
        self.combo_filter_type.addItem("Todos los tipos", "")
        for itype, label in INCIDENT_TYPE_LABELS.items():
            self.combo_filter_type.addItem(label, itype.value)
        self.combo_filter_type.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self.combo_filter_type)

        self.combo_filter_sev = QComboBox()
        self.combo_filter_sev.setMinimumWidth(130)
        self.combo_filter_sev.addItem("Todas las severidades", "")
        for sev, label in INCIDENT_SEVERITY_LABELS.items():
            self.combo_filter_sev.addItem(label, sev.value)
        self.combo_filter_sev.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self.combo_filter_sev)

        self.combo_filter_status = QComboBox()
        self.combo_filter_status.setMinimumWidth(130)
        self.combo_filter_status.addItem("Todos los estados", "")
        for st, label in INCIDENT_STATUS_LABELS.items():
            self.combo_filter_status.addItem(label, st.value)
        self.combo_filter_status.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self.combo_filter_status)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #334155; margin: 2px 2px;")
        toolbar.addWidget(sep)

        def create_icon_btn(icon_name, color, tooltip, on_click, object_name=None):
            btn = QPushButton()
            btn.setIcon(IconManager.get_icon(icon_name, color, 18))
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(36, 36)
            btn.setToolTip(tooltip)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            if object_name:
                btn.setObjectName(object_name)
            btn.clicked.connect(on_click)
            return btn

        self.btn_new = create_icon_btn("add.svg", "#FFFFFF", "Nueva Avería / Observación", self.on_new_incident, "primaryButton")
        toolbar.addWidget(self.btn_new)

        self.btn_edit = create_icon_btn("edit.svg", "#F8FAFC", "Editar Avería / Incidencia", self.on_edit_incident)
        toolbar.addWidget(self.btn_edit)

        self.btn_new_ots = create_icon_btn(
            "tools.svg", "#38BDF8", 
            "Crear Guía de Servicio Técnico (OTS) para la avería seleccionada", 
            self.on_create_service_guide
        )
        toolbar.addWidget(self.btn_new_ots)

        self.btn_new_otm = create_icon_btn(
            "calendar.svg", "#10B981", 
            "Crear Guía de Mantenimiento (OTM) para la avería seleccionada", 
            self.on_create_maint_guide
        )
        toolbar.addWidget(self.btn_new_otm)

        self.btn_delete = create_icon_btn("delete.svg", "#FFFFFF", "Eliminar Avería Seleccionada", self.on_delete_incident, "dangerButton")
        toolbar.addWidget(self.btn_delete)

        self.btn_sync = create_icon_btn(
            "refresh.svg", "#38BDF8", 
            "Sincronizar Estados: Genera o actualiza incidencias desde equipos en Falla, Observación o Fuera de Servicio", 
            self.on_sync_equipment
        )
        toolbar.addWidget(self.btn_sync)

        self.btn_pdf = create_icon_btn(
            "pdf.svg", "#38BDF8", 
            "Generar Listados y Reportes PDF de Averías (Por Piso, General, Equipos en Falla, BMS, etc.)...", 
            self.on_export_pdf_dialog
        )
        toolbar.addWidget(self.btn_pdf)

        self.btn_export = create_icon_btn(
            "excel.svg", "#10B981", 
            "Exportar Incidencias a archivo CSV / Excel", 
            self.on_export_csv
        )
        toolbar.addWidget(self.btn_export)

        main_layout.addLayout(toolbar)

        # 3. Splitter: Left Table + Right Detail Card Panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        table_frame = QFrame()
        table_frame.setObjectName("cardFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableView()
        self.model = IncidentTableModel([], equipment_service=self.equipment_service)
        self.proxy_model = IncidentFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.table.setModel(self.proxy_model)

        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_edit_incident)

        table_layout.addWidget(self.table)
        self.splitter.addWidget(table_frame)

        # Right Detail Panel
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        self.detail_frame.setMinimumWidth(360)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_detail_title = QLabel("Seleccione una avería")
        self.lbl_detail_title.setObjectName("detailTitleLabel")
        self.lbl_detail_title.setWordWrap(True)
        header_layout.addWidget(self.lbl_detail_title, 1)
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
        storage = getattr(self.incident_service, "storage", None)
        setup_modern_table(
            self.table,
            storage=storage,
            settings_key="incidents_table",
            default_widths=[100, 95, 115, 85, 125, 130, 100, 120, 180, 210, 130],
            splitter=self.splitter,
            default_splitter_sizes=[660, 400],
        )
        self._update_incident_detail(None)

    def _get_incident_status_style(self, st_val: str) -> tuple[str, str]:
        st = (st_val or "").upper()
        if st == "RESUELTA":
            return "#10B981", "#064E3B"
        elif st == "EN_REPARACION":
            return "#3B82F6", "#1E3A8A"
        elif st == "ESPERANDO_REPUESTOS" or st == "EN_DIAGNOSTICO":
            return "#F59E0B", "#451A03"
        elif st == "REPORTADA":
            return "#EF4444", "#450A0A"
        return "#94A3B8", "#1E293B"

    def _get_severity_style(self, sev_val: str) -> tuple[str, str]:
        s = (sev_val or "").upper()
        if s == "CRITICA":
            return "#EF4444", "#450A0A"
        elif s == "ALTA":
            return "#F59E0B", "#451A03"
        elif s == "MEDIA":
            return "#38BDF8", "#0C4A6E"
        return "#94A3B8", "#1E293B"

    def on_selection_changed(self, selected=None, deselected=None):
        inc = self.get_selected_incident()
        self._update_incident_detail(inc)

    def _update_incident_detail(self, inc):
        clear_layout_widgets(self.detail_content_layout)
        if not inc:
            self.lbl_detail_title.setText("Seleccione una avería")
            self.detail_content_layout.addWidget(
                build_empty_detail_card("Haga clic en una avería o incidencia de la tabla para ver su estado, severidad, diagnóstico y trabajos realizados.")
            )
            self.detail_content_layout.addStretch()
            return

        self.lbl_detail_title.setText(f"{inc.id} — {inc.equipment_tag or 'Sin Equipo'}")

        st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
        sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
        st_fg, st_bg = self._get_incident_status_style(st_val)
        sev_fg, sev_bg = self._get_severity_style(sev_val)

        self.detail_content_layout.addWidget(
            build_status_banner([
                ("ESTADO INCIDENCIA", inc.status_display, st_fg, st_bg),
                ("SEVERIDAD", inc.severity_display, sev_fg, sev_bg),
            ])
        )

        bms_id = getattr(inc, 'bms_id', '') or ""
        bms_status = "Operativo"
        floor_area = ""
        if self.equipment_service and inc.equipment_id:
            eq = self.equipment_service.get_equipment(inc.equipment_id)
            if eq:
                bms_id = bms_id or getattr(eq, 'bms_id', '') or ""
                bms_status = getattr(eq, 'bms_status', 'Operativo') or "Operativo"
                floor_area = getattr(eq, 'floor_area', '') or ""

        ident_rows = [
            ("Código Incidencia", f"<b style='color: #38BDF8;'>{html.escape(inc.id)}</b>"),
            ("Título / Resumen", f"<b>{html.escape(inc.title or 'N/A')}</b>"),
            ("Equipo Afectado", f"<b style='color: #F8FAFC;'>{html.escape(inc.equipment_tag or 'N/A')}</b>"),
            ("ID BMS / Control", html.escape(bms_id) if bms_id else "<i style='color: #64748B;'>No asignado</i>"),
            ("Estado BMS", f"<b>{html.escape(bms_status)}</b>"),
            ("Piso / Área", html.escape(floor_area or "General")),
            ("Tipo / Especialidad", html.escape(inc.type_display)),
            ("Fecha Reporte", html.escape(format_chilean_date(inc.reported_date))),
            ("Técnico Responsable", html.escape(inc.technician or "Sin asignar")),
        ]
        if getattr(inc, 'work_order_id', ''):
            ident_rows.append(("Guía / OT Asociada", f"<b style='color: #10B981;'>{html.escape(inc.work_order_id)}</b>"))
        if inc.resolved_date:
            ident_rows.append(("Fecha Resolución", f"<b style='color: #10B981;'>{html.escape(format_chilean_date(inc.resolved_date))}</b>"))

        self.detail_content_layout.addWidget(
            build_section_card("Identificación de la Avería", "#38BDF8", build_kv_widget(ident_rows))
        )

        # Diagnosis & Action Taken
        diag_rows = []
        if inc.description:
            diag_rows.append(("Descripción Falla", html.escape(inc.description)))
        if inc.diagnosis:
            diag_rows.append(("Diagnóstico Técnico", html.escape(inc.diagnosis)))
        if inc.action_taken:
            diag_rows.append(("Trabajo Realizado", f"<span style='color: #10B981;'>{html.escape(inc.action_taken)}</span>"))
        if inc.labor_hours:
            diag_rows.append(("Horas Hombre", f"{inc.labor_hours:g} hrs"))
        if inc.cost_estimate:
            diag_rows.append(("Costo Estimado", f"${inc.cost_estimate:,.0f}"))

        if diag_rows:
            self.detail_content_layout.addWidget(
                build_section_card("Diagnóstico y Trabajos Realizados", "#F59E0B", build_kv_widget(diag_rows))
            )

        if inc.parts_used:
            parts_html = "<br>".join(f"• <b>{html.escape(str(p))}</b>" for p in inc.parts_used)
            self.detail_content_layout.addWidget(
                build_section_card("Repuestos e Insumos Utilizados", "#10B981", build_rich_label(parts_html))
            )

        if inc.notes:
            self.detail_content_layout.addWidget(
                build_section_card("Notas y Observaciones", "#A855F7", build_rich_label(html.escape(inc.notes).replace("\n", "<br>")))
            )

        self.detail_content_layout.addStretch()

    def on_sync_equipment(self):
        try:
            added = self.incident_service.sync_from_existing_equipment(self.equipment_service)
            if added > 0:
                QMessageBox.information(
                    self, 
                    "Sincronización de Equipos", 
                    f"Se han incorporado exitosamente {added} incidencias a partir de equipos en falla o en observación."
                )
            else:
                QMessageBox.information(
                    self,
                    "Sincronización de Equipos",
                    "Todos los equipos en falla o en observación ya se encuentran sincronizados en el panel de incidencias."
                )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al sincronizar equipos: {e}")

    def refresh_data(self):
        try:
            if self.equipment_service:
                self.incident_service.sync_from_existing_equipment(self.equipment_service)

            incidents = self.incident_service.get_all_incidents()
            self.model.set_data(incidents)

            self.stat_total.set_value(str(len(incidents)))

            critical_count = sum(
                1 for inc in incidents 
                if (inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)) == "CRITICA"
            )
            self.stat_critical.set_value(str(critical_count))

            in_prog_count = sum(
                1 for inc in incidents 
                if (inc.status.value if hasattr(inc.status, 'value') else str(inc.status)) in ["REPORTADA", "EN_DIAGNOSTICO", "ESPERANDO_REPUESTOS", "EN_REPARACION"]
            )
            self.stat_in_progress.set_value(str(in_prog_count))

            resolved_count = sum(
                1 for inc in incidents 
                if (inc.status.value if hasattr(inc.status, 'value') else str(inc.status)) == "RESUELTA"
            )
            self.stat_resolved.set_value(str(resolved_count))

            bms_count = 0
            if self.equipment_service:
                all_eq = self.equipment_service.get_all_equipment()
                for eq in all_eq:
                    bms_st = (getattr(eq, 'bms_status', '') or '').strip()
                    if bms_st and bms_st not in ["Operativo", "OPERATIONAL"]:
                        bms_count += 1
            else:
                for inc in incidents:
                    bms_st = (getattr(inc, 'bms_status', '') or '').strip()
                    if bms_st and bms_st not in ["", "Operativo", "OPERATIONAL"]:
                        bms_count += 1
            self.stat_bms.set_value(str(bms_count))

            self._apply_filters()
            self.on_selection_changed()
        except Exception as e:
            print(f"Error refreshing incidents view: {e}")

    def _apply_filters(self):
        search_txt = self.search_bar.text()
        itype = self.combo_filter_type.currentData()
        sev = self.combo_filter_sev.currentData()
        status = self.combo_filter_status.currentData()
        self.proxy_model.set_filters(search=search_txt, itype=itype, severity=sev, status=status)

    def get_selected_incident(self):
        indexes = self.table.selectionModel().selectedIndexes()
        if not indexes:
            return None
        src_index = self.proxy_model.mapToSource(indexes[0])
        if not src_index.isValid():
            return None
        return self.model.get_item(src_index.row())

    def on_new_incident(self):
        dialog = IncidentDialog(
            parent=self,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            inventory_service=self.inventory_service,
            work_order_service=self.work_order_service,
            technician_service=self.technician_service
        )
        if dialog.exec():
            new_inc = dialog.get_incident()
            self.incident_service.save_incident(new_inc)

            if dialog.chk_update_eq_status.isChecked() and new_inc.equipment_id:
                self._sync_equipment_status(new_inc)

            self.refresh_data()

    def on_edit_incident(self):
        inc = self.get_selected_incident()
        if not inc:
            QMessageBox.warning(self, "Editar Incidencia", "Seleccione una avería o incidencia para editar.")
            return

        dialog = IncidentDialog(
            parent=self,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            inventory_service=self.inventory_service,
            work_order_service=self.work_order_service,
            technician_service=self.technician_service,
            incident=inc
        )
        if dialog.exec():
            updated = dialog.get_incident()
            self.incident_service.save_incident(updated)

            if dialog.chk_update_eq_status.isChecked() and updated.equipment_id:
                self._sync_equipment_status(updated)

            self.refresh_data()
            self._update_incident_detail(updated)

    def _create_work_order_for_incident(self, guide_kind: str):
        if not self.work_order_service:
            QMessageBox.warning(self, "Error", "El servicio de órdenes de trabajo no está disponible.")
            return

        inc = self.get_selected_incident()
        if not inc:
            QMessageBox.warning(
                self, 
                "Crear Guía / Orden de Trabajo", 
                "Seleccione primero una avería o incidencia de la tabla para generar su guía correspondiente."
            )
            return

        equipments = self.equipment_service.get_all_equipment() if self.equipment_service else []
        
        if guide_kind == GuideKind.SERVICE.value:
            next_code = self.work_order_service.get_next_service_code()
            default_title = f"Atención Avería {inc.id}: {inc.title or inc.equipment_tag}"
        else:
            next_code = self.work_order_service.get_next_maintenance_code()
            default_title = f"Mantenimiento Correctivo Avería {inc.id}: {inc.title or inc.equipment_tag}"

        sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
        if sev_val == "CRITICA":
            prio = Priority.CRITICAL.value
        elif sev_val == "ALTA":
            prio = Priority.HIGH.value
        elif sev_val == "MEDIA":
            prio = Priority.MEDIUM.value
        else:
            prio = Priority.LOW.value

        from src.ui.dialogs.work_order_dialog import WorkOrderDialog
        dialog = WorkOrderDialog(
            parent=self,
            equipment_list=equipments,
            guide_kind=guide_kind,
            preassigned_id=next_code,
            incident_id=inc.id,
            preselected_equipment_id=inc.equipment_id,
            initial_title=default_title,
            initial_diagnosis=inc.diagnosis or inc.description or "",
            initial_technician=inc.technician or "",
            initial_priority=prio,
            inventory_service=self.inventory_service,
            client_service=self.client_service,
            technician_service=self.technician_service
        )

        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)

            inc.work_order_id = wo.id
            cur_st = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
            if cur_st in ["REPORTADA", "EN_DIAGNOSTICO"]:
                inc.status = IncidentStatus.EN_REPARACION
            self.incident_service.save_incident(inc)

            self.refresh_data()
            self._update_incident_detail(inc)
            guide_type_label = "Guía de Servicio Técnico (OTS)" if guide_kind == GuideKind.SERVICE.value else "Guía de Mantenimiento (OTM)"
            QMessageBox.information(
                self,
                "Guía Generada Exitosamente",
                f"Se ha creado la {guide_type_label} con código <b>{wo.id}</b> asociada a la avería <b>{inc.id}</b> y al equipo <b>{inc.equipment_tag}</b>."
            )

    def on_create_service_guide(self):
        self._create_work_order_for_incident(GuideKind.SERVICE.value)

    def on_create_maint_guide(self):
        self._create_work_order_for_incident(GuideKind.MAINTENANCE.value)

    def on_delete_incident(self):
        inc = self.get_selected_incident()
        if not inc:
            QMessageBox.warning(self, "Eliminar", "Seleccione una avería o incidencia para eliminar.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la incidencia '{inc.id}'?\n\n(Se moverá a la Papelera de Reciclaje)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.incident_service.delete_incident(inc.id)
            self.refresh_data()

    def _sync_equipment_status(self, incident):
        if self.incident_service and self.equipment_service:
            self.incident_service.sync_equipment_status_from_incident(incident, self.equipment_service)

    def on_export_csv(self):
        incidents = self.incident_service.get_all_incidents()
        if not incidents:
            QMessageBox.warning(self, "Exportar", "No hay incidencias registradas para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Historial de Averías",
            "Historial_Averias_Incidencias.csv",
            "Archivos CSV (*.csv)"
        )
        if not file_path:
            return

        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow([
                    "Código", "Fecha Reporte", "Equipo", "ID BMS", "Tipo / Especialidad",
                    "Severidad", "Estado", "Título", "Diagnóstico",
                    "Trabajos Realizados", "Técnico", "Repuestos Utilizados",
                    "Horas Hombre", "Costo Estimado", "Fecha Resolución", "Notas"
                ])
                for inc in incidents:
                    bms_val = getattr(inc, 'bms_id', '') or ""
                    if not bms_val and self.equipment_service and inc.equipment_id:
                        eq = self.equipment_service.get_equipment(inc.equipment_id)
                        if eq:
                            bms_val = getattr(eq, 'bms_id', '') or ""
                    writer.writerow([
                        inc.id,
                        format_chilean_date(inc.reported_date),
                        inc.equipment_tag,
                        bms_val or "N/A",
                        inc.type_display,
                        inc.severity_display,
                        inc.status_display,
                        inc.title,
                        inc.diagnosis,
                        inc.action_taken,
                        inc.technician,
                        ", ".join(inc.parts_used),
                        inc.labor_hours,
                        inc.cost_estimate,
                        format_chilean_date(inc.resolved_date) if inc.resolved_date else "",
                        inc.notes
                    ])

            QMessageBox.information(self, "Exportación Exitosa", f"El archivo se guardó correctamente en:\n\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el archivo:\n\n{e}")

    def _get_logo_path(self) -> str:
        from src.app.state_manager import StateManager
        return StateManager().get_logo_path()

    def on_export_pdf_dialog(self):
        if not self.export_service or not self.incident_service:
            QMessageBox.warning(self, "Exportar PDF", "Servicios requeridos no disponibles.")
            return

        selected_inc = self.get_selected_incident()
        from src.ui.dialogs.incident_pdf_dialog import IncidentPdfDialog
        dialog = IncidentPdfDialog(
            incident_service=self.incident_service,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            export_service=self.export_service,
            library_service=self.library_service,
            selected_incident=selected_inc,
            parent=self
        )
        dialog.exec()

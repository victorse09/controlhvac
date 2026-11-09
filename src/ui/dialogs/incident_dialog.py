from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QDateEdit, QMessageBox,
    QComboBox, QGroupBox, QScrollArea, QWidget, QDoubleSpinBox, QCheckBox,
    QListWidget, QListWidgetItem, QLabel, QCompleter, QFrame
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from datetime import datetime

from src.core.models.incident import Incident
from src.core.models.enums import (
    IncidentType, IncidentSeverity, IncidentStatus,
    INCIDENT_TYPE_LABELS, INCIDENT_SEVERITY_LABELS, INCIDENT_STATUS_LABELS,
    OPERATIONAL_STATUS_LABELS, GuideKind, Priority
)
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card

class IncidentDialog(QDialog):
    def __init__(
        self, 
        parent=None, 
        equipment_service=None, 
        client_service=None, 
        inventory_service=None, 
        work_order_service=None,
        technician_service=None,
        incident=None, 
        preselected_equipment_id=None, 
        read_only=None
    ):
        super().__init__(parent)
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.work_order_service = work_order_service
        self.technician_service = technician_service
        if self.technician_service is None and hasattr(parent, 'technician_service'):
            self.technician_service = parent.technician_service
        self.incident = incident
        self.preselected_equipment_id = preselected_equipment_id
        self.work_order_id = getattr(incident, 'work_order_id', '') if incident else ""
        
        # Start in read-only / view mode if opening existing incident
        self.is_read_only = (incident is not None) if read_only is None else read_only
        self.resize(740, 860)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Modern Top Header Banner
        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        hb_layout = QHBoxLayout(header_banner)
        hb_layout.setContentsMargins(14, 12, 14, 12)
        hb_layout.setSpacing(14)

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon("warning.svg", "#EF4444", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(3)
        inc_code = self.incident.id if self.incident else "Nueva Avería / Incidencia"
        self.lbl_banner_title = QLabel(f"Ficha de Avería e Incidencia Técnica  —  {inc_code}")
        self.lbl_banner_title.setObjectName("detailTitleLabel")
        self.lbl_banner_title.setStyleSheet("font-size: 15.5px; font-weight: 700; background: transparent;")
        self.lbl_banner_sub = QLabel("Diagnóstico técnico, trazabilidad de fallas, repuestos utilizados y vinculación con Órdenes de Trabajo")
        self.lbl_banner_sub.setObjectName("kvKeyLabel")
        self.lbl_banner_sub.setStyleSheet("font-size: 11.5px; background: transparent;")
        title_col.addWidget(self.lbl_banner_title)
        title_col.addWidget(self.lbl_banner_sub)
        hb_layout.addLayout(title_col, 1)

        # Status Pill
        st_box = QFrame()
        st_box.setObjectName("eqStatusBanner")
        st_l = QVBoxLayout(st_box)
        st_l.setContentsMargins(10, 5, 10, 5)
        st_l.setSpacing(1)
        lbl_st_cap = QLabel("ESTADO INCIDENCIA")
        lbl_st_cap.setObjectName("kvKeyLabel")
        lbl_st_cap.setStyleSheet("font-size: 9px; letter-spacing: 0.5px; background: transparent;")
        self.lbl_banner_status = QLabel("●  Reportada")
        self.lbl_banner_status.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 700; background: transparent;")
        st_l.addWidget(lbl_st_cap)
        st_l.addWidget(self.lbl_banner_status)
        hb_layout.addWidget(st_box)

        # Severity Pill
        sev_box = QFrame()
        sev_box.setObjectName("eqStatusBanner")
        sev_l = QVBoxLayout(sev_box)
        sev_l.setContentsMargins(10, 5, 10, 5)
        sev_l.setSpacing(1)
        lbl_sev_cap = QLabel("SEVERIDAD")
        lbl_sev_cap.setObjectName("kvKeyLabel")
        lbl_sev_cap.setStyleSheet("font-size: 9px; letter-spacing: 0.5px; background: transparent;")
        self.lbl_banner_severity = QLabel("●  Media")
        self.lbl_banner_severity.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: 700; background: transparent;")
        sev_l.addWidget(lbl_sev_cap)
        sev_l.addWidget(self.lbl_banner_severity)
        hb_layout.addWidget(sev_box)

        main_layout.addWidget(header_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self._setup_equipment_section()
        self._setup_details_section()
        self._setup_work_order_link_section()
        self._setup_actions_section()
        self._setup_materials_section()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Footer Bar
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)

        self.lbl_mode_badge = QLabel()
        self.lbl_mode_badge.setStyleSheet("font-size: 11px; font-weight: 700; background: transparent;")
        btn_layout.addWidget(self.lbl_mode_badge)
        btn_layout.addStretch()
        
        # View Mode Buttons
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setMinimumWidth(100)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)
        
        self.btn_edit_mode = QPushButton("  Editar Incidencia")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setMinimumWidth(145)
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))
        
        # Edit / New Mode Buttons
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumWidth(100)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        
        self.btn_save = QPushButton("  Guardar Incidencia")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setMinimumWidth(155)
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addWidget(footer_bar)

        if self.incident:
            self._load_data()
        elif self.preselected_equipment_id:
            self._preselect_equipment(self.preselected_equipment_id)

        self.combo_status.currentIndexChanged.connect(lambda _: self._refresh_header_banner())
        self.combo_severity.currentIndexChanged.connect(lambda _: self._refresh_header_banner())
        self.combo_equipment.currentIndexChanged.connect(lambda _: self._refresh_header_banner())
        self.edit_title.textChanged.connect(lambda _: self._refresh_header_banner())

        self.set_read_only(self.is_read_only)
        self._refresh_header_banner()

    def _refresh_header_banner(self):
        if not hasattr(self, 'lbl_banner_status'):
            return
        inc_code = self.incident.id if self.incident else "Nueva Avería"
        eq_txt = self.combo_equipment.currentText() if hasattr(self, 'combo_equipment') else ""
        self.lbl_banner_title.setText(f"{inc_code}  —  {eq_txt}" if eq_txt else f"Ficha de Avería  —  {inc_code}")

        sub_parts = []
        if hasattr(self, 'combo_client') and self.combo_client.currentText():
            sub_parts.append(f"Cliente: {self.combo_client.currentText()}")
        if hasattr(self, 'combo_site') and self.combo_site.currentText():
            sub_parts.append(f"Instalación: {self.combo_site.currentText()}")
        if hasattr(self, 'combo_type') and self.combo_type.currentText():
            sub_parts.append(f"Tipo: {self.combo_type.currentText()}")
        self.lbl_banner_sub.setText("   •   ".join(sub_parts) if sub_parts else "Diagnóstico técnico y seguimiento de averías")

        st_code = str(self.combo_status.currentData() or "")
        st_lbl = self.combo_status.currentText() or "Reportada"
        st_colors = {
            "REPORTADA": "#EF4444",
            "EN_DIAGNOSTICO": "#F59E0B",
            "EN_REPARACION": "#38BDF8",
            "ESPERANDO_REPUESTO": "#A855F7",
            "RESUELTA": "#10B981",
            "CERRADA": "#10B981",
        }
        st_col = st_colors.get(st_code, "#F59E0B")
        self.lbl_banner_status.setText(f"●  {st_lbl}")
        self.lbl_banner_status.setStyleSheet(f"color: {st_col}; font-size: 12px; font-weight: 700; background: transparent;")

        sev_code = str(self.combo_severity.currentData() or "")
        sev_lbl = self.combo_severity.currentText() or "Media"
        sev_colors = {
            "CRITICA": "#EF4444",
            "ALTA": "#F97316",
            "MEDIA": "#F59E0B",
            "BAJA": "#10B981",
        }
        sev_col = sev_colors.get(sev_code, "#F59E0B")
        self.lbl_banner_severity.setText(f"●  {sev_lbl}")
        self.lbl_banner_severity.setStyleSheet(f"color: {sev_col}; font-size: 12px; font-weight: 700; background: transparent;")

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        if self.incident:
            if read_only:
                self.setWindowTitle(f"Detalle de Incidencia - {self.incident.id}")
                if hasattr(self, 'lbl_mode_badge'):
                    self.lbl_mode_badge.setText("●  MODO LECTURA / CONSULTA")
                    self.lbl_mode_badge.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
            else:
                self.setWindowTitle(f"Editar Incidencia - {self.incident.id}")
                if hasattr(self, 'lbl_mode_badge'):
                    self.lbl_mode_badge.setText("●  MODO EDICIÓN ACTIVO")
                    self.lbl_mode_badge.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
        else:
            self.setWindowTitle("Registrar Avería / Observación")
            if hasattr(self, 'lbl_mode_badge'):
                self.lbl_mode_badge.setText("●  REGISTRO DE NUEVA AVERÍA")
                self.lbl_mode_badge.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")

        # Toggle Button Visibility
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Toggle Form Fields
        enabled = not read_only
        self.combo_client.setEnabled(enabled)
        self.combo_site.setEnabled(enabled)
        self.combo_equipment.setEnabled(enabled)
        self.edit_title.setReadOnly(read_only)
        self.combo_type.setEnabled(enabled)
        self.combo_severity.setEnabled(enabled)
        self.combo_status.setEnabled(enabled)
        self.date_reported.setEnabled(enabled)
        self.chk_has_resolved.setEnabled(enabled)
        self.date_resolved.setEnabled(enabled and self.chk_has_resolved.isChecked())
        self.edit_description.setReadOnly(read_only)
        self.edit_diagnosis.setReadOnly(read_only)
        self.edit_action.setReadOnly(read_only)
        self.edit_technician.setReadOnly(read_only)
        self.spin_hours.setEnabled(enabled)
        self.spin_cost.setEnabled(enabled)
        self.edit_parts.setReadOnly(read_only)
        if hasattr(self, 'list_inventory'):
            self.list_inventory.setEnabled(enabled)
        self.edit_notes.setReadOnly(read_only)
        self.chk_update_eq_status.setEnabled(enabled)

    def _on_cancel_clicked(self):
        if self.incident:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _setup_equipment_section(self):
        card, gb = _create_dialog_card("1. Equipo y Ubicación Afectada", "#38BDF8")
        fl = QFormLayout(gb)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.combo_client = QComboBox()
        self.combo_site = QComboBox()
        self.combo_equipment = QComboBox()

        self._populate_clients()
        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        self.combo_site.currentIndexChanged.connect(self._on_site_changed)

        fl.addRow("Cliente *:", self.combo_client)
        fl.addRow("Instalación *:", self.combo_site)
        fl.addRow("Equipo Afectado *:", self.combo_equipment)

        self.lbl_equipment_bms = QLineEdit()
        self.lbl_equipment_bms.setReadOnly(True)
        self.lbl_equipment_bms.setPlaceholderText("Sin ID BMS asignado")
        self.lbl_equipment_bms.setStyleSheet("QLineEdit { color: #38BDF8; font-weight: bold; }")
        fl.addRow("ID BMS:", self.lbl_equipment_bms)

        self.lbl_equipment_bms_status = QLineEdit()
        self.lbl_equipment_bms_status.setReadOnly(True)
        self.lbl_equipment_bms_status.setPlaceholderText("Estado BMS del equipo")
        self.lbl_equipment_bms_status.setStyleSheet("QLineEdit { font-weight: bold; }")
        fl.addRow("Estado BMS / Control:", self.lbl_equipment_bms_status)

        self.lbl_equipment_status = QLineEdit()
        self.lbl_equipment_status.setReadOnly(True)
        self.lbl_equipment_status.setPlaceholderText("Estado operativo del equipo")
        self.lbl_equipment_status.setStyleSheet("QLineEdit { font-weight: bold; }")
        fl.addRow("Estado Operativo Equipo:", self.lbl_equipment_status)

        self.txt_equipment_notes = QTextEdit()
        self.txt_equipment_notes.setReadOnly(True)
        self.txt_equipment_notes.setMaximumHeight(65)
        self.txt_equipment_notes.setPlaceholderText("Sin notas registradas en la ficha del equipo.")
        fl.addRow("Notas del Equipo:", self.txt_equipment_notes)
        self.combo_equipment.currentIndexChanged.connect(self._on_equipment_changed)

        self.layout.addWidget(card)

    def _setup_details_section(self):
        card, gb = _create_dialog_card("2. Clasificación y Diagnóstico", "#F59E0B")
        fl = QFormLayout(gb)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Ej: Fuga de refrigerante en serpentín y daño en contactor principal")
        fl.addRow("Título / Resumen *:", self.edit_title)

        self.combo_type = QComboBox()
        for itype, label in INCIDENT_TYPE_LABELS.items():
            self.combo_type.addItem(label, itype.value)
        fl.addRow("Tipo / Especialidad *:", self.combo_type)

        self.combo_severity = QComboBox()
        for sev, label in INCIDENT_SEVERITY_LABELS.items():
            self.combo_severity.addItem(label, sev.value)
        fl.addRow("Severidad *:", self.combo_severity)

        self.combo_status = QComboBox()
        for st, label in INCIDENT_STATUS_LABELS.items():
            self.combo_status.addItem(label, st.value)
        fl.addRow("Estado Actual *:", self.combo_status)

        dates_row = QHBoxLayout()
        self.date_reported = QDateEdit()
        self.date_reported.setCalendarPopup(True)
        self.date_reported.setDate(QDate.currentDate())
        
        self.date_resolved = QDateEdit()
        self.date_resolved.setCalendarPopup(True)
        self.date_resolved.setDate(QDate.currentDate())
        self.chk_has_resolved = QCheckBox("Resuelto en fecha:")
        self.date_resolved.setEnabled(False)
        self.chk_has_resolved.toggled.connect(self.date_resolved.setEnabled)

        dates_row.addWidget(QLabel("Reportado:"))
        dates_row.addWidget(self.date_reported)
        dates_row.addSpacing(15)
        dates_row.addWidget(self.chk_has_resolved)
        dates_row.addWidget(self.date_resolved)
        fl.addRow("Fechas:", dates_row)

        self.edit_description = QTextEdit()
        self.edit_description.setMaximumHeight(70)
        self.edit_description.setPlaceholderText("Descripción detallada de la falla o anomalía detectada...")
        fl.addRow("Descripción de Falla:", self.edit_description)

        self.edit_diagnosis = QTextEdit()
        self.edit_diagnosis.setMaximumHeight(70)
        self.edit_diagnosis.setPlaceholderText("Causa raíz técnica (ej: sobrecorriente por rodamiento trancado, vibración que fisuró tubería)...")
        fl.addRow("Diagnóstico Técnico:", self.edit_diagnosis)

        self.layout.addWidget(card)

    def _setup_work_order_link_section(self):
        self.gb_wo, wo_body = _create_dialog_card("3. Orden de Trabajo / Guía de Atención", "#0EA5E9")
        wo_layout = QVBoxLayout(wo_body)
        wo_layout.setSpacing(10)
        wo_layout.setContentsMargins(16, 14, 16, 16)

        info_layout = QHBoxLayout()
        self.lbl_wo_status = QLabel("No se ha generado una Orden de Trabajo / Guía para esta avería.")
        self.lbl_wo_status.setObjectName("kvKeyLabel")
        info_layout.addWidget(self.lbl_wo_status, 1)

        self.btn_view_wo = QPushButton("Ver Guía / OT")
        self.btn_view_wo.setIcon(IconManager.get_icon("edit.svg", "#38BDF8", 16))
        self.btn_view_wo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_view_wo.setVisible(False)
        self.btn_view_wo.clicked.connect(self._on_view_linked_work_order)
        info_layout.addWidget(self.btn_view_wo)

        wo_layout.addLayout(info_layout)

        # Buttons to create OTS / OTM if not linked
        self.create_wo_box = QWidget()
        create_layout = QHBoxLayout(self.create_wo_box)
        create_layout.setContentsMargins(0, 0, 0, 0)
        create_layout.setSpacing(10)

        self.btn_create_ots = QPushButton(" + Crear Guía de Servicio (OTS)")
        self.btn_create_ots.setStyleSheet("background-color: #0284C7; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        self.btn_create_ots.setIcon(IconManager.get_icon("tools.svg", "#FFFFFF", 16))
        self.btn_create_ots.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_create_ots.clicked.connect(lambda: self._on_create_linked_wo(GuideKind.SERVICE.value))

        self.btn_create_otm = QPushButton(" + Crear Guía Mantenimiento (OTM)")
        self.btn_create_otm.setStyleSheet("background-color: #059669; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        self.btn_create_otm.setIcon(IconManager.get_icon("calendar.svg", "#FFFFFF", 16))
        self.btn_create_otm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_create_otm.clicked.connect(lambda: self._on_create_linked_wo(GuideKind.MAINTENANCE.value))

        create_layout.addWidget(self.btn_create_ots)
        create_layout.addWidget(self.btn_create_otm)
        create_layout.addStretch()

        wo_layout.addWidget(self.create_wo_box)
        self.layout.addWidget(self.gb_wo)

    def _update_wo_section_ui(self):
        wo_id = self.work_order_id or (getattr(self.incident, 'work_order_id', '') if self.incident else "")
        if wo_id:
            self.lbl_wo_status.setText(f"Orden de Trabajo Vinculada: &nbsp;<span style='color: #38BDF8; font-weight: bold; font-size: 13px;'>{wo_id}</span>")
            self.btn_view_wo.setVisible(True)
            self.create_wo_box.setVisible(False)
        else:
            self.lbl_wo_status.setText("No se ha generado una Orden de Trabajo / Guía para esta avería.")
            self.btn_view_wo.setVisible(False)
            self.create_wo_box.setVisible(self.incident is not None and self.work_order_service is not None)

    def _on_view_linked_work_order(self):
        wo_id = self.work_order_id or (getattr(self.incident, 'work_order_id', '') if self.incident else "")
        if not wo_id or not self.work_order_service:
            return
        wo = self.work_order_service.get_work_order(wo_id)
        if not wo:
            QMessageBox.warning(self, "Orden no encontrada", f"No se encontró la orden de trabajo {wo_id}.")
            return
        from src.ui.dialogs.work_order_dialog import WorkOrderDialog
        equipments = self.equipment_service.get_all_equipment() if self.equipment_service else []
        dialog = WorkOrderDialog(
            parent=self,
            equipment_list=equipments,
            work_order=wo,
            inventory_service=self.inventory_service,
            client_service=self.client_service,
            read_only=True
        )
        if dialog.exec():
            updated = dialog.get_work_order()
            self.work_order_service.save_work_order(updated)

    def _on_create_linked_wo(self, guide_kind: str):
        if not self.work_order_service:
            QMessageBox.warning(self, "Error", "Servicio de órdenes de trabajo no disponible.")
            return

        eq_id = self.combo_equipment.currentData() or (self.incident.equipment_id if self.incident else "")
        eq_tag = self.lbl_equipment_bms.text() or ""
        inc_id = self.incident.id if self.incident else ""

        if guide_kind == GuideKind.SERVICE.value:
            next_code = self.work_order_service.get_next_service_code()
            default_title = f"Atención Avería {inc_id}: {self.edit_title.text().strip() or eq_tag}"
        else:
            next_code = self.work_order_service.get_next_maintenance_code()
            default_title = f"Mantenimiento Correctivo Avería {inc_id}: {self.edit_title.text().strip() or eq_tag}"

        sev_val = self.combo_severity.currentData()
        if sev_val == "CRITICA": prio = Priority.CRITICAL.value
        elif sev_val == "ALTA": prio = Priority.HIGH.value
        elif sev_val == "MEDIA": prio = Priority.MEDIUM.value
        else: prio = Priority.LOW.value

        from src.ui.dialogs.work_order_dialog import WorkOrderDialog
        equipments = self.equipment_service.get_all_equipment() if self.equipment_service else []
        dialog = WorkOrderDialog(
            parent=self,
            equipment_list=equipments,
            guide_kind=guide_kind,
            preassigned_id=next_code,
            incident_id=inc_id,
            preselected_equipment_id=eq_id,
            initial_title=default_title,
            initial_diagnosis=self.edit_diagnosis.toPlainText().strip() or self.edit_description.toPlainText().strip(),
            initial_technician=self.edit_technician.text().strip(),
            initial_priority=prio,
            inventory_service=self.inventory_service,
            client_service=self.client_service,
            technician_service=self.technician_service
        )
        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)
            self.work_order_id = wo.id
            if self.incident:
                self.incident.work_order_id = wo.id
                st_cur = self.combo_status.currentData()
                if st_cur in ["REPORTADA", "EN_DIAGNOSTICO"]:
                    idx = self.combo_status.findData(IncidentStatus.EN_REPARACION.value)
                    if idx >= 0: self.combo_status.setCurrentIndex(idx)
                    self.incident.status = IncidentStatus.EN_REPARACION
                if hasattr(self.parent(), 'incident_service') and self.parent().incident_service:
                    self.parent().incident_service.save_incident(self.incident)
            self._update_wo_section_ui()
            guide_lbl = "Guía de Servicio (OTS)" if guide_kind == GuideKind.SERVICE.value else "Guía de Mantenimiento (OTM)"
            QMessageBox.information(self, "Guía Creada", f"Se creó exitosamente la {guide_lbl} <b>{wo.id}</b>.")

    def _setup_actions_section(self):
        card, gb = _create_dialog_card("4. Trabajos Realizados y Responsable", "#10B981")
        fl = QFormLayout(gb)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.edit_action = QTextEdit()
        self.edit_action.setMaximumHeight(75)
        self.edit_action.setPlaceholderText("Detalle de las reparaciones ejecutadas (ej: Soldadura con varilla de plata 15%, vacío a 450 micrones, cambio de contactor Schneider 25A y prueba operativa)...")
        fl.addRow("Trabajos Ejecutados:", self.edit_action)

        self.edit_technician = QLineEdit()
        self.edit_technician.setPlaceholderText("Técnico o especialista a cargo")
        if self.technician_service:
            tech_names = self.technician_service.get_technician_names()
            if tech_names:
                completer = QCompleter(tech_names, self)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.edit_technician.setCompleter(completer)
        fl.addRow("Técnico Responsable:", self.edit_technician)

        hours_cost_row = QHBoxLayout()
        self.spin_hours = QDoubleSpinBox()
        self.spin_hours.setRange(0, 1000)
        self.spin_hours.setDecimals(1)
        self.spin_hours.setSuffix(" hrs")
        
        self.spin_cost = QDoubleSpinBox()
        self.spin_cost.setRange(0, 100000000)
        self.spin_cost.setDecimals(0)
        self.spin_cost.setPrefix("$ ")

        hours_cost_row.addWidget(QLabel("Horas Hombre:"))
        hours_cost_row.addWidget(self.spin_hours)
        hours_cost_row.addSpacing(20)
        hours_cost_row.addWidget(QLabel("Costo Estimado:"))
        hours_cost_row.addWidget(self.spin_cost)
        fl.addRow("Tiempos y Costos:", hours_cost_row)

        self.layout.addWidget(card)

    def _setup_materials_section(self):
        card, gb = _create_dialog_card("5. Repuestos / Materiales Empleados y Notas", "#8B5CF6")
        fl = QFormLayout(gb)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.edit_parts = QLineEdit()
        self.edit_parts.setPlaceholderText("Ej: Contactor LC1D25, Relé térmico LRD33, Varilla plata 15%, Filtro deshidratador")
        fl.addRow("Repuestos Utilizados:", self.edit_parts)

        if self.inventory_service:
            self.list_inventory = QListWidget()
            self.list_inventory.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            self.list_inventory.setMaximumHeight(90)
            try:
                for p in self.inventory_service.get_all_spare_parts():
                    unit = getattr(p, 'unit', 'unid')
                    item = QListWidgetItem(f"{p.name} [{p.part_number or 'Sin cód.'}] (Stock: {p.quantity} {unit})")
                    item.setData(Qt.ItemDataRole.UserRole, p.name)
                    self.list_inventory.addItem(item)
            except Exception:
                pass
            fl.addRow("Inventario Disponible:", self.list_inventory)

        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(65)
        self.edit_notes.setPlaceholderText("Recomendaciones futuras, notas de garantía, estado post-reparación...")
        fl.addRow("Notas / Observaciones:", self.edit_notes)

        # Sync equipment status checkbox
        self.chk_update_eq_status = QCheckBox("Actualizar estado del equipo automáticamente al guardar")
        self.chk_update_eq_status.setChecked(True)
        fl.addRow("", self.chk_update_eq_status)

        self.layout.addWidget(card)

    def _populate_clients(self):
        self.combo_client.clear()
        if not self.client_service:
            return
        clients = self.client_service.get_all_clients()
        for c in clients:
            cname = getattr(c, 'company_name', '') or getattr(c, 'name', '')
            self.combo_client.addItem(cname, c.id)
        self._on_client_changed()

    def _on_client_changed(self):
        self.combo_site.clear()
        cid = self.combo_client.currentData()
        if cid and self.client_service:
            sites = self.client_service.get_sites_for_client(cid)
            for s in sites:
                self.combo_site.addItem(s.name, s.id)
        self._on_site_changed()

    def _on_site_changed(self):
        self.combo_equipment.clear()
        site_id = self.combo_site.currentData()
        if site_id and self.equipment_service:
            eqs = self.equipment_service.get_equipment_for_site(site_id)
            for e in eqs:
                stype_str = e.system_type.value if hasattr(e.system_type, 'value') else str(e.system_type)
                bms = getattr(e, 'bms_id', '') or ""
                floor = getattr(e, 'floor_area', '') or ""
                
                parts = []
                if bms:
                    parts.append(str(bms))
                parts.append(f"({stype_str})")
                if floor:
                    parts.append(f"[{floor}]")
                parts.append(e.tag)
                
                label = " ".join(parts)
                self.combo_equipment.addItem(label, e.id)
        self._on_equipment_changed()

    def _on_equipment_changed(self):
        eq_id = self.combo_equipment.currentData()
        if not eq_id or not self.equipment_service:
            if hasattr(self, 'lbl_equipment_bms'):
                self.lbl_equipment_bms.setText("")
            if hasattr(self, 'lbl_equipment_bms_status'):
                self.lbl_equipment_bms_status.setText("")
            if hasattr(self, 'lbl_equipment_status'):
                self.lbl_equipment_status.setText("")
            if hasattr(self, 'txt_equipment_notes'):
                self.txt_equipment_notes.setPlainText("Sin notas registradas en la ficha del equipo.")
            return

        eq = self.equipment_service.get_equipment(eq_id)
        if not eq:
            if hasattr(self, 'lbl_equipment_bms'):
                self.lbl_equipment_bms.setText("")
            if hasattr(self, 'lbl_equipment_bms_status'):
                self.lbl_equipment_bms_status.setText("")
            if hasattr(self, 'lbl_equipment_status'):
                self.lbl_equipment_status.setText("")
            if hasattr(self, 'txt_equipment_notes'):
                self.txt_equipment_notes.setPlainText("Sin notas registradas en la ficha del equipo.")
            return

        bms_val = getattr(eq, 'bms_id', '') or ""
        if hasattr(self, 'lbl_equipment_bms'):
            self.lbl_equipment_bms.setText(bms_val)

        bms_st_val = getattr(eq, 'bms_status', 'Operativo') or 'Operativo'
        if hasattr(self, 'lbl_equipment_bms_status'):
            self.lbl_equipment_bms_status.setText(bms_st_val)

        eq_st_raw = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
        eq_st_label = OPERATIONAL_STATUS_LABELS.get(eq.status, eq_st_raw)
        if hasattr(self, 'lbl_equipment_status'):
            self.lbl_equipment_status.setText(eq_st_label)

        notes = (getattr(eq, 'notes', '') or '').strip()
        if hasattr(self, 'txt_equipment_notes'):
            self.txt_equipment_notes.setPlainText(notes if notes else "Sin notas registradas en la ficha del equipo.")

        # If registering a new incident and fields are empty, prefill from equipment notes
        if not self.incident and notes:
            if not self.edit_diagnosis.toPlainText().strip():
                self.edit_diagnosis.setPlainText(notes)
            if not self.edit_notes.toPlainText().strip():
                self.edit_notes.setPlainText(notes)
            if not self.edit_description.toPlainText().strip():
                status_str = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
                self.edit_description.setPlainText(f"Equipo {eq.tag} [{status_str}]. Notas de la ficha: {notes}")

    def _preselect_equipment(self, equipment_id: str):
        if not self.equipment_service:
            return
        eq = self.equipment_service.get_equipment(equipment_id)
        if not eq:
            return

        if eq.client_id:
            idx = self.combo_client.findData(eq.client_id)
            if idx >= 0: self.combo_client.setCurrentIndex(idx)

        if eq.site_id:
            idx = self.combo_site.findData(eq.site_id)
            if idx >= 0: self.combo_site.setCurrentIndex(idx)

        idx = self.combo_equipment.findData(eq.id)
        if idx >= 0:
            self.combo_equipment.setCurrentIndex(idx)
        self._on_equipment_changed()

    def _load_data(self):
        inc = self.incident
        if not inc:
            return

        # Select equipment
        if inc.client_id:
            idx = self.combo_client.findData(inc.client_id)
            if idx >= 0: self.combo_client.setCurrentIndex(idx)
        if inc.site_id:
            idx = self.combo_site.findData(inc.site_id)
            if idx >= 0: self.combo_site.setCurrentIndex(idx)
        if inc.equipment_id:
            idx = self.combo_equipment.findData(inc.equipment_id)
            if idx >= 0: self.combo_equipment.setCurrentIndex(idx)
        self._on_equipment_changed()

        self.edit_title.setText(inc.title)

        t_val = inc.incident_type.value if hasattr(inc.incident_type, 'value') else str(inc.incident_type)
        idx = self.combo_type.findData(t_val)
        if idx >= 0: self.combo_type.setCurrentIndex(idx)

        s_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
        idx = self.combo_severity.findData(s_val)
        if idx >= 0: self.combo_severity.setCurrentIndex(idx)

        st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
        idx = self.combo_status.findData(st_val)
        if idx >= 0: self.combo_status.setCurrentIndex(idx)

        if inc.reported_date:
            try: self.date_reported.setDate(QDate.fromString(inc.reported_date[:10], Qt.DateFormat.ISODate))
            except: pass

        if inc.resolved_date:
            self.chk_has_resolved.setChecked(True)
            try: self.date_resolved.setDate(QDate.fromString(inc.resolved_date[:10], Qt.DateFormat.ISODate))
            except: pass

        self.edit_description.setPlainText(inc.description)
        self.edit_diagnosis.setPlainText(inc.diagnosis)
        self.edit_action.setPlainText(inc.action_taken)
        self.edit_technician.setText(inc.technician)
        self.spin_hours.setValue(float(inc.labor_hours or 0.0))
        self.spin_cost.setValue(float(inc.cost_estimate or 0.0))
        self.edit_notes.setPlainText(inc.notes)

        # Parts
        sp_list = getattr(inc, 'parts_used', []) or []
        self.edit_parts.setText(", ".join(sp_list))

        if hasattr(self, 'list_inventory'):
            for i in range(self.list_inventory.count()):
                item = self.list_inventory.item(i)
                pname = item.data(Qt.ItemDataRole.UserRole)
                if pname in sp_list:
                    item.setSelected(True)

        self._update_wo_section_ui()

    def validate_and_accept(self):
        if not self.combo_equipment.currentData():
            QMessageBox.warning(self, "Error", "Debe seleccionar el equipo afectado.")
            return

        if not self.edit_title.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar un título o resumen de la incidencia.")
            return

        self.accept()

    def get_incident(self) -> Incident:
        eq_id = self.combo_equipment.currentData() or ""
        eq_tag = ""
        if self.equipment_service and eq_id:
            eq = self.equipment_service.get_equipment(eq_id)
            if eq:
                eq_tag = eq.tag

        parts = []
        raw_parts = self.edit_parts.text().strip()
        if raw_parts:
            for p in raw_parts.split(','):
                pt = p.strip()
                if pt and pt not in parts:
                    parts.append(pt)

        if hasattr(self, 'list_inventory'):
            for item in self.list_inventory.selectedItems():
                pname = item.data(Qt.ItemDataRole.UserRole)
                if pname and pname not in parts:
                    parts.append(pname)

        resolved_dt = ""
        if self.chk_has_resolved.isChecked():
            resolved_dt = self.date_resolved.date().toString(Qt.DateFormat.ISODate)

        inc_id = self.incident.id if self.incident else ""
        wo_id = self.work_order_id or (getattr(self.incident, 'work_order_id', '') if self.incident else "")

        return Incident(
            id=inc_id,
            client_id=self.combo_client.currentData() or "",
            site_id=self.combo_site.currentData() or "",
            equipment_id=eq_id,
            equipment_tag=eq_tag,
            title=self.edit_title.text().strip(),
            incident_type=self.combo_type.currentData(),
            severity=self.combo_severity.currentData(),
            status=self.combo_status.currentData(),
            reported_date=self.date_reported.date().toString(Qt.DateFormat.ISODate),
            resolved_date=resolved_dt,
            description=self.edit_description.toPlainText().strip(),
            diagnosis=self.edit_diagnosis.toPlainText().strip(),
            action_taken=self.edit_action.toPlainText().strip(),
            technician=self.edit_technician.text().strip(),
            parts_used=parts,
            labor_hours=self.spin_hours.value(),
            cost_estimate=self.spin_cost.value(),
            notes=self.edit_notes.toPlainText().strip(),
            work_order_id=wo_id
        )

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QRadioButton,
    QButtonGroup, QLineEdit, QFileDialog, QMessageBox, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.ui.icon_manager import IconManager
from src.core.models.enums import (
    INCIDENT_SEVERITY_LABELS, INCIDENT_STATUS_LABELS,
    IncidentSeverity, IncidentStatus
)
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class IncidentPdfDialog(QDialog):
    """Dialog to configure and export customized incidents and faults PDF reports."""

    def __init__(
        self,
        incident_service,
        equipment_service,
        client_service,
        export_service,
        library_service=None,
        selected_incident=None,
        parent=None
    ):
        super().__init__(parent)
        self.incident_service = incident_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.export_service = export_service
        self.library_service = library_service
        if not self.library_service and hasattr(parent, 'library_service'):
            self.library_service = parent.library_service
        self.selected_incident = selected_incident

        self.setWindowTitle("Generar Reportes y Listados PDF de Averías")
        self.resize(880, 500)
        self.setMinimumSize(800, 450)
        self.setModal(True)

        self.all_incidents = self.incident_service.get_all_incidents() if self.incident_service else []
        self.all_equipment = self.equipment_service.get_all_equipment() if self.equipment_service else []
        self.filtered_incidents = []
        self.eq_map = {eq.id: eq for eq in self.all_equipment}

        self.setup_ui()
        self._on_criteria_changed(0)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # Header Title & Info
        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        header_layout = QHBoxLayout(header_banner)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(14)

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_icon = QLabel()
        header_icon.setPixmap(IconManager.get_icon("pdf.svg", "#EF4444", 22).pixmap(22, 22))
        header_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(header_icon)
        header_layout.addWidget(icon_badge)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        lbl_h = QLabel("Exportar Listados y Reportes de Averías a PDF")
        lbl_h.setObjectName("detailTitleLabel")
        lbl_h.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        lbl_sub = QLabel("Seleccione la modalidad o filtro para generar el documento PDF con formato oficial:")
        lbl_sub.setObjectName("kvKeyLabel")
        header_text_layout.addWidget(lbl_h)
        header_text_layout.addWidget(lbl_sub)
        header_layout.addLayout(header_text_layout, 1)
        main_layout.addWidget(header_banner)

        # 2-Column Body Layout
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(12)

        # Left Column: 1. Criteria Group
        gb_criteria, criteria_body = _create_dialog_card("1. Alcance y Modalidad del Listado", "#EF4444")
        criteria_layout = QVBoxLayout(criteria_body)
        criteria_layout.setContentsMargins(14, 12, 14, 12)
        criteria_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)

        self.rb_by_floor = QRadioButton("📑 Listado separado por Piso / Área (1 pág/piso)")
        self.rb_all = QRadioButton("📄 Listado General Consolidado de Averías")
        self.rb_faulty_eq = QRadioButton("🚨 Listado Oficial de Equipos en Falla / Avería")
        self.rb_bms_issues = QRadioButton("🖥️ Informe de Problemas BMS / Sistema de Control")
        self.rb_client = QRadioButton("🏢 Listado de Averías por Cliente")
        self.rb_site = QRadioButton("📍 Listado de Averías por Instalación / Sede")
        self.rb_floor = QRadioButton("🚪 Listado de Averías de un Piso / Área específico")
        self.rb_severity = QRadioButton("⚠️ Listado por Severidad (Crítica, Alta, etc.)")
        self.rb_status = QRadioButton("🔄 Listado por Estado (Reportada, En Rep., etc.)")
        
        self.rb_single = QRadioButton("📋 Ficha / Informe Individual de Avería")
        if self.selected_incident:
            self.rb_single.setText(f"📋 Ficha Individual: {self.selected_incident.id}")
        else:
            self.rb_single.setEnabled(False)

        self.rb_by_floor.setChecked(True)

        radios = [
            self.rb_by_floor, self.rb_all, self.rb_faulty_eq, self.rb_bms_issues,
            self.rb_client, self.rb_site, self.rb_floor,
            self.rb_severity, self.rb_status, self.rb_single
        ]

        for idx, rb in enumerate(radios):
            self.btn_group.addButton(rb, idx)
            criteria_layout.addWidget(rb)

        self.btn_group.idClicked.connect(self._on_criteria_changed)
        cols_layout.addWidget(gb_criteria, 1)

        # Right Column: Filter params + Document customization + Info box
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        # 2. Filter Parameters Form
        self.gb_params, params_body = _create_dialog_card("2. Parámetros del Filtro Seleccionado", "#F59E0B")
        self.params_layout = QFormLayout(params_body)
        self.params_layout.setContentsMargins(14, 12, 14, 12)
        self.params_layout.setSpacing(6)

        # Client & Site combos
        self.combo_client = QComboBox()
        self.combo_site = QComboBox()
        self.params_layout.addRow("Cliente / Empresa:", self.combo_client)
        self.params_layout.addRow("Instalación / Sede:", self.combo_site)

        # Floor combo
        self.combo_floor = QComboBox()
        self.params_layout.addRow("Piso / Nivel:", self.combo_floor)

        # Severity combo
        self.combo_severity = QComboBox()
        for sev, label in INCIDENT_SEVERITY_LABELS.items():
            val = sev.value if hasattr(sev, 'value') else str(sev)
            self.combo_severity.addItem(label, val)
        self.params_layout.addRow("Severidad:", self.combo_severity)

        # Status combo
        self.combo_status = QComboBox()
        for st, label in INCIDENT_STATUS_LABELS.items():
            val = st.value if hasattr(st, 'value') else str(st)
            self.combo_status.addItem(label, val)
        self.params_layout.addRow("Estado Avería:", self.combo_status)

        # Only active check
        self.chk_only_open = QCheckBox("Excluir averías ya resueltas (Sólo activas)")
        self.chk_only_open.setChecked(False)
        self.chk_only_open.stateChanged.connect(self._update_filter_selection)
        self.params_layout.addRow("", self.chk_only_open)

        # Floor plan image check
        self.chk_include_floor_plan = QCheckBox("🗺️ Incluir plano/imagen del piso si existe en Librería")
        self.chk_include_floor_plan.setChecked(True)
        self.params_layout.addRow("", self.chk_include_floor_plan)

        right_col.addWidget(self.gb_params)

        # 3. Document Customization
        gb_doc, doc_body = _create_dialog_card("3. Datos del Documento", "#38BDF8")
        doc_layout = QFormLayout(doc_body)
        doc_layout.setContentsMargins(14, 12, 14, 12)
        doc_layout.setSpacing(6)

        self.txt_title = QLineEdit("Listado de Averías por Piso / Área")
        self.txt_subtitle = QLineEdit("ControlHVAC CMMS - Gestión y Control de Averías")
        doc_layout.addRow("Título del PDF:", self.txt_title)
        doc_layout.addRow("Subtítulo:", self.txt_subtitle)

        right_col.addWidget(gb_doc)

        # Count indicator box
        self.lbl_count_info = QLabel("Se incluirán 0 averías en el reporte PDF.")
        self.lbl_count_info.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px; padding: 6px 10px; border-radius: 5px; border: 1px solid #38BDF8;")
        right_col.addWidget(self.lbl_count_info)

        cols_layout.addLayout(right_col, 1)
        main_layout.addLayout(cols_layout, 1)

        # Action Buttons
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_generate = QPushButton("Generar Documento PDF")
        self.btn_generate.setObjectName("primaryButton")
        self.btn_generate.setIcon(IconManager.get_icon("pdf.svg", "#000000", 16))
        self.btn_generate.clicked.connect(self._generate_pdf)
        btn_layout.addWidget(self.btn_generate)

        main_layout.addWidget(footer_bar)

        # Populate
        self._populate_clients()
        self._populate_floors()

        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        self.combo_site.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_floor.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_severity.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_status.currentIndexChanged.connect(self._update_filter_selection)

    def _populate_clients(self):
        self.combo_client.blockSignals(True)
        self.combo_client.clear()
        self.combo_client.addItem("Todos los Clientes / Instalaciones", "")
        if self.client_service:
            clients = self.client_service.get_all_clients()
            for c in clients:
                self.combo_client.addItem(c.company_name, c.id)
        self.combo_client.blockSignals(False)
        self._on_client_changed()

    def _on_client_changed(self):
        self.combo_site.blockSignals(True)
        self.combo_site.clear()
        self.combo_site.addItem("Todas las Instalaciones", "")
        cid = self.combo_client.currentData()
        if cid and self.client_service:
            sites = self.client_service.get_sites_for_client(cid)
            for s in sites:
                self.combo_site.addItem(s.name, s.id)
        self.combo_site.blockSignals(False)
        self._update_filter_selection()

    def _populate_floors(self):
        self.combo_floor.blockSignals(True)
        self.combo_floor.clear()
        floors = set()
        for eq in self.all_equipment:
            fl = (getattr(eq, 'floor_area', '') or '').strip()
            if fl:
                floors.add(fl)
        sorted_floors = sorted(list(floors))
        for f in sorted_floors:
            self.combo_floor.addItem(f, f)
        if not sorted_floors:
            self.combo_floor.addItem("Piso 1", "Piso 1")
        self.combo_floor.blockSignals(False)

    def _on_criteria_changed(self, _id):
        is_by_floor = self.rb_by_floor.isChecked()
        is_client = self.rb_client.isChecked()
        is_site = self.rb_site.isChecked()
        is_floor = self.rb_floor.isChecked()
        is_sev = self.rb_severity.isChecked()
        is_status = self.rb_status.isChecked()
        is_faulty = self.rb_faulty_eq.isChecked()
        is_bms = self.rb_bms_issues.isChecked()
        is_single = self.rb_single.isChecked()

        self.combo_client.setEnabled(is_by_floor or is_client or is_site)
        self.combo_site.setEnabled(is_by_floor or is_site)
        self.combo_floor.setEnabled(is_floor)
        self.combo_severity.setEnabled(is_sev)
        self.combo_status.setEnabled(is_status)
        self.chk_only_open.setEnabled(not is_single and not is_status)
        self.chk_include_floor_plan.setVisible(is_by_floor)

        self._update_filter_selection()

    def _update_filter_selection(self):
        # Base list
        base_incidents = list(self.all_incidents)
        if self.chk_only_open.isChecked() and not self.rb_status.isChecked() and not self.rb_single.isChecked():
            base_incidents = [
                i for i in base_incidents 
                if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"
            ]

        if self.rb_by_floor.isChecked():
            cid = self.combo_client.currentData()
            sid = self.combo_site.currentData()
            if cid:
                base_incidents = [i for i in base_incidents if i.client_id == cid]
            if sid:
                base_incidents = [i for i in base_incidents if i.site_id == sid]
            self.filtered_incidents = base_incidents

            floors_found = set()
            for inc in self.filtered_incidents:
                eq = self.eq_map.get(inc.equipment_id)
                fl = (getattr(eq, 'floor_area', '') or '').strip() if eq else ""
                floors_found.add(fl or "Sin Piso / Área")

            c_name = self.combo_client.currentText() if cid else ""
            s_name = self.combo_site.currentText() if sid else ""
            if c_name and s_name:
                self.txt_title.setText(f"Listado de Averías por Pisos - {s_name}")
            elif c_name:
                self.txt_title.setText(f"Listado de Averías por Pisos - {c_name}")
            else:
                self.txt_title.setText("Listado de Averías por Piso / Área")

            scope_desc = f"{len(floors_found)} pisos/áreas detectadas (1 página por piso)"

        elif self.rb_all.isChecked():
            self.filtered_incidents = list(base_incidents)
            self.txt_title.setText("Listado General de Averías e Incidencias")
            scope_desc = "Todas las Averías"

        elif self.rb_faulty_eq.isChecked():
            self.filtered_incidents = list(base_incidents)
            self.txt_title.setText("Listado Oficial de Equipos en Avería")
            scope_desc = "Equipos en Avería / Falla"

        elif self.rb_bms_issues.isChecked():
            self.filtered_incidents = list(base_incidents)
            self.txt_title.setText("Listado de Equipos con Problemas BMS / Control")
            scope_desc = "Problemas de Control / BMS"

        elif self.rb_client.isChecked():
            cid = self.combo_client.currentData()
            c_name = self.combo_client.currentText()
            if cid:
                self.filtered_incidents = [i for i in base_incidents if i.client_id == cid]
                self.txt_title.setText(f"Listado de Averías - {c_name}")
                scope_desc = f"Cliente: {c_name}"
            else:
                self.filtered_incidents = list(base_incidents)
                self.txt_title.setText("Listado de Averías - Todos los Clientes")
                scope_desc = "Todos los Clientes"

        elif self.rb_site.isChecked():
            cid = self.combo_client.currentData()
            sid = self.combo_site.currentData()
            s_name = self.combo_site.currentText()
            c_name = self.combo_client.currentText()
            base = base_incidents
            if cid:
                base = [i for i in base if i.client_id == cid]
            if sid:
                base = [i for i in base if i.site_id == sid]
            self.filtered_incidents = base
            self.txt_title.setText(f"Listado de Averías - {s_name}")
            scope_desc = f"Instalación: {s_name} ({c_name})"

        elif self.rb_floor.isChecked():
            fl = self.combo_floor.currentData()
            res = []
            for inc in base_incidents:
                eq = self.eq_map.get(inc.equipment_id)
                if eq and (getattr(eq, 'floor_area', '') or '').strip() == fl:
                    res.append(inc)
            self.filtered_incidents = res
            self.txt_title.setText(f"Listado de Averías - {fl}")
            scope_desc = f"Piso / Nivel: {fl}"

        elif self.rb_severity.isChecked():
            sev_val = self.combo_severity.currentData()
            sev_label = self.combo_severity.currentText()
            self.filtered_incidents = [
                i for i in base_incidents
                if (i.severity.value if hasattr(i.severity, 'value') else str(i.severity)) == sev_val
            ]
            self.txt_title.setText(f"Listado de Averías con Severidad: {sev_label}")
            scope_desc = f"Severidad: {sev_label}"

        elif self.rb_status.isChecked():
            st_val = self.combo_status.currentData()
            st_label = self.combo_status.currentText()
            self.filtered_incidents = [
                i for i in self.all_incidents
                if (i.status.value if hasattr(i.status, 'value') else str(i.status)) == st_val
            ]
            self.txt_title.setText(f"Listado de Averías en Estado: {st_label}")
            scope_desc = f"Estado: {st_label}"

        elif self.rb_single.isChecked():
            self.filtered_incidents = [self.selected_incident] if self.selected_incident else []
            if self.selected_incident:
                self.txt_title.setText(f"Ficha de Avería: {self.selected_incident.id}")
                scope_desc = f"Avería individual {self.selected_incident.id}"
            else:
                scope_desc = "Ninguna avería seleccionada"
        else:
            self.filtered_incidents = list(base_incidents)
            scope_desc = "Todas las Averías"

        count = len(self.filtered_incidents)
        self.lbl_count_info.setText(f"Total a exportar: {count} registros ({scope_desc})")
        self.btn_generate.setEnabled(count > 0 or self.rb_faulty_eq.isChecked() or self.rb_bms_issues.isChecked())

    def _get_logo_path(self) -> str:
        from src.app.state_manager import StateManager
        return StateManager().get_logo_path()

    def _generate_pdf(self):
        if not self.export_service:
            QMessageBox.critical(self, "Error", "El servicio de exportación PDF no está disponible.")
            return

        clean_title = "".join(c for c in self.txt_title.text() if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        now_tag = datetime.now().strftime("%Y%m%d")
        default_filename = f"{clean_title}_{now_tag}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte de Averías en PDF",
            default_filename,
            "Archivos PDF (*.pdf)"
        )
        if not file_path:
            return

        try:
            client_name = ""
            site_name = ""
            cid = self.combo_client.currentData()
            sid = self.combo_site.currentData()
            if cid:
                client_name = self.combo_client.currentText()
            if sid:
                site_name = self.combo_site.currentText()

            logo_p = self._get_logo_path()

            if self.rb_single.isChecked() and self.selected_incident:
                self.export_service.export_incident_pdf(
                    incident=self.selected_incident,
                    output_path=file_path,
                    logo_path=logo_p,
                    client_name=client_name,
                    site_name=site_name,
                    equipment_service=self.equipment_service
                )

            elif self.rb_by_floor.isChecked():
                self.export_service.export_incidents_by_floor_pdf(
                    incident_list=self.filtered_incidents,
                    equipment_service=self.equipment_service,
                    title_text=self.txt_title.text().strip(),
                    subtitle_text=self.txt_subtitle.text().strip(),
                    client_name=client_name,
                    site_name=site_name,
                    logo_path=logo_p,
                    library_service=self.library_service,
                    include_floor_plans=self.chk_include_floor_plan.isChecked(),
                    output_path=file_path
                )

            elif self.rb_faulty_eq.isChecked():
                all_eq = self.equipment_service.get_all_equipment() if self.equipment_service else []
                faulty_eq = []
                for eq in all_eq:
                    st_val = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
                    if st_val in ["FAULT", "WARNING", "OUT_OF_SERVICE"]:
                        faulty_eq.append(eq)
                    elif self.incident_service:
                        open_incs = [
                            i for i in self.incident_service.get_incidents_for_equipment(eq.id)
                            if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"
                        ]
                        if open_incs:
                            faulty_eq.append(eq)

                if not faulty_eq:
                    QMessageBox.information(self, "Listado de Equipos", "No se encontraron equipos actualmente en avería o falla.")
                    return

                self.export_service.export_faulty_equipment_pdf(
                    equipment_list=faulty_eq,
                    incident_service=self.incident_service,
                    output_path=file_path,
                    logo_path=logo_p,
                    client_service=self.client_service
                )

            elif self.rb_bms_issues.isChecked():
                all_eq = self.equipment_service.get_all_equipment() if self.equipment_service else []
                bms_issue_eq = [
                    eq for eq in all_eq
                    if (getattr(eq, 'bms_status', '') or '').strip() and (getattr(eq, 'bms_status', '') or '').strip() not in ["Operativo", "OPERATIONAL"]
                ]
                if not bms_issue_eq:
                    QMessageBox.information(self, "Problemas BMS", "No se encontraron equipos registrados con problemas BMS / Control.")
                    return

                self.export_service.export_bms_issues_pdf(
                    equipment_list=bms_issue_eq,
                    incident_service=self.incident_service,
                    output_path=file_path,
                    logo_path=logo_p,
                    client_service=self.client_service
                )

            else:
                self.export_service.export_incidents_list_pdf(
                    incident_list=self.filtered_incidents,
                    title_text=self.txt_title.text().strip(),
                    subtitle_text=self.txt_subtitle.text().strip(),
                    scope_info=self.txt_title.text().strip(),
                    client_name=client_name,
                    site_name=site_name,
                    logo_path=logo_p,
                    equipment_service=self.equipment_service,
                    output_path=file_path
                )

            QMessageBox.information(
                self,
                "PDF Generado Exitosamente",
                f"El reporte de averías se generó correctamente en:\n\n{file_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar PDF", f"No se pudo generar el documento PDF:\n\n{e}")


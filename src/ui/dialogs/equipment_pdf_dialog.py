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
from src.core.models.enums import SYSTEM_TYPE_LABELS, OPERATIONAL_STATUS_LABELS
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class EquipmentPdfDialog(QDialog):
    """Dialog to configure and export customized equipment PDF reports."""

    def __init__(self, equipment_service, client_service, export_service, custom_lists_service=None, incident_service=None, library_service=None, parent=None):
        super().__init__(parent)
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.export_service = export_service
        self.custom_lists_service = custom_lists_service
        self.incident_service = incident_service
        self.library_service = library_service or getattr(parent, 'library_service', None)

        self.setWindowTitle("Generar Reporte PDF de Equipos")
        self.resize(860, 480)
        self.setMinimumSize(780, 430)
        self.setModal(True)

        self.all_equipment = self.equipment_service.get_all_equipment() if self.equipment_service else []
        self.filtered_equipment = []

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
        lbl_h = QLabel("Exportar Listado Oficial de Equipos a PDF")
        lbl_h.setObjectName("detailTitleLabel")
        lbl_h.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        lbl_sub = QLabel("Seleccione el criterio o filtro para generar el documento PDF con formato oficial:")
        lbl_sub.setObjectName("kvKeyLabel")
        header_text_layout.addWidget(lbl_h)
        header_text_layout.addWidget(lbl_sub)
        header_layout.addLayout(header_text_layout, 1)
        main_layout.addWidget(header_banner)

        # 2-Column Body Layout
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(12)

        # Left Column: 1. Criteria Group
        gb_criteria, criteria_body = _create_dialog_card("1. Alcance y Modalidad del Listado", "#38BDF8")
        criteria_layout = QVBoxLayout(criteria_body)
        criteria_layout.setContentsMargins(14, 12, 14, 12)
        criteria_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)

        self.rb_by_floor = QRadioButton("📑 Listado separado por Piso / Área (1 pág/piso)")
        self.rb_all = QRadioButton("📄 Listado General Consolidado (Todos los equipos)")
        self.rb_client = QRadioButton("🏢 Listado de equipos por Cliente")
        self.rb_site = QRadioButton("📍 Listado de equipos por Instalación")
        self.rb_floor = QRadioButton("🚪 Listado de un Piso / Nivel específico")
        self.rb_type = QRadioButton("❄️ Listado por Tipo / Especialidad")
        self.rb_status = QRadioButton("⚙️ Listado por Estado Operativo")
        self.rb_bms = QRadioButton("🖥️ Listado por Estado BMS / Control")

        self.rb_by_floor.setChecked(True)

        radios = [
            self.rb_by_floor, self.rb_all, self.rb_client, self.rb_site,
            self.rb_floor, self.rb_type, self.rb_status, self.rb_bms
        ]

        for idx, rb in enumerate(radios):
            self.btn_group.addButton(rb, idx)
            criteria_layout.addWidget(rb)

        self.btn_group.idClicked.connect(self._on_criteria_changed)
        cols_layout.addWidget(gb_criteria, 1)

        # Right Column: Filter params + Document data + Info box
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

        # System type combo
        self.combo_type = QComboBox()
        for stype, label in SYSTEM_TYPE_LABELS.items():
            val = stype.value if hasattr(stype, 'value') else str(stype)
            self.combo_type.addItem(label, val)
        self.params_layout.addRow("Tipo de Equipo:", self.combo_type)

        # Operational status combo
        self.combo_status = QComboBox()
        for status, label in OPERATIONAL_STATUS_LABELS.items():
            val = status.value if hasattr(status, 'value') else str(status)
            self.combo_status.addItem(label, val)
        self.params_layout.addRow("Estado Operativo:", self.combo_status)

        # BMS status combo
        self.combo_bms = QComboBox()
        if self.custom_lists_service:
            bms_opts = self.custom_lists_service.get_list("bms_status")
        else:
            bms_opts = ["Operativo", "En Falla", "Sin Grafica", "Sin Control", "Fuera de Servicio", "Inexistente"]
        for opt in bms_opts:
            self.combo_bms.addItem(f"BMS: {opt}", opt)
        self.params_layout.addRow("Estado BMS / Control:", self.combo_bms)

        # Floor plan image check
        self.chk_include_floor_plan = QCheckBox("🗺️ Incluir plano/imagen del piso si existe en Librería")
        self.chk_include_floor_plan.setChecked(True)
        self.params_layout.addRow("", self.chk_include_floor_plan)

        right_col.addWidget(self.gb_params)

        # 3. Document Customization
        gb_doc, doc_body = _create_dialog_card("3. Datos del Documento", "#10B981")
        doc_layout = QFormLayout(doc_body)
        doc_layout.setContentsMargins(14, 12, 14, 12)
        doc_layout.setSpacing(6)

        self.txt_title = QLineEdit("Listado de Equipos por Piso / Área")
        self.txt_subtitle = QLineEdit("ControlHVAC CMMS - Gestión e Inventario de Activos")
        doc_layout.addRow("Título del PDF:", self.txt_title)
        doc_layout.addRow("Subtítulo:", self.txt_subtitle)

        right_col.addWidget(gb_doc)

        # Count indicator box
        self.lbl_count_info = QLabel("Se incluirán 0 equipos en el reporte PDF.")
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

        # Now populate and connect signals safely
        self._populate_clients()
        self._populate_floors()

        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        self.combo_site.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_floor.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_type.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_status.currentIndexChanged.connect(self._update_filter_selection)
        self.combo_bms.currentIndexChanged.connect(self._update_filter_selection)

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
        # Show/Hide relevant controls in params layout
        is_by_floor = self.rb_by_floor.isChecked()
        is_client = self.rb_client.isChecked()
        is_site = self.rb_site.isChecked()
        is_floor = self.rb_floor.isChecked()
        is_type = self.rb_type.isChecked()
        is_status = self.rb_status.isChecked()
        is_bms = self.rb_bms.isChecked()

        self.combo_client.setEnabled(is_by_floor or is_client or is_site)
        self.combo_site.setEnabled(is_by_floor or is_site)
        self.combo_floor.setEnabled(is_floor)
        self.combo_type.setEnabled(is_type)
        self.combo_status.setEnabled(is_status)
        self.combo_bms.setEnabled(is_bms)
        self.chk_include_floor_plan.setVisible(is_by_floor)

        self._update_filter_selection()

    def _update_filter_selection(self):
        if self.rb_by_floor.isChecked():
            cid = self.combo_client.currentData()
            sid = self.combo_site.currentData()
            base_list = list(self.all_equipment)
            if cid:
                base_list = [eq for eq in base_list if eq.client_id == cid]
            if sid:
                base_list = [eq for eq in base_list if eq.site_id == sid]
            self.filtered_equipment = base_list

            floors_found = set()
            for eq in self.filtered_equipment:
                fl = (getattr(eq, 'floor_area', '') or '').strip() or (eq.location_description or '').strip() or "Sin Piso / Área"
                floors_found.add(fl)

            c_name = self.combo_client.currentText() if cid else ""
            s_name = self.combo_site.currentText() if sid else ""
            if c_name and s_name:
                self.txt_title.setText(f"Listado por Pisos - {s_name}")
            elif c_name:
                self.txt_title.setText(f"Listado por Pisos - {c_name}")
            else:
                self.txt_title.setText("Listado de Equipos por Piso / Área")

            scope_desc = f"{len(floors_found)} pisos/áreas detectadas (1 página por piso)"

        elif self.rb_all.isChecked():
            self.filtered_equipment = list(self.all_equipment)
            self.txt_title.setText("Listado General de Equipos HVAC")
            scope_desc = "Todos los Equipos"

        elif self.rb_client.isChecked():
            cid = self.combo_client.currentData()
            c_name = self.combo_client.currentText()
            if cid:
                self.filtered_equipment = [eq for eq in self.all_equipment if eq.client_id == cid]
                self.txt_title.setText(f"Listado de Equipos - {c_name}")
                scope_desc = f"Cliente: {c_name}"
            else:
                self.filtered_equipment = list(self.all_equipment)
                self.txt_title.setText("Listado de Equipos - Todos los Clientes")
                scope_desc = "Todos los Clientes"

        elif self.rb_site.isChecked():
            cid = self.combo_client.currentData()
            sid = self.combo_site.currentData()
            s_name = self.combo_site.currentText()
            c_name = self.combo_client.currentText()
            base = self.all_equipment
            if cid:
                base = [eq for eq in base if eq.client_id == cid]
            if sid:
                base = [eq for eq in base if eq.site_id == sid]
            self.filtered_equipment = base
            self.txt_title.setText(f"Listado de Equipos - {s_name}")
            scope_desc = f"Instalación: {s_name} ({c_name})"

        elif self.rb_floor.isChecked():
            fl = self.combo_floor.currentData()
            self.filtered_equipment = [eq for eq in self.all_equipment if (getattr(eq, 'floor_area', '') or '').strip() == fl]
            self.txt_title.setText(f"Listado de Equipos - {fl}")
            scope_desc = f"Piso / Nivel: {fl}"

        elif self.rb_type.isChecked():
            t_val = self.combo_type.currentData()
            t_label = self.combo_type.currentText()
            self.filtered_equipment = [
                eq for eq in self.all_equipment 
                if (eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)) == t_val
            ]
            self.txt_title.setText(f"Listado de Equipos - {t_label}")
            scope_desc = f"Tipo / Sistema: {t_label}"

        elif self.rb_status.isChecked():
            st_val = self.combo_status.currentData()
            st_label = self.combo_status.currentText()
            self.filtered_equipment = [
                eq for eq in self.all_equipment 
                if (eq.status.value if hasattr(eq.status, 'value') else str(eq.status)) == st_val
            ]
            self.txt_title.setText(f"Listado de Equipos en Estado: {st_label}")
            scope_desc = f"Estado Operativo: {st_label}"

        elif self.rb_bms.isChecked():
            b_val = self.combo_bms.currentData()
            b_label = self.combo_bms.currentText()
            self.filtered_equipment = [
                eq for eq in self.all_equipment 
                if (getattr(eq, 'bms_status', '') or '').strip() == b_val
            ]
            self.txt_title.setText(f"Listado de Equipos - {b_label}")
            scope_desc = f"Estado BMS / Control: {b_label}"
        else:
            self.filtered_equipment = list(self.all_equipment)
            scope_desc = "Todos los Equipos"

        count = len(self.filtered_equipment)
        self.lbl_count_info.setText(f"Total a exportar: {count} equipos ({scope_desc})")
        self.btn_generate.setEnabled(count > 0)

    def _get_logo_path(self) -> str:
        from src.app.state_manager import StateManager
        return StateManager().get_logo_path()

    def _generate_pdf(self):
        if not self.filtered_equipment:
            QMessageBox.warning(self, "Exportar PDF", "No hay equipos que coincidan con el criterio seleccionado.")
            return

        if not self.export_service:
            QMessageBox.critical(self, "Error", "El servicio de exportación PDF no está disponible.")
            return

        clean_title = "".join(c for c in self.txt_title.text() if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        now_tag = datetime.now().strftime("%Y%m%d")
        default_filename = f"{clean_title}_{now_tag}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Listado de Equipos en PDF",
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

            scope_info = self.txt_title.text()
            logo_p = self._get_logo_path()

            if self.rb_by_floor.isChecked():
                self.export_service.export_equipment_by_floor_pdf(
                    equipment_list=self.filtered_equipment,
                    title_text=self.txt_title.text().strip(),
                    subtitle_text=self.txt_subtitle.text().strip(),
                    client_name=client_name,
                    site_name=site_name,
                    logo_path=logo_p,
                    library_service=self.library_service,
                    include_floor_plans=self.chk_include_floor_plan.isChecked(),
                    incident_service=self.incident_service,
                    output_path=file_path
                )
            else:
                self.export_service.export_equipment_inventory_pdf(
                    equipment_list=self.filtered_equipment,
                    title_text=self.txt_title.text().strip(),
                    subtitle_text=self.txt_subtitle.text().strip(),
                    scope_info=scope_info,
                    client_name=client_name,
                    site_name=site_name,
                    logo_path=logo_p,
                    incident_service=self.incident_service,
                    output_path=file_path
                )

            QMessageBox.information(
                self,
                "PDF Generado Exitosamente",
                f"El reporte de equipos se generó correctamente en:\n\n{file_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar PDF", f"No se pudo generar el documento PDF:\n\n{e}")


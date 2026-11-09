from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QComboBox, QGroupBox, QCheckBox, 
    QLineEdit, QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QColor, QFont, QCursor

from src.core.models.enums import (
    SYSTEM_TYPE_LABELS, OPERATIONAL_STATUS_LABELS, MAINTENANCE_FREQUENCY_LABELS
)
from src.ui.icon_manager import IconManager


def _create_section_card(title: str, accent_color: str = "#38BDF8"):
    card = QFrame()
    card.setObjectName("eqSectionCard")
    card_l = QVBoxLayout(card)
    card_l.setContentsMargins(0, 0, 0, 0)
    card_l.setSpacing(0)

    header = QFrame()
    header.setObjectName("eqCardHeader")
    header.setStyleSheet(f"QFrame#eqCardHeader {{ border-bottom: 2px solid {accent_color}; }}")
    h_l = QHBoxLayout(header)
    h_l.setContentsMargins(14, 9, 14, 9)

    dot = QLabel("●")
    dot.setStyleSheet(f"color: {accent_color}; font-size: 10px; background: transparent; border: none;")
    h_l.addWidget(dot)

    lbl = QLabel(title.upper())
    lbl.setStyleSheet(
        f"color: {accent_color}; font-weight: 700; font-size: 11px; "
        f"letter-spacing: 0.7px; background: transparent; border: none;"
    )
    h_l.addWidget(lbl)
    h_l.addStretch()

    card_l.addWidget(header)

    body = QWidget()
    body.setObjectName("eqCardBody")
    card_l.addWidget(body, 1)
    return card, body

class BulkEquipmentWidget(QWidget):
    """Widget to bulk-update fields for selected equipment in a specific installation."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.equipment_service = getattr(main_window, 'equipment_service', None)
        self.client_service = getattr(main_window, 'client_service', None)
        self.inventory_service = getattr(main_window, 'inventory_service', None)
        
        self.current_equipments = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header description
        lbl_info = QLabel("Seleccione el cliente e instalación, marque los equipos deseados y defina los campos que desea actualizar de forma masiva:")
        lbl_info.setObjectName("kvKeyLabel")
        lbl_info.setWordWrap(True)
        main_layout.addWidget(lbl_info)

        # Top: Select Client & Site
        top_card, top_box = _create_section_card("1. Seleccionar Cliente e Instalación", "#38BDF8")
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(14, 12, 14, 12)
        top_layout.setSpacing(15)

        top_layout.addWidget(QLabel("Cliente:"))
        self.combo_client = QComboBox()
        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        top_layout.addWidget(self.combo_client, 1)

        top_layout.addWidget(QLabel("Instalación:"))
        self.combo_site = QComboBox()
        self.combo_site.currentIndexChanged.connect(self._on_site_changed)
        top_layout.addWidget(self.combo_site, 1)

        main_layout.addWidget(top_card)

        # Splitter: Left Table (Equipments) / Right (Fields to Apply)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # --- Left: Equipment Selection Table ---
        left_card, left_box = _create_section_card("2. Seleccionar Equipos a Modificar", "#F59E0B")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        sel_btn_row = QHBoxLayout()
        btn_select_all = QPushButton("Seleccionar Todos")
        btn_select_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_select_all.clicked.connect(self._select_all_equipment)
        btn_deselect_all = QPushButton("Deseleccionar Todos")
        btn_deselect_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_deselect_all.clicked.connect(self._deselect_all_equipment)
        
        self.lbl_selected_count = QLabel("0 equipos seleccionados")
        self.lbl_selected_count.setObjectName("distCountBadge")
        self.lbl_selected_count.setStyleSheet(
            "color: #38BDF8; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 6px;"
        )
        
        sel_btn_row.addWidget(btn_select_all)
        sel_btn_row.addWidget(btn_deselect_all)
        sel_btn_row.addStretch()
        sel_btn_row.addWidget(self.lbl_selected_count)
        left_layout.addLayout(sel_btn_row)

        self.table_equipment = QTableWidget()
        self.table_equipment.setAlternatingRowColors(True)
        self.table_equipment.setShowGrid(False)
        self.table_equipment.setIconSize(QSize(16, 16))
        self.table_equipment.verticalHeader().setVisible(False)
        self.table_equipment.verticalHeader().setDefaultSectionSize(32)
        self.table_equipment.setColumnCount(6)
        self.table_equipment.setHorizontalHeaderLabels(["✓", "Tag / Equipo", "Tipo de Sistema", "Estado BMS", "Piso / Área", "Marca"])
        hdr = self.table_equipment.horizontalHeader()
        hdr.setSectionsMovable(True)
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        self.table_equipment.setColumnWidth(0, 42)
        self.table_equipment.setColumnWidth(1, 130)
        self.table_equipment.setColumnWidth(2, 165)
        self.table_equipment.setColumnWidth(3, 115)
        self.table_equipment.setColumnWidth(4, 110)
        self.table_equipment.itemChanged.connect(self._update_selected_count)
        left_layout.addWidget(self.table_equipment)

        splitter.addWidget(left_card)

        # --- Right: Bulk Fields to Apply ---
        right_card, right_box = _create_section_card("3. Campos a Modificar de Forma Masiva", "#10B981")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        lbl_fields_note = QLabel("Marque la casilla del campo que desea aplicar a los equipos seleccionados:")
        lbl_fields_note.setObjectName("kvKeyLabel")
        right_layout.addWidget(lbl_fields_note)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # 1. Manufacturer (Marca)
        self.chk_mfr = QCheckBox("Fabricante / Marca:")
        self.edit_mfr = QLineEdit()
        self.edit_mfr.setPlaceholderText("Ej: York, Carrier, Trane, Daikin")
        self.edit_mfr.setEnabled(False)
        self.chk_mfr.toggled.connect(self.edit_mfr.setEnabled)
        form_layout.addRow(self.chk_mfr, self.edit_mfr)

        # 2. Floor / Area
        self.chk_floor = QCheckBox("Piso / Nivel / Área:")
        self.edit_floor = QLineEdit()
        self.edit_floor.setPlaceholderText("Ej: Piso 1, Azotea, Sala Técnica")
        self.edit_floor.setEnabled(False)
        self.chk_floor.toggled.connect(self.edit_floor.setEnabled)
        form_layout.addRow(self.chk_floor, self.edit_floor)

        # 3. System Type
        self.chk_type = QCheckBox("Tipo de Sistema:")
        self.combo_type = QComboBox()
        for stype, label in SYSTEM_TYPE_LABELS.items():
            self.combo_type.addItem(label, stype.value)
        self.combo_type.setEnabled(False)
        self.chk_type.toggled.connect(self.combo_type.setEnabled)
        form_layout.addRow(self.chk_type, self.combo_type)

        # 4. Status
        self.chk_status = QCheckBox("Estado Operativo:")
        self.combo_status = QComboBox()
        for status, label in OPERATIONAL_STATUS_LABELS.items():
            self.combo_status.addItem(label, status.value)
        self.combo_status.setEnabled(False)
        self.chk_status.toggled.connect(self.combo_status.setEnabled)
        form_layout.addRow(self.chk_status, self.combo_status)

        # 4b. BMS Status
        self.chk_bms_status = QCheckBox("Estado BMS / Control:")
        self.combo_bms_status = QComboBox()
        bms_opts = ["Operativo", "En Falla", "Sin Grafica", "Sin Control", "Fuera de Servicio", "Inexistente"]
        if hasattr(self.main_window, 'custom_lists_service') and self.main_window.custom_lists_service:
            bms_opts = self.main_window.custom_lists_service.get_list("bms_status")
        for b_opt in bms_opts:
            self.combo_bms_status.addItem(b_opt, b_opt)
        self.combo_bms_status.setEnabled(False)
        self.chk_bms_status.toggled.connect(self.combo_bms_status.setEnabled)
        form_layout.addRow(self.chk_bms_status, self.combo_bms_status)

        # 5. Maintenance Frequency
        self.chk_freq = QCheckBox("Frecuencia Mantenimiento:")
        self.combo_freq = QComboBox()
        for freq, label in MAINTENANCE_FREQUENCY_LABELS.items():
            self.combo_freq.addItem(label, freq.value)
        default_freq_idx = self.combo_freq.findData("MONTHLY")
        if default_freq_idx >= 0:
            self.combo_freq.setCurrentIndex(default_freq_idx)
        self.combo_freq.setEnabled(False)
        self.chk_freq.toggled.connect(self.combo_freq.setEnabled)
        form_layout.addRow(self.chk_freq, self.combo_freq)

        # 6. Installation Date
        self.chk_inst_date = QCheckBox("Fecha de Instalación:")
        self.date_inst = QDateEdit()
        self.date_inst.setCalendarPopup(True)
        self.date_inst.setDate(QDate.currentDate())
        self.date_inst.setEnabled(False)
        self.chk_inst_date.toggled.connect(self.date_inst.setEnabled)
        form_layout.addRow(self.chk_inst_date, self.date_inst)

        # 7. Warranty Date
        self.chk_warr_date = QCheckBox("Garantía Hasta:")
        self.date_warr = QDateEdit()
        self.date_warr.setCalendarPopup(True)
        self.date_warr.setDate(QDate.currentDate().addYears(1))
        self.date_warr.setEnabled(False)
        self.chk_warr_date.toggled.connect(self.date_warr.setEnabled)
        form_layout.addRow(self.chk_warr_date, self.date_warr)

        # 8. Spare parts
        self.chk_spare = QCheckBox("Repuestos Compatibles:")
        self.edit_spare = QLineEdit()
        self.edit_spare.setPlaceholderText("Ej: Correa A75, Filtro 24x24x2")
        self.edit_spare.setEnabled(False)
        self.chk_spare.toggled.connect(self.edit_spare.setEnabled)
        form_layout.addRow(self.chk_spare, self.edit_spare)

        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        # Apply button
        self.btn_apply = QPushButton("Aplicar Cambios Masivos a los Equipos")
        self.btn_apply.setObjectName("primaryButton")
        self.btn_apply.setIcon(IconManager.get_icon("save.svg", "#FFFFFF"))
        self.btn_apply.clicked.connect(self._run_bulk_update)
        right_layout.addWidget(self.btn_apply)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        splitter.addWidget(right_card)
        splitter.setSizes([500, 380])

        self._populate_clients()

    def _populate_clients(self):
        self.combo_client.clear()
        if not self.client_service:
            return
        try:
            clients = self.client_service.get_all_clients()
            for c in clients:
                cname = getattr(c, 'company_name', '') or getattr(c, 'name', '')
                self.combo_client.addItem(cname, c.id)
            self._on_client_changed()
        except Exception:
            pass

    def _on_client_changed(self):
        self.combo_site.clear()
        cid = self.combo_client.currentData()
        if cid:
            try:
                sites = self.client_service.get_sites_for_client(cid)
                for s in sites:
                    self.combo_site.addItem(s.name, s.id)
                self._on_site_changed()
            except Exception:
                pass

    def _on_site_changed(self):
        site_id = self.combo_site.currentData()
        self.table_equipment.setRowCount(0)
        self.current_equipments = []
        if not site_id:
            self._update_selected_count()
            return

        try:
            self.current_equipments = self.equipment_service.get_equipment_for_site(site_id)
            self.table_equipment.blockSignals(True)
            self.table_equipment.setRowCount(len(self.current_equipments))
            
            sys_label_map = {k.value if hasattr(k, 'value') else str(k): v for k, v in SYSTEM_TYPE_LABELS.items()}
            bold_font = QFont()
            bold_font.setBold(True)

            for row, eq in enumerate(self.current_equipments):
                self.table_equipment.setRowHeight(row, 32)
                # Checkbox item
                chk_item = QTableWidgetItem()
                chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_item.setCheckState(Qt.CheckState.Unchecked)
                chk_item.setData(Qt.ItemDataRole.UserRole, str(eq.id))
                self.table_equipment.setItem(row, 0, chk_item)

                # System Type string
                stype_str = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
                stype_label = sys_label_map.get(stype_str, stype_str)

                # Tag + Icon
                tag_item = QTableWidgetItem(eq.tag)
                tag_item.setFont(bold_font)
                tag_item.setIcon(IconManager.get_equipment_icon(stype_str, "#38BDF8"))
                self.table_equipment.setItem(row, 1, tag_item)

                # System Type human-readable label
                self.table_equipment.setItem(row, 2, QTableWidgetItem(stype_label))

                # BMS Status with dot badge
                bms_st = getattr(eq, 'bms_status', 'Operativo') or 'Operativo'
                bms_item = QTableWidgetItem(f"●  {bms_st}")
                bms_item.setFont(bold_font)
                b_low = bms_st.lower()
                if "falla" in b_low or "fuera" in b_low or "alarma" in b_low:
                    bms_item.setForeground(QColor("#EF4444"))
                elif "sin " in b_low or "manual" in b_low or "inexistente" in b_low:
                    bms_item.setForeground(QColor("#F59E0B"))
                else:
                    bms_item.setForeground(QColor("#10B981"))
                self.table_equipment.setItem(row, 3, bms_item)

                # Floor / Area
                floor_str = getattr(eq, 'floor_area', '') or ""
                self.table_equipment.setItem(row, 4, QTableWidgetItem(floor_str))

                # Manufacturer
                self.table_equipment.setItem(row, 5, QTableWidgetItem(eq.manufacturer or ""))

            self.table_equipment.blockSignals(False)
            self._update_selected_count()
        except Exception as e:
            self.table_equipment.blockSignals(False)
            print(f"Error loading site equipment: {e}")

    def _select_all_equipment(self):
        for row in range(self.table_equipment.rowCount()):
            item = self.table_equipment.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all_equipment(self):
        for row in range(self.table_equipment.rowCount()):
            item = self.table_equipment.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _update_selected_count(self):
        count = 0
        for row in range(self.table_equipment.rowCount()):
            item = self.table_equipment.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        self.lbl_selected_count.setText(f"{count} equipos seleccionados")

    def _run_bulk_update(self):
        # 1. Collect selected equipment IDs
        selected_ids = []
        for row in range(self.table_equipment.rowCount()):
            item = self.table_equipment.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                eq_id = item.data(Qt.ItemDataRole.UserRole)
                if eq_id:
                    selected_ids.append(str(eq_id))

        if not selected_ids:
            QMessageBox.warning(self, "Atención", "Debe marcar al menos un equipo de la tabla para modificar.")
            return

        # 2. Check if at least one field checkbox is active
        active_fields = []
        if self.chk_mfr.isChecked(): active_fields.append("Fabricante / Marca")
        if self.chk_floor.isChecked(): active_fields.append("Piso / Nivel / Área")
        if self.chk_type.isChecked(): active_fields.append("Tipo de Sistema")
        if self.chk_status.isChecked(): active_fields.append("Estado Operativo")
        if self.chk_bms_status.isChecked(): active_fields.append("Estado BMS / Control")
        if self.chk_freq.isChecked(): active_fields.append("Frecuencia Mantenimiento")
        if self.chk_inst_date.isChecked(): active_fields.append("Fecha Instalación")
        if self.chk_warr_date.isChecked(): active_fields.append("Garantía")
        if self.chk_spare.isChecked(): active_fields.append("Repuestos")

        if not active_fields:
            QMessageBox.warning(self, "Atención", "Debe marcar al menos una casilla de campo para actualizar.")
            return

        # Confirm dialog
        fields_str = "\n• " + "\n• ".join(active_fields)
        reply = QMessageBox.question(
            self,
            "Confirmar Modificación Masiva",
            f"¿Está seguro de que desea actualizar {len(selected_ids)} equipos con los siguientes campos?{fields_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected_ids))
        self.progress_bar.setValue(0)

        updated_count = 0
        for idx, eq_id in enumerate(selected_ids):
            eq = self.equipment_service.get_equipment(eq_id)
            if not eq:
                continue

            if self.chk_mfr.isChecked():
                eq.manufacturer = self.edit_mfr.text().strip()

            if self.chk_floor.isChecked():
                eq.floor_area = self.edit_floor.text().strip()

            if self.chk_type.isChecked():
                eq.system_type = self.combo_type.currentData()

            if self.chk_status.isChecked():
                eq.status = self.combo_status.currentData()

            if self.chk_bms_status.isChecked():
                eq.bms_status = self.combo_bms_status.currentText().strip() or "Operativo"

            if self.chk_freq.isChecked():
                eq.maintenance_frequency = self.combo_freq.currentData()

            if self.chk_inst_date.isChecked():
                eq.installation_date = self.date_inst.date().toString(Qt.DateFormat.ISODate)

            if self.chk_warr_date.isChecked():
                eq.warranty_expiry = self.date_warr.date().toString(Qt.DateFormat.ISODate)

            if self.chk_spare.isChecked():
                sp_raw = self.edit_spare.text().strip()
                sp_list = [s.strip() for s in sp_raw.split(',') if s.strip()] if sp_raw else []
                eq.spare_parts = sp_list

            self.equipment_service.save_equipment(eq)
            updated_count += 1
            self.progress_bar.setValue(idx + 1)

        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self,
            "Modificación Masiva Completada",
            f"Se han actualizado exitosamente {updated_count} equipos."
        )

        # Refresh table and app views
        self._on_site_changed()
        if hasattr(self.main_window, '_refresh_current_view'):
            self.main_window._refresh_current_view()

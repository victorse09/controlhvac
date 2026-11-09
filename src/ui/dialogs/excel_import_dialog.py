import os
import openpyxl
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QComboBox, QGroupBox, QFileDialog, 
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QCursor

from src.core.models.equipment import HVACEquipment
from src.ui.icon_manager import IconManager
from src.ui.dialogs.bulk_equipment_widget import _create_section_card

EQUIPMENT_FIELDS = [
    ("tag", "Tag / Código Equipo *", True),
    ("bms_id", "ID / Orden BMS", False),
    ("bms_status", "Estado BMS / Control", False),
    ("floor_area", "Piso / Nivel / Área", False),
    ("system_type", "Tipo de Sistema", False),
    ("manufacturer", "Fabricante / Marca", False),
    ("model_number", "Modelo", False),
    ("serial_number", "Número de Serie", False),
    ("installation_date", "Fecha Instalación (AAAA-MM-DD)", False),
    ("warranty_expiry", "Garantía Hasta (AAAA-MM-DD)", False),
    ("location_description", "Ubicación Específica", False),
    ("status", "Estado Operativo", False),
    ("maintenance_frequency", "Frecuencia Mantenimiento", False),
    ("spare_parts", "Repuestos Asociados (sep. por coma)", False),
    ("notes", "Notas / Observaciones", False),
]

COLUMN_MAP_RULES = {
    "tag": ["tag", "codigo", "código", "nombre", "equipo", "id equipo"],
    "bms_id": ["bms", "bms id", "orden bms", "id bms", "bms_id"],
    "bms_status": ["estado bms", "estado control", "status bms", "bms status", "estado_bms", "control bms"],
    "floor_area": ["piso", "nivel", "area", "área", "sector", "ubicacion piso"],
    "system_type": ["tipo", "sistema", "tipo sistema", "tipo equipo", "type"],
    "manufacturer": ["marca", "fabricante", "brand", "make", "manufacturer"],
    "model_number": ["modelo", "model", "nro modelo"],
    "serial_number": ["serie", "serial", "nro serie", "sn", "s/n"],
    "installation_date": ["instalacion", "instalación", "fecha instalacion", "fecha instalación"],
    "warranty_expiry": ["garantia", "garantía", "vencimiento garantia"],
    "location_description": ["ubicacion", "ubicación", "sala", "detalles ubicacion"],
    "status": ["estado", "status", "condicion", "condición"],
    "maintenance_frequency": ["frecuencia", "frecuencia mant", "mantenimiento"],
    "spare_parts": ["repuestos", "repuesto", "partes", "consumibles"],
    "notes": ["notas", "observaciones", "comentarios"]
}

class ExcelImportWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.equipment_service = getattr(main_window, 'equipment_service', None)
        self.client_service = getattr(main_window, 'client_service', None)
        
        self.file_path = ""
        self.workbook = None
        self.excel_headers = []
        self.mapping_combos = {}
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)

        # 1. Select Excel File & Sheet Group
        card_file, gb_file = _create_section_card("1. Selección de Planilla Excel y Pestaña", "#38BDF8")
        file_layout = QVBoxLayout(gb_file)
        file_layout.setContentsMargins(14, 12, 14, 12)
        file_layout.setSpacing(10)
        
        file_row = QHBoxLayout()
        self.lbl_file = QLabel("No se ha seleccionado archivo (.xlsx)")
        self.lbl_file.setObjectName("eqStatusBanner")
        self.lbl_file.setStyleSheet("color: #38BDF8; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        
        btn_file = QPushButton("Examinar Excel...")
        btn_file.setIcon(IconManager.get_icon("folder.svg", "#38BDF8"))
        btn_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_file.clicked.connect(self._select_excel_file)
        
        file_row.addWidget(self.lbl_file, 1)
        file_row.addWidget(btn_file)
        file_layout.addLayout(file_row)

        sheet_row = QHBoxLayout()
        sheet_row.addWidget(QLabel("Pestaña / Hoja del Excel:"))
        self.combo_sheet = QComboBox()
        self.combo_sheet.currentIndexChanged.connect(self._on_sheet_changed)
        sheet_row.addWidget(self.combo_sheet, 1)
        file_layout.addLayout(sheet_row)

        layout.addWidget(card_file)

        # 2. Select Client & Site Target
        card_target, gb_target = _create_section_card("2. Cliente e Instalación de Destino", "#F59E0B")
        target_layout = QFormLayout(gb_target)
        target_layout.setContentsMargins(14, 12, 14, 12)
        target_layout.setSpacing(10)
        
        self.combo_client = QComboBox()
        self.combo_site = QComboBox()
        self._populate_clients()
        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        
        target_layout.addRow("Cliente Destino *:", self.combo_client)
        target_layout.addRow("Instalación Destino *:", self.combo_site)
        layout.addWidget(card_target)

        # 3. Column Mapping Table Group
        card_map, gb_map = _create_section_card("3. Cruce de Datos (Mapeo de Columnas Excel vs Campos de Equipo)", "#10B981")
        map_layout = QVBoxLayout(gb_map)
        map_layout.setContentsMargins(14, 12, 14, 12)
        map_layout.setSpacing(8)
        
        lbl_map_info = QLabel("Asigne qué columna de la hoja Excel corresponde a cada campo de los Equipos:")
        lbl_map_info.setObjectName("kvKeyLabel")
        map_layout.addWidget(lbl_map_info)
        
        self.map_table = QTableWidget()
        self.map_table.setAlternatingRowColors(True)
        self.map_table.setShowGrid(False)
        self.map_table.verticalHeader().setVisible(False)
        self.map_table.setColumnCount(2)
        self.map_table.setHorizontalHeaderLabels(["Campo de Equipo en Sistema", "Columna en la Hoja Excel"])
        self.map_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.map_table.verticalHeader().setDefaultSectionSize(36)
        self.map_table.verticalHeader().setMinimumSectionSize(32)
        self.map_table.setRowCount(len(EQUIPMENT_FIELDS))
        
        bold_font = QFont()
        bold_font.setBold(True)
        for row, (field_key, field_label, required) in enumerate(EQUIPMENT_FIELDS):
            self.map_table.setRowHeight(row, 36)
            item_lbl = QTableWidgetItem(field_label)
            if required:
                item_lbl.setForeground(QColor("#F59E0B"))
                item_lbl.setFont(bold_font)
            self.map_table.setItem(row, 0, item_lbl)
            
            combo = QComboBox()
            combo.setStyleSheet("QComboBox { padding: 4px 8px; min-height: 24px; font-size: 12px; }")
            combo.addItem("(Ignorar)", "")
            self.map_table.setCellWidget(row, 1, combo)
            self.mapping_combos[field_key] = combo

        map_layout.addWidget(self.map_table)
        layout.addWidget(card_map, 1)

        # 4. Import Actions & Progress
        act_row = QHBoxLayout()
        self.btn_preview = QPushButton("Vista Previa (Primeras 10 filas)")
        self.btn_preview.setIcon(IconManager.get_icon("search.svg", "#F8FAFC"))
        self.btn_preview.clicked.connect(self._show_preview)
        
        self.btn_import = QPushButton("Iniciar Importación de Equipos")
        self.btn_import.setObjectName("primaryButton")
        self.btn_import.setIcon(IconManager.get_icon("excel.svg", "#FFFFFF"))
        self.btn_import.clicked.connect(self._run_import)
        
        act_row.addWidget(self.btn_preview)
        act_row.addStretch()
        act_row.addWidget(self.btn_import)
        layout.addLayout(act_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _populate_clients(self):
        self.combo_client.clear()
        if not self.client_service:
            return
        try:
            clients = self.client_service.get_all_clients()
            for c in clients:
                self.combo_client.addItem(c.company_name, c.id)
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
            except Exception:
                pass

    def _select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Planilla de Equipos Excel",
            os.path.expanduser("~"),
            "Archivos Excel (*.xlsx *.xlsm *.xls)"
        )
        if not file_path:
            return
            
        self.file_path = file_path
        self.lbl_file.setText(os.path.basename(file_path))
        
        try:
            self.workbook = openpyxl.load_workbook(file_path, data_only=True)
            self.combo_sheet.clear()
            self.combo_sheet.addItems(self.workbook.sheetnames)
        except Exception as e:
            QMessageBox.critical(self, "Error al Abrir Excel", f"No se pudo leer el archivo Excel:\n\n{e}")

    def _on_sheet_changed(self):
        sheet_name = self.combo_sheet.currentText()
        if not self.workbook or not sheet_name:
            return
            
        try:
            sheet = self.workbook[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            
            # Find first non-empty row as header
            self.excel_headers = []
            for r in rows:
                if any(cell is not None for cell in r):
                    self.excel_headers = [str(cell).strip() if cell is not None else f"Columna {i+1}" for i, cell in enumerate(r)]
                    break
                    
            # Populate mapping dropdowns
            for field_key, combo in self.mapping_combos.items():
                combo.clear()
                combo.addItem("(Ignorar)", "")
                for idx, h in enumerate(self.excel_headers):
                    combo.addItem(f"[{idx+1}] {h}", idx)
                    
                # Auto-matching rule
                rules = COLUMN_MAP_RULES.get(field_key, [])
                for idx, h in enumerate(self.excel_headers):
                    h_norm = h.lower()
                    if any(r in h_norm for r in rules):
                        combo.setCurrentIndex(idx + 1)
                        break

        except Exception as e:
            print(f"Error reading sheet headers: {e}")

    def _get_mapped_data_rows(self, max_rows=None):
        sheet_name = self.combo_sheet.currentText()
        if not self.workbook or not sheet_name:
            return []

        sheet = self.workbook[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []

        # Find header index
        header_row_idx = 0
        for i, r in enumerate(rows):
            if any(cell is not None for cell in r):
                header_row_idx = i
                break

        data_rows = rows[header_row_idx + 1:]
        if max_rows:
            data_rows = data_rows[:max_rows]

        # Extract mapping indices
        mapping = {}
        for field_key, combo in self.mapping_combos.items():
            col_idx = combo.currentData()
            if col_idx is not None and col_idx != "":
                mapping[field_key] = int(col_idx)

        mapped_results = []
        for r in data_rows:
            if not any(cell is not None for cell in r):
                continue
                
            row_dict = {}
            for field_key, col_idx in mapping.items():
                if col_idx < len(r):
                    val = r[col_idx]
                    row_dict[field_key] = str(val).strip() if val is not None else ""
                else:
                    row_dict[field_key] = ""
            if row_dict.get("tag"):
                mapped_results.append(row_dict)

        return mapped_results

    def _show_preview(self):
        rows = self._get_mapped_data_rows(max_rows=10)
        if not rows:
            QMessageBox.warning(self, "Vista Previa", "No se encontraron filas de datos mapeadas. Verifique la selección de hoja y la columna 'Tag / Código Equipo'.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Vista Previa de Importación de Equipos")
        dlg.resize(750, 400)
        
        l = QVBoxLayout(dlg)
        lbl = QLabel(f"Se muestra la vista previa de las primeras {len(rows)} filas que se importarán:")
        l.addWidget(lbl)

        tbl = QTableWidget()
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        headers = [f_label for _, f_label, _ in EQUIPMENT_FIELDS]
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setRowCount(len(rows))

        for r_idx, r_data in enumerate(rows):
            for c_idx, (f_key, _, _) in enumerate(EQUIPMENT_FIELDS):
                val = r_data.get(f_key, "")
                tbl.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

        l.addWidget(tbl)
        btn_close = QPushButton("Cerrar Vista Previa")
        btn_close.clicked.connect(dlg.accept)
        l.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        dlg.exec()

    def _run_import(self):
        client_id = self.combo_client.currentData()
        site_id = self.combo_site.currentData()

        if not client_id or not site_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar un Cliente e Instalación de destino.")
            return

        tag_col = self.mapping_combos["tag"].currentData()
        if tag_col is None or tag_col == "":
            QMessageBox.warning(self, "Error", "La columna para 'Tag / Código Equipo *' es obligatoria. Por favor asígnela en el cruce de datos.")
            return

        rows = self._get_mapped_data_rows()
        if not rows:
            QMessageBox.warning(self, "Error", "No hay datos para importar. Asegúrese de que la columna Tag tenga valores.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Importación",
            f"¿Está seguro de que desea importar {len(rows)} equipos a la instalación seleccionada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(rows))
        self.progress_bar.setValue(0)

        imported_count = 0
        error_count = 0

        for idx, r_data in enumerate(rows):
            try:
                tag = r_data.get("tag", "").strip()
                if not tag:
                    continue

                sp_raw = r_data.get("spare_parts", "")
                sp_list = [s.strip() for s in sp_raw.split(',') if s.strip()] if sp_raw else []

                eq = HVACEquipment(
                    id="",
                    client_id=client_id,
                    site_id=site_id,
                    tag=tag,
                    bms_id=r_data.get("bms_id", ""),
                    bms_status=r_data.get("bms_status", "Operativo") or "Operativo",
                    floor_area=r_data.get("floor_area", ""),
                    system_type=r_data.get("system_type", "AHU") or "AHU",
                    manufacturer=r_data.get("manufacturer", ""),
                    model_number=r_data.get("model_number", ""),
                    serial_number=r_data.get("serial_number", ""),
                    installation_date=r_data.get("installation_date", ""),
                    warranty_expiry=r_data.get("warranty_expiry", ""),
                    location_description=r_data.get("location_description", ""),
                    status=r_data.get("status", "OPERATIONAL") or "OPERATIONAL",
                    maintenance_frequency=r_data.get("maintenance_frequency", "MONTHLY") or "MONTHLY",
                    spare_parts=sp_list,
                    notes=r_data.get("notes", "")
                )

                self.equipment_service.save_equipment(eq)
                imported_count += 1
            except Exception as e:
                print(f"Error importing row {idx}: {e}")
                error_count += 1

            self.progress_bar.setValue(idx + 1)

        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self,
            "Importación Finalizada",
            f"Proceso completado exitosamente.\n\n• Equipos importados: {imported_count}\n• Errores: {error_count}"
        )

        if hasattr(self.main_window, '_refresh_current_view'):
            self.main_window._refresh_current_view()

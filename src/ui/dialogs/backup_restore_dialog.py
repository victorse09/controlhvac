"""
Backup and Restore Dialog for ControlHVAC CMMS.

Allows users to:
- Create full backups with embedded backup_manifest.json
- Select from existing backups or browse external ZIP files
- Inspect backup metadata, record counts, and file-by-file comparison (Missing, Modified, Identical)
- Perform Full Restore, Missing/Deleted Files Recovery, or Selective Module/File Restore
- Automatic pre-restore safety snapshot
- Seamless reload of application services and views
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog,
    QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QRadioButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

from src.core.services.backup_service import BackupService, MODULE_LABELS
from src.ui.icon_manager import IconManager


class BackupRestoreDialog(QDialog):
    """Dialog for creating backups and performing smart data restorations."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.storage = main_window.storage
        self.backup_service = BackupService(self.storage)

        self.current_inspection: Optional[Dict[str, Any]] = None
        self.available_backups: List[Dict[str, Any]] = []

        self.setWindowTitle("Gestor de Copias de Seguridad y Restauración de Datos")
        self.resize(1000, 680)
        self.setMinimumSize(880, 580)
        self.setModal(True)

        self.setup_ui()
        self.refresh_backups_list()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ---------------------------------------------------------------------
        # Header
        # ---------------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setObjectName("dialogHeaderBanner")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 10, 14, 10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(IconManager.get_pixmap("settings.svg", "#38BDF8", 32))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        header_layout.addWidget(icon_lbl)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)
        lbl_title = QLabel("Copias de Seguridad y Restauración del Sistema")
        lbl_title.setObjectName("detailTitleLabel")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        lbl_sub = QLabel("Genere respaldos comprimidos (.zip) con manifiesto de datos o restaure archivos perdidos, módulos específicos o el sistema completo.")
        lbl_sub.setObjectName("kvKeyLabel")
        header_text.addWidget(lbl_title)
        header_text.addWidget(lbl_sub)
        header_layout.addLayout(header_text, 1)

        # Quick New Backup Button in Header
        self.btn_new_backup = QPushButton("⚡ Crear Nuevo Respaldo...")
        self.btn_new_backup.setObjectName("primaryButton")
        self.btn_new_backup.setIcon(IconManager.get_icon("save.svg", "#050B14"))
        self.btn_new_backup.clicked.connect(self._create_new_backup_dialog)
        header_layout.addWidget(self.btn_new_backup)

        main_layout.addWidget(header_frame)

        # ---------------------------------------------------------------------
        # Main Body Tabs: (Tab 1: Restaurar Respaldo, Tab 2: Historial de Respaldos)
        # ---------------------------------------------------------------------
        self.tabs = QTabWidget()
        
        # Tab 1: Restore
        self.tab_restore = QWidget()
        self._setup_restore_tab(self.tab_restore)
        self.tabs.addTab(self.tab_restore, IconManager.get_icon("tools.svg", "#FFFFFF"), "Restauración y Recuperación")

        # Tab 2: Backup History
        self.tab_history = QWidget()
        self._setup_history_tab(self.tab_history)
        self.tabs.addTab(self.tab_history, IconManager.get_icon("calendar.svg", "#FFFFFF"), "Historial de Respaldos")

        main_layout.addWidget(self.tabs, 1)

        # ---------------------------------------------------------------------
        # Bottom Buttons
        # ---------------------------------------------------------------------
        bottom_layout = QHBoxLayout()
        self.lbl_global_status = QLabel("")
        self.lbl_global_status.setStyleSheet("color: #38BDF8; font-size: 12px;")
        bottom_layout.addWidget(self.lbl_global_status)
        bottom_layout.addStretch()

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.clicked.connect(self.reject)
        bottom_layout.addWidget(self.btn_close)

        main_layout.addLayout(bottom_layout)

    # -------------------------------------------------------------------------
    # TAB 1: RESTORE TAB SETUP
    # -------------------------------------------------------------------------

    def _setup_restore_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 10, 8, 8)

        # 1. Zip Selection Row
        gb_select = QGroupBox("1. Seleccionar Archivo de Respaldo (.zip)")
        sel_layout = QHBoxLayout(gb_select)
        sel_layout.setSpacing(8)

        self.combo_backups = QComboBox()
        self.combo_backups.setMinimumWidth(360)
        self.combo_backups.currentIndexChanged.connect(self._on_backup_selected_from_combo)
        sel_layout.addWidget(self.combo_backups, 1)

        self.btn_browse_zip = QPushButton("📁 Examinar otro ZIP...")
        self.btn_browse_zip.clicked.connect(self._browse_external_zip)
        sel_layout.addWidget(self.btn_browse_zip)

        self.btn_reload_zip = QPushButton("🔄 Re-inspeccionar")
        self.btn_reload_zip.clicked.connect(self._reinspect_current)
        sel_layout.addWidget(self.btn_reload_zip)

        layout.addWidget(gb_select)

        # 2. Metadata & Comparison Diagnostics Panel
        self.gb_info = QGroupBox("2. Información y Diagnóstico Comparativo del Respaldo")
        info_layout = QVBoxLayout(self.gb_info)
        info_layout.setSpacing(8)

        # Summary Row (Date, files count, status badges)
        self.lbl_manifest_summary = QLabel("Seleccione un archivo de respaldo para visualizar su contenido y diagnóstico comparativo.")
        self.lbl_manifest_summary.setWordWrap(True)
        self.lbl_manifest_summary.setStyleSheet("background-color: #0F172A; padding: 8px 12px; border-radius: 6px; font-size: 12px; color: #F1F5F9;")
        info_layout.addWidget(self.lbl_manifest_summary)

        # Diagnostic badges row
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(10)

        self.badge_missing = QLabel("🔴 0 Faltantes / Borrados")
        self.badge_missing.setStyleSheet("background-color: #450A0A; color: #F87171; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
        
        self.badge_modified = QLabel("🟡 0 Modificados")
        self.badge_modified.setStyleSheet("background-color: #451A03; color: #FBBF24; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
        
        self.badge_identical = QLabel("🟢 0 Idénticos")
        self.badge_identical.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;")

        self.badge_total = QLabel("📦 0 Archivos totales")
        self.badge_total.setStyleSheet("background-color: #1E293B; color: #94A3B8; padding: 4px 10px; border-radius: 4px; font-size: 11px;")

        badges_layout.addWidget(self.badge_missing)
        badges_layout.addWidget(self.badge_modified)
        badges_layout.addWidget(self.badge_identical)
        badges_layout.addWidget(self.badge_total)
        badges_layout.addStretch()
        info_layout.addLayout(badges_layout)

        layout.addWidget(self.gb_info)

        # 3. Restore Mode Group & Selective Tree
        gb_mode = QGroupBox("3. Modo de Restauración")
        mode_layout = QVBoxLayout(gb_mode)
        mode_layout.setSpacing(8)

        self.btn_mode_group = QButtonGroup(self)

        # Radio 1: Full
        self.rb_full = QRadioButton("🔄 Restauración Total (Reemplazo Completo)")
        self.rb_full.setToolTip("Restaura y sobrescribe todos los archivos del sistema con los contenidos en el respaldo.")
        self.btn_mode_group.addButton(self.rb_full, 0)
        mode_layout.addWidget(self.rb_full)

        # Radio 2: Missing only
        self.rb_missing_only = QRadioButton("🩹 Recuperar únicamente Archivos Perdidos o Borrados (Recomendado)")
        self.rb_missing_only.setToolTip("Restaura solo los archivos que existen en el respaldo pero faltan en la carpeta de trabajo. No modifica datos existentes.")
        self.rb_missing_only.setChecked(True)
        self.btn_mode_group.addButton(self.rb_missing_only, 1)
        mode_layout.addWidget(self.rb_missing_only)

        # Radio 3: Selective
        self.rb_selective = QRadioButton("🎯 Restauración Selectiva por Módulos o Archivos Específicos")
        self.btn_mode_group.addButton(self.rb_selective, 2)
        mode_layout.addWidget(self.rb_selective)

        self.btn_mode_group.idClicked.connect(self._on_mode_changed)

        # Selective Container (Tables & filters)
        self.container_selective = QFrame()
        self.container_selective.setStyleSheet("background-color: #0F172A; border-radius: 6px; padding: 6px;")
        sel_inner_layout = QVBoxLayout(self.container_selective)
        sel_inner_layout.setSpacing(6)
        sel_inner_layout.setContentsMargins(4, 4, 4, 4)

        # Module quick checkboxes
        mod_quick_layout = QHBoxLayout()
        mod_quick_layout.setSpacing(8)
        lbl_m = QLabel("Módulos a restaurar:")
        lbl_m.setStyleSheet("font-weight: bold; color: #CBD5E1; font-size: 11px;")
        mod_quick_layout.addWidget(lbl_m)

        self.chk_modules: Dict[str, QCheckBox] = {}
        for mod_key in ["clients", "equipment", "incidents", "work_orders", "technicians", "library", "inventory", "maintenance_schedules"]:
            chk = QCheckBox(MODULE_LABELS.get(mod_key, mod_key).split(" ")[0] + " " + mod_key.capitalize())
            chk.setChecked(True)
            chk.stateChanged.connect(self._on_module_check_changed)
            self.chk_modules[mod_key] = chk
            mod_quick_layout.addWidget(chk)
        mod_quick_layout.addStretch()
        sel_inner_layout.addLayout(mod_quick_layout)

        # Files Table
        filter_row = QHBoxLayout()
        self.txt_filter_files = QLineEdit()
        self.txt_filter_files.setPlaceholderText("🔍 Filtrar archivos por nombre, módulo o estado...")
        self.txt_filter_files.textChanged.connect(self._filter_files_table)
        filter_row.addWidget(self.txt_filter_files, 1)

        self.chk_overwrite_selective = QCheckBox("Sobrescribir si el archivo ya existe")
        self.chk_overwrite_selective.setChecked(True)
        filter_row.addWidget(self.chk_overwrite_selective)

        self.btn_select_all = QPushButton("Marcar Todos")
        self.btn_select_all.clicked.connect(lambda: self._set_all_files_checked(True))
        filter_row.addWidget(self.btn_select_all)

        self.btn_unselect_all = QPushButton("Desmarcar Todos")
        self.btn_unselect_all.clicked.connect(lambda: self._set_all_files_checked(False))
        filter_row.addWidget(self.btn_unselect_all)

        sel_inner_layout.addLayout(filter_row)

        self.table_files = QTableWidget()
        self.table_files.verticalHeader().setVisible(False)
        self.table_files.setColumnCount(5)
        self.table_files.setHorizontalHeaderLabels(["[x]", "Ruta de Archivo", "Módulo", "Tamaño", "Estado Diagnóstico"])
        self.table_files.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_files.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_files.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_files.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_files.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_files.setAlternatingRowColors(True)
        self.table_files.setStyleSheet("QTableWidget { background-color: #1E293B; }")
        self.table_files.setMaximumHeight(180)
        sel_inner_layout.addWidget(self.table_files)

        mode_layout.addWidget(self.container_selective)
        self.container_selective.setVisible(False)

        layout.addWidget(gb_mode)

        # 4. Safety and Execution Row
        exec_layout = QHBoxLayout()
        exec_layout.setSpacing(12)

        self.chk_safety_snapshot = QCheckBox("🛡️ Crear automáticamente un Snapshot de seguridad previo a la restauración")
        self.chk_safety_snapshot.setChecked(True)
        self.chk_safety_snapshot.setStyleSheet("color: #38BDF8; font-weight: bold;")
        exec_layout.addWidget(self.chk_safety_snapshot)

        exec_layout.addStretch()

        self.btn_restore = QPushButton("🚀 Iniciar Restauración de Datos")
        self.btn_restore.setObjectName("primaryButton")
        self.btn_restore.setIcon(IconManager.get_icon("check.svg", "#FFFFFF"))
        self.btn_restore.setStyleSheet("background-color: #059669; font-weight: bold; font-size: 13px; padding: 8px 16px;")
        self.btn_restore.clicked.connect(self._execute_restoration)
        exec_layout.addWidget(self.btn_restore)

        layout.addLayout(exec_layout)

    # -------------------------------------------------------------------------
    # TAB 2: HISTORY TAB SETUP
    # -------------------------------------------------------------------------

    def _setup_history_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_info = QLabel("Listado de copias de seguridad encontradas en la carpeta de respaldos:")
        lbl_info.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(lbl_info)

        self.table_history = QTableWidget()
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["Nombre de Archivo", "Fecha Creación", "Tamaño (MB)", "Comentarios / Contenido", "Acciones"])
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.setAlternatingRowColors(True)
        layout.addWidget(self.table_history, 1)

        hist_btn_row = QHBoxLayout()
        btn_open_backups_folder = QPushButton("📂 Abrir Carpeta de Respaldos en el Explorador")
        btn_open_backups_folder.clicked.connect(self._open_backups_dir)
        hist_btn_row.addWidget(btn_open_backups_folder)

        hist_btn_row.addStretch()

        btn_refresh_hist = QPushButton("🔄 Actualizar Historial")
        btn_refresh_hist.clicked.connect(self.refresh_backups_list)
        hist_btn_row.addWidget(btn_refresh_hist)

        layout.addLayout(hist_btn_row)

    # -------------------------------------------------------------------------
    # DATA LOADING & INSPECTION
    # -------------------------------------------------------------------------

    def refresh_backups_list(self):
        """Scan backups directory and populate combo and history table."""
        self.available_backups = self.backup_service.list_available_backups()

        # Update Combo in Tab 1
        self.combo_backups.blockSignals(True)
        self.combo_backups.clear()

        if not self.available_backups:
            self.combo_backups.addItem("No se encontraron respaldos en la carpeta oficial", "")
            self.btn_restore.setEnabled(False)
        else:
            self.btn_restore.setEnabled(True)
            for b in self.available_backups:
                label = f"{b['filename']} ({b['size_mb']} MB - {b['created_at']})"
                self.combo_backups.addItem(label, b["path"])

        self.combo_backups.blockSignals(False)

        # Update History Table in Tab 2
        self.table_history.setRowCount(len(self.available_backups))
        for row, b in enumerate(self.available_backups):
            self.table_history.setItem(row, 0, QTableWidgetItem(b["filename"]))
            self.table_history.setItem(row, 1, QTableWidgetItem(b["created_at"]))
            self.table_history.setItem(row, 2, QTableWidgetItem(str(b["size_mb"])))
            
            # Format summary / comments
            sum_dict = b.get("summary", {})
            parts = []
            if sum_dict.get("equipment"):
                parts.append(f"Equipos: {sum_dict['equipment']}")
            if sum_dict.get("incidents"):
                parts.append(f"Averías: {sum_dict['incidents']}")
            if sum_dict.get("work_orders"):
                parts.append(f"OTs: {sum_dict['work_orders']}")
            if sum_dict.get("technicians"):
                parts.append(f"Técnicos: {sum_dict['technicians']}")
            if sum_dict.get("library"):
                parts.append(f"Docs: {sum_dict['library']}")
            
            desc_text = " | ".join(parts)
            if b.get("comments"):
                desc_text = f"[{b['comments']}] " + desc_text

            self.table_history.setItem(row, 3, QTableWidgetItem(desc_text or "Respaldo estándar"))

            btn_load = QPushButton("Seleccionar")
            btn_load.clicked.connect(lambda _, p=b["path"]: self._select_path_and_switch(p))
            self.table_history.setCellWidget(row, 4, btn_load)

        # Inspect first backup if available
        if self.available_backups:
            self._inspect_zip(self.available_backups[0]["path"])
        else:
            self._clear_inspection()

    def _select_path_and_switch(self, zip_path: str):
        self._inspect_zip(zip_path)
        self.tabs.setCurrentIndex(0)

    def _on_backup_selected_from_combo(self):
        zip_path = self.combo_backups.currentData()
        if zip_path and os.path.exists(zip_path):
            self._inspect_zip(zip_path)

    def _browse_external_zip(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Respaldo ZIP",
            self.backup_service.backups_dir,
            "Archivos ZIP (*.zip)"
        )
        if file_path:
            # Add to combo if not present and inspect
            self.combo_backups.blockSignals(True)
            self.combo_backups.insertItem(0, f"📁 {os.path.basename(file_path)} (Externo)", file_path)
            self.combo_backups.setCurrentIndex(0)
            self.combo_backups.blockSignals(False)
            self._inspect_zip(file_path)

    def _reinspect_current(self):
        zip_path = self.combo_backups.currentData()
        if zip_path and os.path.exists(zip_path):
            self._inspect_zip(zip_path)

    def _clear_inspection(self):
        self.current_inspection = None
        self.lbl_manifest_summary.setText("No hay ningún archivo de respaldo cargado.")
        self.badge_missing.setText("🔴 0 Faltantes / Borrados")
        self.badge_modified.setText("🟡 0 Modificados")
        self.badge_identical.setText("🟢 0 Idénticos")
        self.badge_total.setText("📦 0 Archivos totales")
        self.table_files.setRowCount(0)
        self.btn_restore.setEnabled(False)

    def _inspect_zip(self, zip_path: str):
        try:
            self.current_inspection = self.backup_service.inspect_backup_archive(zip_path)
            m = self.current_inspection["manifest"]
            counts = self.current_inspection["status_counts"]
            summary = m.get("summary", {})

            # Build rich summary html
            date_str = m.get("created_at_local", m.get("created_at", "Desconocida"))
            comments_str = f"<br><b>Nota:</b> {m.get('comments')}" if m.get('comments') else ""
            
            rec_parts = []
            if summary.get("clients"): rec_parts.append(f"🏢 Clientes: <b>{summary['clients']}</b>")
            if summary.get("equipment"): rec_parts.append(f"❄️ Equipos: <b>{summary['equipment']}</b>")
            if summary.get("incidents"): rec_parts.append(f"🚨 Averías: <b>{summary['incidents']}</b>")
            if summary.get("work_orders"): rec_parts.append(f"📋 OTs/Guías: <b>{summary['work_orders']}</b>")
            if summary.get("technicians"): rec_parts.append(f"👷 Técnicos: <b>{summary['technicians']}</b>")
            if summary.get("library"): rec_parts.append(f"📚 Docs/Planos: <b>{summary['library']}</b>")
            if summary.get("inventory"): rec_parts.append(f"🔧 Repuestos/Herramientas: <b>{summary['inventory']}</b>")

            rec_html = " &nbsp;|&nbsp; ".join(rec_parts) if rec_parts else "Estructura de archivos estándar"

            html = f"""
            <b>Archivo:</b> {os.path.basename(zip_path)} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha Respaldo:</b> {date_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Versión Manifest:</b> {m.get('backup_version', '2.0')}
            <br><b>Registros en el respaldo:</b> {rec_html}{comments_str}
            """
            self.lbl_manifest_summary.setText(html)

            # Update badges
            self.badge_missing.setText(f"🔴 {counts['MISSING']} Faltantes / Borrados")
            self.badge_modified.setText(f"🟡 {counts['MODIFIED']} Modificados")
            self.badge_identical.setText(f"🟢 {counts['IDENTICAL']} Idénticos")
            self.badge_total.setText(f"📦 {len(self.current_inspection['files'])} Archivos totales")

            # Update files table
            self._populate_files_table(self.current_inspection["files"])
            self.btn_restore.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error al Inspeccionar Respaldo", f"No se pudo leer el archivo ZIP:\n\n{e}")
            self._clear_inspection()

    def _populate_files_table(self, files: List[Dict[str, Any]]):
        self.table_files.setRowCount(len(files))
        for row, f_info in enumerate(files):
            # Column 0: Checkbox
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked)
            self.table_files.setItem(row, 0, chk_item)

            # Column 1: Path
            p_item = QTableWidgetItem(f_info["path"])
            self.table_files.setItem(row, 1, p_item)

            # Column 2: Module
            m_item = QTableWidgetItem(f_info.get("module_label", f_info.get("module", "")))
            self.table_files.setItem(row, 2, m_item)

            # Column 3: Size
            sz_kb = round(f_info["size"] / 1024, 1)
            sz_item = QTableWidgetItem(f"{sz_kb} KB" if sz_kb > 0 else f"{f_info['size']} B")
            self.table_files.setItem(row, 3, sz_item)

            # Column 4: Status badge
            st = f_info["status"]
            st_item = QTableWidgetItem()
            if st == "MISSING":
                st_item.setText("🔴 Faltante / Borrado")
                st_item.setForeground(QColor("#F87171"))
            elif st == "MODIFIED":
                st_item.setText("🟡 Modificado")
                st_item.setForeground(QColor("#FBBF24"))
            else:
                st_item.setText("🟢 Idéntico")
                st_item.setForeground(QColor("#34D399"))
            self.table_files.setItem(row, 4, st_item)

    def _filter_files_table(self, query: str):
        query = query.lower().strip()
        for row in range(self.table_files.rowCount()):
            path = self.table_files.item(row, 1).text().lower()
            mod = self.table_files.item(row, 2).text().lower()
            status = self.table_files.item(row, 4).text().lower()
            match = not query or query in path or query in mod or query in status
            self.table_files.setRowHidden(row, not match)

    def _set_all_files_checked(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.table_files.rowCount()):
            if not self.table_files.isRowHidden(row):
                item = self.table_files.item(row, 0)
                if item:
                    item.setCheckState(state)

    def _on_module_check_changed(self):
        active_modules = {k for k, chk in self.chk_modules.items() if chk.isChecked()}
        for row in range(self.table_files.rowCount()):
            if self.current_inspection and row < len(self.current_inspection["files"]):
                f_info = self.current_inspection["files"][row]
                mod = f_info.get("module", "")
                item = self.table_files.item(row, 0)
                if item:
                    item.setCheckState(Qt.CheckState.Checked if mod in active_modules else Qt.CheckState.Unchecked)

    def _on_mode_changed(self, btn_id: int):
        self.container_selective.setVisible(self.rb_selective.isChecked())

    # -------------------------------------------------------------------------
    # RESTORATION EXECUTION
    # -------------------------------------------------------------------------

    def _execute_restoration(self):
        if not self.current_inspection:
            QMessageBox.warning(self, "Restauración", "No hay un archivo de respaldo seleccionado.")
            return

        zip_path = self.current_inspection["zip_path"]
        
        # Determine mode
        if self.rb_full.isChecked():
            mode = "FULL"
            mode_desc = "Restauración Total (Reemplaza todos los datos actuales)"
            selected_files = None
        elif self.rb_missing_only.isChecked():
            mode = "MISSING_ONLY"
            missing_count = self.current_inspection["status_counts"]["MISSING"]
            if missing_count == 0:
                QMessageBox.information(
                    self,
                    "Sin Archivos Faltantes",
                    "No se detectaron archivos borrados o faltantes en el sistema actual respecto a esta copia de seguridad."
                )
                return
            mode_desc = f"Recuperación de Archivos Perdidos/Borrados ({missing_count} archivos a recuperar)"
            selected_files = None
        else:
            mode = "SELECTIVE"
            # Gather checked files
            selected_files = set()
            for row in range(self.table_files.rowCount()):
                item = self.table_files.item(row, 0)
                if item and item.checkState() == Qt.CheckState.Checked:
                    selected_files.add(self.table_files.item(row, 1).text())

            if not selected_files:
                QMessageBox.warning(self, "Restauración Selectiva", "Debe marcar al menos un archivo o módulo para restaurar.")
                return

            mode_desc = f"Restauración Selectiva ({len(selected_files)} archivos seleccionados)"

        # Confirmation Dialog
        snapshot_msg = "\n\n🛡️ Se generará automáticamente un Snapshot de seguridad preventivo antes de restaurar." if self.chk_safety_snapshot.isChecked() else ""
        res = QMessageBox.question(
            self,
            "Confirmar Restauración de Datos",
            f"¿Está seguro de proceder con la siguiente restauración?\n\n"
            f"• Archivo: {os.path.basename(zip_path)}\n"
            f"• Modalidad: {mode_desc}{snapshot_msg}\n\n"
            f"La aplicación recargará automáticamente la base de datos una vez finalizado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        try:
            result = self.backup_service.restore_backup(
                zip_path=zip_path,
                restore_mode=mode,
                selected_files=selected_files,
                overwrite_existing=self.chk_overwrite_selective.isChecked() if mode == "SELECTIVE" else True,
                create_safety_snapshot=self.chk_safety_snapshot.isChecked()
            )

            if not result.get("success"):
                err_text = "\n".join(result.get("errors", []))
                QMessageBox.critical(self, "Errores durante la Restauración", f"Ocurrieron errores al restaurar:\n\n{err_text}")
                return

            # Success message
            snap_text = f"\n\n🛡️ Snapshot preventivo guardado en:\n{result.get('safety_snapshot')}" if result.get('safety_snapshot') else ""
            QMessageBox.information(
                self,
                "Restauración Completada",
                f"¡La restauración se completó exitosamente!\n\n"
                f"• Archivos restaurados/recuperados: {result.get('restored_count', 0)}\n"
                f"• Archivos omitidos/conservados: {result.get('skipped_count', 0)}{snap_text}"
            )

            # Reload MainWindow services, views, and restored company logo seamlessly
            if hasattr(self.main_window, '_initialize_services') and hasattr(self.main_window, '_create_views'):
                self.main_window._initialize_services()
                self.main_window._create_views()
                active_sec = getattr(self.main_window.sidebar, "active_section", None) or "dashboard"
                self.main_window._switch_view(active_sec)
            if hasattr(self.main_window, 'sidebar') and hasattr(self.main_window, 'state_manager'):
                self.main_window.sidebar.update_logo(self.main_window.state_manager.get_logo_path())

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error de Restauración", f"No se pudo completar el proceso de restauración:\n\n{e}")

    # -------------------------------------------------------------------------
    # NEW BACKUP DIALOG
    # -------------------------------------------------------------------------

    def _create_new_backup_dialog(self):
        """Prompt user for destination, optional comment and create a new ZIP backup with manifest."""
        now_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"backup_ControlHVAC_{now_tag}.zip"
        default_path = os.path.join(self.backup_service.backups_dir, default_filename)

        comment_dialog = QDialog(self)
        comment_dialog.setWindowTitle("Crear Nueva Copia de Seguridad")
        comment_dialog.resize(520, 290)
        c_layout = QVBoxLayout(comment_dialog)
        c_layout.setSpacing(10)

        # 1. Destination Path
        lbl_dest = QLabel("Ubicación y nombre del archivo de respaldo (.zip):")
        lbl_dest.setStyleSheet("font-weight: bold; color: #F8FAFC;")
        c_layout.addWidget(lbl_dest)

        dest_row = QHBoxLayout()
        txt_dest = QLineEdit(default_path)
        dest_row.addWidget(txt_dest, 1)

        def _browse_save_dest():
            f_path, _ = QFileDialog.getSaveFileName(
                comment_dialog,
                "Seleccionar dónde guardar el respaldo ZIP",
                txt_dest.text() or default_path,
                "Archivos ZIP (*.zip)"
            )
            if f_path:
                txt_dest.setText(f_path)

        btn_browse_dest = QPushButton("📁 Examinar...")
        btn_browse_dest.clicked.connect(_browse_save_dest)
        dest_row.addWidget(btn_browse_dest)
        c_layout.addLayout(dest_row)

        # 2. Description / Comment
        lbl_com = QLabel("Descripción o comentario para este respaldo (opcional):")
        c_layout.addWidget(lbl_com)

        txt_comment = QTextEdit()
        txt_comment.setPlaceholderText("Ej: Respaldo antes de mantención mayor en Torre A...")
        txt_comment.setMaximumHeight(70)
        c_layout.addWidget(txt_comment)

        # 3. Checkbox Photos
        chk_photos = QCheckBox("Incluir carpeta de fotos / evidencias")
        chk_photos.setChecked(True)
        c_layout.addWidget(chk_photos)

        # Buttons
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(comment_dialog.reject)
        btn_box.addWidget(btn_cancel)
        btn_box.addStretch()

        btn_ok = QPushButton("Generar Respaldo ZIP")
        btn_ok.setObjectName("primaryButton")
        btn_ok.clicked.connect(comment_dialog.accept)
        btn_box.addWidget(btn_ok)
        c_layout.addLayout(btn_box)

        if comment_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        target_zip = txt_dest.text().strip()
        if not target_zip:
            target_zip = default_path

        try:
            res = self.backup_service.create_backup(
                output_zip_path=target_zip,
                comments=txt_comment.toPlainText().strip(),
                include_photos=chk_photos.isChecked()
            )
            QMessageBox.information(
                self,
                "Copia de Seguridad Exitosa",
                f"La copia de seguridad se generó correctamente con su manifiesto de datos en:\n\n{res['zip_path']}"
            )
            self.refresh_backups_list()
        except Exception as e:
            QMessageBox.critical(self, "Error al Crear Respaldo", f"No se pudo generar la copia de seguridad:\n\n{e}")

    def _open_backups_dir(self):
        b_dir = self.backup_service.backups_dir
        if os.path.exists(b_dir):
            import subprocess
            if os.name == 'nt':
                os.startfile(b_dir)
            else:
                subprocess.Popen(['xdg-open', b_dir])

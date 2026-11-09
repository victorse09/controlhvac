import os
import shutil
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QGroupBox, QMessageBox, QFileDialog,
    QComboBox, QApplication, QTabWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QCursor

from src.ui.theme import THEME_LABELS, apply_theme
from src.ui.dialogs.excel_import_dialog import ExcelImportWidget
from src.ui.dialogs.custom_lists_widget import CustomListsWidget
from src.ui.dialogs.bulk_equipment_widget import BulkEquipmentWidget, _create_section_card
from src.ui.icon_manager import IconManager

class SettingsDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.config = main_window.config
        self.state_manager = main_window.state_manager
        self.storage = getattr(main_window, 'storage', None)
        
        self.setWindowTitle("Configuración del Sistema")
        self.resize(980, 760)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

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
        lbl_icon.setPixmap(IconManager.get_icon("settings.svg", "#38BDF8", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(3)
        lbl_title = QLabel("Configuración y Administración del Sistema")
        lbl_title.setObjectName("detailTitleLabel")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        lbl_sub = QLabel("Edición masiva de equipos, listas desplegables, importación Excel, apariencia, respaldos y papelera")
        lbl_sub.setObjectName("kvKeyLabel")
        lbl_sub.setStyleSheet("font-size: 11.5px; background: transparent;")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_sub)
        hb_layout.addLayout(title_col, 1)

        theme_pill = QFrame()
        theme_pill.setObjectName("eqStatusBanner")
        tp_l = QVBoxLayout(theme_pill)
        tp_l.setContentsMargins(12, 5, 12, 5)
        tp_l.setSpacing(1)
        lbl_tp_cap = QLabel("TEMA ACTIVO")
        lbl_tp_cap.setObjectName("kvKeyLabel")
        lbl_tp_cap.setStyleSheet("font-size: 9px; letter-spacing: 0.5px; background: transparent;")
        self.lbl_active_theme_badge = QLabel(f"●  {THEME_LABELS.get(self.state_manager.get_theme(), 'Tema del Sistema')}")
        self.lbl_active_theme_badge.setStyleSheet("color: #38BDF8; font-size: 11.5px; font-weight: 700; background: transparent;")
        tp_l.addWidget(lbl_tp_cap)
        tp_l.addWidget(self.lbl_active_theme_badge)
        hb_layout.addWidget(theme_pill)

        layout.addWidget(header_banner)

        # Tab Widget
        self.tabs = QTabWidget()
        
        # --- TAB 1: Edición Masiva de Equipos ---
        self.tab_bulk = QWidget()
        tab_bulk_layout = QVBoxLayout(self.tab_bulk)
        tab_bulk_layout.setContentsMargins(6, 6, 6, 6)
        
        self.bulk_equipment_widget = BulkEquipmentWidget(self.main_window, parent=self.tab_bulk)
        tab_bulk_layout.addWidget(self.bulk_equipment_widget)
        self.tabs.addTab(self.tab_bulk, IconManager.get_icon("edit.svg", "#38BDF8"), "Edición Masiva")

        # --- TAB 2: Listas Desplegables ---
        self.tab_lists = QWidget()
        tab_lists_layout = QVBoxLayout(self.tab_lists)
        tab_lists_layout.setContentsMargins(6, 6, 6, 6)
        
        self.custom_lists_widget = CustomListsWidget(self.main_window, parent=self.tab_lists)
        tab_lists_layout.addWidget(self.custom_lists_widget)
        self.tabs.addTab(self.tab_lists, IconManager.get_icon("equipment.svg", "#F59E0B"), "Listas Desplegables")

        # --- TAB 3: Importar Equipos desde Excel ---
        self.tab_import = QWidget()
        tab_import_layout = QVBoxLayout(self.tab_import)
        tab_import_layout.setContentsMargins(6, 6, 6, 6)
        
        self.excel_import_widget = ExcelImportWidget(self.main_window, parent=self.tab_import)
        tab_import_layout.addWidget(self.excel_import_widget)
        self.tabs.addTab(self.tab_import, IconManager.get_icon("excel.svg", "#10B981"), "Importar Equipos (Excel)")

        # --- TAB 4: Apariencia y Sistema ---
        self.tab_general = QWidget()
        tab_gen_scroll = QScrollArea()
        tab_gen_scroll.setWidgetResizable(True)
        tab_gen_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        gen_content = QWidget()
        gen_content.setObjectName("scrollContent")
        gen_layout = QVBoxLayout(gen_content)
        gen_layout.setSpacing(14)
        gen_layout.setContentsMargins(12, 12, 12, 12)

        # Logo Group
        card_logo, gb_logo = _create_section_card("Logotipo de la Empresa", "#38BDF8")
        logo_layout = QVBoxLayout(gb_logo)
        logo_layout.setContentsMargins(14, 12, 14, 12)
        logo_layout.setSpacing(10)
        
        lbl_logo_info = QLabel("Cargue el logotipo de su empresa. Este se mostrará en la barra lateral y en los documentos PDF de averías:")
        lbl_logo_info.setObjectName("kvKeyLabel")
        lbl_logo_info.setWordWrap(True)
        logo_layout.addWidget(lbl_logo_info)
        
        preview_box = QHBoxLayout()
        self.lbl_logo_preview = QLabel()
        self.lbl_logo_preview.setFixedSize(220, 75)
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_preview.setObjectName("eqStatusBanner")
        preview_box.addWidget(self.lbl_logo_preview)
        
        logo_btn_layout = QVBoxLayout()
        btn_upload_logo = QPushButton("Subir / Seleccionar Logo...")
        btn_upload_logo.setObjectName("primaryButton")
        btn_upload_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_upload_logo.clicked.connect(self._upload_logo)
        logo_btn_layout.addWidget(btn_upload_logo)
        
        btn_remove_logo = QPushButton("Quitar Logo")
        btn_remove_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_remove_logo.clicked.connect(self._remove_logo)
        logo_btn_layout.addWidget(btn_remove_logo)
        logo_btn_layout.addStretch()
        
        preview_box.addLayout(logo_btn_layout)
        preview_box.addStretch()
        logo_layout.addLayout(preview_box)
        gen_layout.addWidget(card_logo)
        
        self._update_logo_preview()

        # Theme Group
        card_theme, gb_theme = _create_section_card("Entorno de Color y Apariencia", "#8B5CF6")
        theme_layout = QVBoxLayout(gb_theme)
        theme_layout.setContentsMargins(14, 12, 14, 12)
        theme_layout.setSpacing(10)
        
        lbl_theme_info = QLabel("Seleccione el entorno de color para personalizar la apariencia de la aplicación:")
        lbl_theme_info.setObjectName("kvKeyLabel")
        theme_layout.addWidget(lbl_theme_info)
        
        self.combo_theme = QComboBox()
        current_theme = self.state_manager.get_theme()
        
        for key, label in THEME_LABELS.items():
            self.combo_theme.addItem(label, key)
            
        idx = self.combo_theme.findData(current_theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
            
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.combo_theme)
        gen_layout.addWidget(card_theme)

        # Data Folder Group
        card_folder, gb_folder = _create_section_card("Carpeta de Datos del Sistema", "#F59E0B")
        folder_layout = QVBoxLayout(gb_folder)
        folder_layout.setContentsMargins(14, 12, 14, 12)
        folder_layout.setSpacing(10)
        
        lbl_info = QLabel("Ubicación donde se guardan los datos de clientes, equipos y órdenes:")
        lbl_info.setObjectName("kvKeyLabel")
        folder_layout.addWidget(lbl_info)
        
        self.lbl_path = QLabel(self.config.data_dir or "No seleccionada")
        self.lbl_path.setObjectName("eqStatusBanner")
        self.lbl_path.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px; padding: 8px 12px; border-radius: 6px;")
        self.lbl_path.setWordWrap(True)
        folder_layout.addWidget(self.lbl_path)
        
        btn_folder = QPushButton("Cambiar Carpeta de Datos...")
        btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_folder.clicked.connect(self._change_folder)
        folder_layout.addWidget(btn_folder, alignment=Qt.AlignmentFlag.AlignRight)
        gen_layout.addWidget(card_folder)

        # Backup Group
        card_backup, gb_backup = _create_section_card("Copias de Seguridad y Restauración", "#10B981")
        backup_layout = QVBoxLayout(gb_backup)
        backup_layout.setContentsMargins(14, 12, 14, 12)
        backup_layout.setSpacing(10)
        
        lbl_backup_info = QLabel("Genere respaldos comprimidos (.zip) con manifiesto JSON de integridad o restaure archivos perdidos/borrados, módulos particulares o el sistema completo:")
        lbl_backup_info.setObjectName("kvKeyLabel")
        lbl_backup_info.setWordWrap(True)
        backup_layout.addWidget(lbl_backup_info)
        
        btn_row_backup = QHBoxLayout()
        btn_open_restore = QPushButton("🛡️ Abrir Administrador de Respaldos y Restauración...")
        btn_open_restore.setObjectName("primaryButton")
        btn_open_restore.setIcon(IconManager.get_icon("settings.svg", "#000000"))
        btn_open_restore.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_open_restore.clicked.connect(self._open_backup_restore_dialog)
        btn_row_backup.addWidget(btn_open_restore)

        btn_backup = QPushButton("⚡ Crear Respaldo Rápido Ahora")
        btn_backup.setIcon(IconManager.get_icon("save.svg", "#38BDF8"))
        btn_backup.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_backup.clicked.connect(self._make_backup)
        btn_row_backup.addWidget(btn_backup)
        
        backup_layout.addLayout(btn_row_backup)
        gen_layout.addWidget(card_backup)

        # System info Group
        card_sys, gb_sys = _create_section_card("Información del Sistema", "#14B8A6")
        sys_layout = QFormLayout(gb_sys)
        sys_layout.setContentsMargins(14, 12, 14, 12)
        sys_layout.addRow("Aplicación:", QLabel("ControlHVAC - CMMS Climatización"))
        sys_layout.addRow("Versión:", QLabel("v1.0.0"))
        gen_layout.addWidget(card_sys)
        gen_layout.addStretch()

        tab_gen_scroll.setWidget(gen_content)
        tab_gen_layout = QVBoxLayout(self.tab_general)
        tab_gen_layout.setContentsMargins(0, 0, 0, 0)
        tab_gen_layout.addWidget(tab_gen_scroll)
        self.tabs.addTab(self.tab_general, IconManager.get_icon("settings.svg", "#8B5CF6"), "Apariencia y Sistema")

        # --- TAB 5: Papelera de Reciclaje ---
        self.tab_recycle = QWidget()
        rec_layout = QVBoxLayout(self.tab_recycle)
        rec_layout.setContentsMargins(12, 12, 12, 12)
        
        card_recycle, gb_recycle = _create_section_card("Papelera de Reciclaje del Sistema", "#EF4444")
        rec_inner_layout = QVBoxLayout(gb_recycle)
        rec_inner_layout.setContentsMargins(14, 14, 14, 14)
        rec_inner_layout.setSpacing(12)
        
        lbl_recycle_info = QLabel("Acceda a la Papelera de Reciclaje para recuperar o eliminar definitivamente elementos del sistema:")
        lbl_recycle_info.setObjectName("kvKeyLabel")
        rec_inner_layout.addWidget(lbl_recycle_info)
        
        btn_recycle = QPushButton("  Abrir Ventana de Papelera de Reciclaje...")
        btn_recycle.setObjectName("primaryButton")
        btn_recycle.setMinimumHeight(36)
        btn_recycle.setMinimumWidth(310)
        btn_recycle.setIcon(IconManager.get_icon("delete.svg", "#050B14"))
        btn_recycle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_recycle.clicked.connect(self._open_recycle_bin)
        rec_inner_layout.addWidget(btn_recycle, alignment=Qt.AlignmentFlag.AlignLeft)
        rec_inner_layout.addStretch()
        
        rec_layout.addWidget(card_recycle)
        rec_layout.addStretch()
        self.tabs.addTab(self.tab_recycle, IconManager.get_icon("delete.svg", "#EF4444"), "Papelera de Reciclaje")

        layout.addWidget(self.tabs, 1)

        # Footer Bar
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        footer_layout = QHBoxLayout(footer_bar)
        footer_layout.setContentsMargins(12, 10, 12, 10)
        lbl_footer_note = QLabel("●  Los cambios en listas desplegables, edición masiva y apariencia se guardan automáticamente")
        lbl_footer_note.setObjectName("kvKeyLabel")
        lbl_footer_note.setStyleSheet("font-size: 11px; background: transparent;")
        footer_layout.addWidget(lbl_footer_note)
        footer_layout.addStretch()

        btn_close = QPushButton("  Cerrar Configuración")
        btn_close.setObjectName("primaryButton")
        btn_close.setMinimumWidth(160)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)
        layout.addWidget(footer_bar)

    def _update_logo_preview(self):
        logo_path = self.state_manager.get_logo_path()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 65, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo_preview.setPixmap(scaled)
                return
        self.lbl_logo_preview.setPixmap(QPixmap())
        self.lbl_logo_preview.setText("Sin Logotipo Configurado")

    def _upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen del Logotipo",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)"
        )
        if not file_path:
            return

        try:
            # Always store the logo inside the workspace data directory (config/company_logo.<ext>)
            target_path = file_path
            if self.config.is_data_dir_set:
                logo_dir = self.config.workspace_config_dir
                os.makedirs(logo_dir, exist_ok=True)
                # Remove any previous company_logo.* files in config/ and root data_dir
                for cleanup_dir in (logo_dir, self.config.data_dir):
                    if os.path.isdir(cleanup_dir):
                        for f in os.listdir(cleanup_dir):
                            if f.lower().startswith("company_logo"):
                                try:
                                    os.remove(os.path.join(cleanup_dir, f))
                                except OSError:
                                    pass
                ext = os.path.splitext(file_path)[1].lower() or ".png"
                target_path = os.path.join(logo_dir, f"company_logo{ext}")
                if os.path.abspath(file_path) != os.path.abspath(target_path):
                    shutil.copy2(file_path, target_path)

            self.state_manager.set_logo_path(target_path)
            self._update_logo_preview()
            if hasattr(self.main_window, 'sidebar'):
                self.main_window.sidebar.update_logo(target_path)

            QMessageBox.information(self, "Logotipo Actualizado", "El logotipo se ha guardado en la carpeta de trabajo y aplicado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la imagen del logotipo: {e}")

    def _remove_logo(self):
        if self.config.is_data_dir_set:
            for cleanup_dir in (self.config.workspace_config_dir, self.config.data_dir):
                if os.path.isdir(cleanup_dir):
                    for f in os.listdir(cleanup_dir):
                        if f.lower().startswith("company_logo"):
                            try:
                                os.remove(os.path.join(cleanup_dir, f))
                            except OSError:
                                pass
        self.state_manager.set_logo_path("")
        self._update_logo_preview()
        if hasattr(self.main_window, 'sidebar'):
            self.main_window.sidebar.update_logo("")
        QMessageBox.information(self, "Logotipo Eliminado", "Se ha removido el logotipo de la configuración y de la carpeta de trabajo.")

    def _on_theme_changed(self):
        theme_key = self.combo_theme.currentData()
        if theme_key:
            self.state_manager.set_theme(theme_key)
            if hasattr(self, "lbl_active_theme_badge"):
                self.lbl_active_theme_badge.setText(f"●  {THEME_LABELS.get(theme_key, theme_key)}")
            app = QApplication.instance()
            if app:
                apply_theme(app, theme_key)
            if hasattr(self, "main_window") and hasattr(self.main_window, "views"):
                for view in self.main_window.views.values():
                    if hasattr(view, "tree") and view.tree.viewport():
                        view.tree.viewport().update()
                    if hasattr(view, "table") and view.table.viewport():
                        view.table.viewport().update()

    def _open_recycle_bin(self):
        from src.ui.dialogs.recycle_bin_dialog import RecycleBinDialog
        dialog = RecycleBinDialog(self.main_window, parent=self)
        dialog.exec()

    def _open_backup_restore_dialog(self):
        from src.ui.dialogs.backup_restore_dialog import BackupRestoreDialog
        dialog = BackupRestoreDialog(self.main_window, parent=self)
        dialog.exec()
        self._update_logo_preview()

    def _change_folder(self):
        self.main_window._select_data_folder()
        self.lbl_path.setText(self.config.data_dir or "No seleccionada")
        self._update_logo_preview()

    def _make_backup(self):
        if not self.config.data_dir or not os.path.exists(self.config.data_dir):
            QMessageBox.warning(self, "Error", "No hay una carpeta de datos válida seleccionada.")
            return

        now_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"backup_ControlHVAC_{now_tag}.zip"
        default_path = os.path.join(self.config.backups_dir, default_filename)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Copia de Seguridad en...",
            default_path,
            "Archivos ZIP (*.zip)"
        )
        if not file_path:
            return

        try:
            from src.core.services.backup_service import BackupService
            from src.data.json_storage import JsonStorageEngine

            storage = getattr(self, 'storage', None) or getattr(self.main_window, 'storage', None)
            if not storage:
                storage = JsonStorageEngine(self.config.data_dir)
            self.storage = storage

            backup_svc = BackupService(storage)
            res = backup_svc.create_backup(
                output_zip_path=file_path,
                comments="Respaldo rápido desde Configuración"
            )
            
            QMessageBox.information(
                self, 
                "Copia de Seguridad Creada", 
                f"La copia de seguridad se creó exitosamente con su manifiesto de datos JSON en:\n\n{res['zip_path']}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la copia de seguridad: {e}")

"""
Library Dialog for ControlHVAC CMMS.
Allows uploading, categorizing, and associating documents, floor plans, and datasheets with HVAC equipment and floors.
"""
import os
import subprocess
import sys
import uuid
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QComboBox, QMessageBox,
    QLabel, QFileDialog, QListWidget, QListWidgetItem, QAbstractItemView,
    QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from src.core.models.enums import LibraryCategory, LIBRARY_CATEGORY_LABELS
from src.core.models.library import LibraryDocument
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class LibraryDialog(QDialog):
    def __init__(
        self,
        parent=None,
        document: Optional[LibraryDocument] = None,
        equipment_service=None,
        client_service=None,
        library_service=None,
        preselected_equipment_id: Optional[str] = None,
        preselected_floor_area: Optional[str] = None,
        preselected_category: Optional[str] = None,
        read_only: Optional[bool] = None
    ):
        super().__init__(parent)
        self.document = document
        self.equipment_service = equipment_service
        self.client_service = client_service
        if not self.client_service and hasattr(parent, 'client_service'):
            self.client_service = parent.client_service
        self.library_service = library_service
        if not self.library_service and hasattr(parent, 'library_service'):
            self.library_service = parent.library_service

        self.preselected_equipment_id = preselected_equipment_id
        self.preselected_floor_area = preselected_floor_area
        self.preselected_category = preselected_category
        self.is_read_only = (document is not None) if read_only is None else read_only
        self.selected_file_path = ""

        self.resize(740, 760)
        self.setup_ui()

        if self.document:
            self._load_data()
        else:
            if self.preselected_category:
                idx = self.category_combo.findData(self.preselected_category)
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)
            if self.preselected_equipment_id:
                self._preselect_equipment(self.preselected_equipment_id)
            if self.preselected_floor_area:
                self.floor_combo.setEditText(self.preselected_floor_area)
            self._update_header_badges()

        self.set_read_only(self.is_read_only)

    def _resolve_saved_file_path(self) -> str:
        """Resolve full path on disk for the currently selected or saved document."""
        if self.selected_file_path and os.path.isfile(self.selected_file_path):
            return os.path.abspath(self.selected_file_path)
        if self.document:
            if self.library_service and hasattr(self.library_service, "get_absolute_file_path"):
                abs_p = self.library_service.get_absolute_file_path(self.document)
                if abs_p:
                    return abs_p
            if self.document.file_path:
                return self.document.file_path
            if getattr(self.document, "original_path", ""):
                return self.document.original_path
        return ""

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Top Modern Header Banner ──
        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        hb_layout = QHBoxLayout(header_banner)
        hb_layout.setContentsMargins(16, 12, 16, 12)
        hb_layout.setSpacing(14)

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon("library.svg", "#38BDF8", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.lbl_header_title = QLabel("Nuevo Recurso en Librería Técnica")
        self.lbl_header_title.setObjectName("detailTitleLabel")
        self.lbl_header_title.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        self.lbl_header_sub = QLabel("Gestión de manuales de fabricante, fichas técnicas, planos de planta y hojas de seguridad")
        self.lbl_header_sub.setObjectName("kvKeyLabel")
        title_col.addWidget(self.lbl_header_title)
        title_col.addWidget(self.lbl_header_sub)
        hb_layout.addLayout(title_col, 1)

        # Live Category & Size Pills
        pills_col = QHBoxLayout()
        pills_col.setSpacing(8)
        self.lbl_cat_pill = QLabel("●  Manual")
        self.lbl_size_pill = QLabel("●  0 KB")
        pills_col.addWidget(self.lbl_cat_pill)
        pills_col.addWidget(self.lbl_size_pill)
        hb_layout.addLayout(pills_col)

        main_layout.addWidget(header_banner)

        # ── Scrollable Card Content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(12)

        # CARD 1: Archivo y Clasificación Documental
        card_file, body_file = _create_dialog_card("1. Archivo y Clasificación Documental", "#38BDF8")
        form_file = QFormLayout(body_file)
        form_file.setContentsMargins(16, 14, 16, 14)
        form_file.setSpacing(10)
        form_file.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Ej: Plano de Distribución Piso 1 / Manual York YK")
        self.title_edit.textChanged.connect(self._update_header_badges)
        form_file.addRow("Título del Documento *:", self.title_edit)

        self.category_combo = QComboBox()
        for cat, label in LIBRARY_CATEGORY_LABELS.items():
            self.category_combo.addItem(label, cat.value if hasattr(cat, 'value') else cat)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        form_file.addRow("Categoría Documental *:", self.category_combo)

        # File Selector Row
        file_layout = QHBoxLayout()
        file_layout.setSpacing(6)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Seleccione una imagen de plano o archivo PDF/Office...")
        self.file_path_edit.setReadOnly(True)

        self.btn_browse = QPushButton(" Examinar...")
        self.btn_browse.setObjectName("primaryButton")
        self.btn_browse.setIcon(IconManager.get_icon("folder.svg", "#000000", 16))
        self.btn_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_browse.clicked.connect(self._browse_file)

        file_layout.addWidget(self.file_path_edit, 1)
        file_layout.addWidget(self.btn_browse)
        form_file.addRow("Archivo Adjunto *:", file_layout)

        # Persistent Saved / Source Path Row
        saved_path_layout = QHBoxLayout()
        saved_path_layout.setSpacing(6)
        self.saved_path_edit = QLineEdit()
        self.saved_path_edit.setPlaceholderText("La ruta completa del archivo se conservará automáticamente al seleccionar o guardar...")
        self.saved_path_edit.setReadOnly(True)

        self.btn_open_file = QPushButton(" Abrir Archivo")
        self.btn_open_file.setIcon(IconManager.get_icon("pdf.svg", "#38BDF8", 15))
        self.btn_open_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_file.setToolTip("Abrir el archivo con el visor del sistema")
        self.btn_open_file.clicked.connect(self._on_open_current_file)

        self.btn_open_folder = QPushButton(" Carpeta")
        self.btn_open_folder.setIcon(IconManager.get_icon("folder.svg", "#10B981", 15))
        self.btn_open_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_folder.setToolTip("Abrir la carpeta donde está guardado el archivo")
        self.btn_open_folder.clicked.connect(self._on_open_containing_folder)

        saved_path_layout.addWidget(self.saved_path_edit, 1)
        saved_path_layout.addWidget(self.btn_open_file)
        saved_path_layout.addWidget(self.btn_open_folder)
        form_file.addRow("Ruta Guardada:", saved_path_layout)

        scroll_layout.addWidget(card_file)

        # CARD 2: Ubicación y Alcance (Cliente / Instalación / Piso)
        card_loc, body_loc = _create_dialog_card("2. Ubicación y Alcance (Cliente / Instalación / Nivel)", "#F59E0B")
        form_loc = QFormLayout(body_loc)
        form_loc.setContentsMargins(16, 14, 16, 14)
        form_loc.setSpacing(10)
        form_loc.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.combo_client = QComboBox()
        self.combo_client.addItem("Todos los Clientes / General", "")
        self.combo_site = QComboBox()
        self.combo_site.addItem("Todas las Instalaciones / General", "")

        self._populate_clients_and_sites()
        self.combo_client.currentIndexChanged.connect(self._on_client_changed)
        self.combo_site.currentIndexChanged.connect(self._on_site_changed)

        form_loc.addRow("Cliente / Empresa:", self.combo_client)
        form_loc.addRow("Instalación / Sede:", self.combo_site)

        self.floor_combo = QComboBox()
        self.floor_combo.setEditable(True)
        self.floor_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.floor_combo.addItem("")
        self._populate_floors()
        self.floor_combo.lineEdit().setPlaceholderText("Ej: Piso 1, Subterráneo -1, Sala de Máquinas, Azotea...")
        form_loc.addRow("Piso / Nivel / Planta:", self.floor_combo)

        scroll_layout.addWidget(card_loc)

        # CARD 3: Equipos Vinculados Opcionales
        card_eq, body_eq = _create_dialog_card("3. Equipos HVAC Vinculados (Opcional)", "#10B981")
        eq_layout = QVBoxLayout(body_eq)
        eq_layout.setContentsMargins(16, 12, 16, 14)
        eq_layout.setSpacing(8)

        self.eq_search = QLineEdit()
        self.eq_search.setPlaceholderText("🔍 Filtrar equipos por TAG, nombre, modelo o sede para vincular...")
        self.eq_search.textChanged.connect(self._filter_equipment_list)
        eq_layout.addWidget(self.eq_search)

        self.eq_list_widget = QListWidget()
        self.eq_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.eq_list_widget.setMinimumHeight(125)
        self.eq_list_widget.setMaximumHeight(160)
        self._populate_equipment_list()
        eq_layout.addWidget(self.eq_list_widget)

        scroll_layout.addWidget(card_eq)

        # CARD 4: Descripción y Etiquetas
        card_meta, body_meta = _create_dialog_card("4. Descripción Técnica y Etiquetas (Tags)", "#8B5CF6")
        form_meta = QFormLayout(body_meta)
        form_meta.setContentsMargins(16, 14, 16, 14)
        form_meta.setSpacing(10)
        form_meta.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Descripción general, indicaciones de acceso, ubicación de tableros o salas...")
        self.desc_edit.setMaximumHeight(68)
        form_meta.addRow("Descripción:", self.desc_edit)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Ej: plano, planta, piso1, distribucion, equipos (separados por coma)")
        form_meta.addRow("Etiquetas (Tags):", self.tags_edit)

        scroll_layout.addWidget(card_meta)
        scroll_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # ── Bottom Action Bar ──
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        self.lbl_mode_indicator = QLabel("● MODO EDICIÓN")
        self.lbl_mode_indicator.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")
        btn_layout.addWidget(self.lbl_mode_indicator)
        btn_layout.addStretch()

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)

        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)

        self.btn_save = QPushButton("Guardar en Librería")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)

        main_layout.addWidget(footer_bar)

    def _update_header_badges(self):
        t_val = self.title_edit.text().strip() if hasattr(self, "title_edit") else ""
        if self.document and not t_val:
            t_val = self.document.title
        self.lbl_header_title.setText(f"Documento  —  {t_val}" if t_val else "Nuevo Recurso en Librería Técnica")

        cat_label = self.category_combo.currentText() if hasattr(self, "category_combo") else "Manual"
        cat_code = (self.category_combo.currentData() or "").upper()
        if "SAFETY" in cat_code:
            c_fg, c_bg = "#F59E0B", "#451A03"
        elif "DIAGRAM" in cat_code or "FLOOR" in cat_code:
            c_fg, c_bg = "#10B981", "#064E3B"
        elif "DATASHEET" in cat_code:
            c_fg, c_bg = "#818CF8", "#1E1B4B"
        else:
            c_fg, c_bg = "#38BDF8", "#0C4A6E"

        self.lbl_cat_pill.setText(f"●  {cat_label}")
        self.lbl_cat_pill.setStyleSheet(
            f"background-color: {c_bg}; color: {c_fg}; border: 1px solid {c_fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

        # Size pill
        size_str = "Sin archivo"
        if self.selected_file_path and os.path.isfile(self.selected_file_path):
            sz_kb = os.path.getsize(self.selected_file_path) / 1024
            size_str = f"{sz_kb:.1f} KB" if sz_kb < 1024 else f"{sz_kb / 1024:.2f} MB"
        elif self.document and self.document.file_size > 0:
            size_str = self.document.formatted_size

        self.lbl_size_pill.setText(f"●  {size_str}")
        self.lbl_size_pill.setStyleSheet(
            "background-color: #064E3B; color: #10B981; border: 1px solid #10B981; "
            "border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

        resolved_path = self._resolve_saved_file_path()
        has_file = bool(resolved_path and os.path.isfile(resolved_path))
        self.btn_open_file.setEnabled(has_file)
        self.btn_open_folder.setEnabled(bool(resolved_path))

    def _on_category_changed(self):
        cat = self.category_combo.currentData()
        if cat == LibraryCategory.FLOOR_PLAN.value:
            if not self.title_edit.text().strip():
                self.title_edit.setPlaceholderText("Ej: Plano de Planta Arquitectónico Piso 1")
            self.floor_combo.setFocus()
        self._update_header_badges()

    def _populate_clients_and_sites(self):
        self.combo_client.clear()
        self.combo_client.addItem("Todos los Clientes / General", "")
        if not self.client_service:
            return

        clients = self.client_service.get_all_clients()
        clients.sort(key=lambda c: (c.name or c.company_name or "").lower())
        for c in clients:
            cname = c.name or c.company_name
            self.combo_client.addItem(cname, c.id)

    def _on_client_changed(self):
        self.combo_site.clear()
        self.combo_site.addItem("Todas las Instalaciones / General", "")
        client_id = self.combo_client.currentData()
        if not client_id or not self.client_service:
            self._populate_floors()
            return

        sites = self.client_service.get_sites_for_client(client_id)
        for s in sites:
            self.combo_site.addItem(s.name, s.id)
        self._populate_floors()

    def _on_site_changed(self):
        self._populate_floors()

    def _populate_floors(self):
        current_txt = self.floor_combo.currentText()
        self.floor_combo.clear()
        self.floor_combo.addItem("")

        floors = set()
        if self.equipment_service:
            all_eqs = self.equipment_service.get_all_equipment()
            site_id = self.combo_site.currentData()
            client_id = self.combo_client.currentData()
            for eq in all_eqs:
                if site_id and eq.site_id != site_id:
                    continue
                if client_id and eq.client_id != client_id:
                    continue
                fl = getattr(eq, 'floor_area', '') or ''
                if fl and fl.strip():
                    floors.add(fl.strip())

        for fl in sorted(floors):
            self.floor_combo.addItem(fl)

        if current_txt:
            self.floor_combo.setEditText(current_txt)

    def _populate_equipment_list(self):
        self.eq_list_widget.clear()
        if not self.equipment_service:
            return

        all_eqs = self.equipment_service.get_all_equipment()
        all_eqs.sort(key=lambda e: (e.tag or e.name or "").lower())

        for eq in all_eqs:
            display_text = f"[{eq.tag}] {eq.name} - {eq.model or ''} ({eq.site_name or eq.client_name or ''})".strip()
            item = QListWidgetItem(display_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, eq.id)
            self.eq_list_widget.addItem(item)

    def _filter_equipment_list(self, text: str):
        query = text.lower().strip()
        for i in range(self.eq_list_widget.count()):
            item = self.eq_list_widget.item(i)
            item.setHidden(query not in item.text().lower() if query else False)

    def _preselect_equipment(self, equipment_id: str):
        for i in range(self.eq_list_widget.count()):
            item = self.eq_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == equipment_id:
                item.setCheckState(Qt.CheckState.Checked)

        if self.equipment_service:
            eq = self.equipment_service.get_equipment(equipment_id)
            if eq:
                if eq.client_id:
                    idx = self.combo_client.findData(eq.client_id)
                    if idx >= 0:
                        self.combo_client.setCurrentIndex(idx)
                if eq.site_id:
                    idx = self.combo_site.findData(eq.site_id)
                    if idx >= 0:
                        self.combo_site.setCurrentIndex(idx)
                if getattr(eq, 'floor_area', ''):
                    self.floor_combo.setEditText(eq.floor_area)

    def _load_data(self):
        doc = self.document
        self.title_edit.setText(doc.title)
        idx = self.category_combo.findData(doc.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        if doc.client_id:
            c_idx = self.combo_client.findData(doc.client_id)
            if c_idx >= 0:
                self.combo_client.setCurrentIndex(c_idx)
        if doc.site_id:
            s_idx = self.combo_site.findData(doc.site_id)
            if s_idx >= 0:
                self.combo_site.setCurrentIndex(s_idx)

        if doc.floor_area:
            self.floor_combo.setEditText(doc.floor_area)

        self.file_path_edit.setText(f"{doc.file_name} ({doc.formatted_size})" if doc.file_name else "")

        resolved_path = self._resolve_saved_file_path()
        self.saved_path_edit.setText(resolved_path or doc.file_path or getattr(doc, "original_path", "") or "")
        self.saved_path_edit.setToolTip(self.saved_path_edit.text())

        self.desc_edit.setText(doc.description)
        self.tags_edit.setText(", ".join(doc.tags) if doc.tags else "")

        eq_ids = set(doc.equipment_ids or [])
        for i in range(self.eq_list_widget.count()):
            item = self.eq_list_widget.item(i)
            item_eq_id = item.data(Qt.ItemDataRole.UserRole)
            if item_eq_id in eq_ids:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

        self._update_header_badges()

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only

        if self.document:
            self.setWindowTitle(
                f"Documento: {self.document.title}" if read_only
                else f"Editar Documento: {self.document.title}"
            )
            self.lbl_mode_indicator.setText("● MODO LECTURA / CONSULTA" if read_only else "● MODO EDICIÓN ACTIVO")
            self.lbl_mode_indicator.setStyleSheet(
                "color: #94A3B8; font-weight: bold; font-size: 11px;" if read_only
                else "color: #F59E0B; font-weight: bold; font-size: 11px;"
            )
        else:
            self.setWindowTitle("Nuevo Documento / Plano de Planta")
            self.lbl_mode_indicator.setText("● NUEVO RECURSO DOCUMENTAL")
            self.lbl_mode_indicator.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self.title_edit.setReadOnly(read_only)
        self.category_combo.setEnabled(not read_only)
        self.btn_browse.setEnabled(not read_only)
        self.combo_client.setEnabled(not read_only)
        self.combo_site.setEnabled(not read_only)
        self.floor_combo.setEnabled(not read_only)
        self.desc_edit.setReadOnly(read_only)
        self.tags_edit.setReadOnly(read_only)
        self.eq_search.setEnabled(not read_only)
        self.eq_list_widget.setEnabled(not read_only)

        self.btn_close.setVisible(read_only and self.document is not None)
        self.btn_edit_mode.setVisible(read_only and self.document is not None)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

    def _browse_file(self):
        from src.app.state_manager import StateManager
        sm = StateManager()

        # Determine initial folder: current selected file, document's original path, or last browsed folder
        start_dir = sm.get_last_library_dir()
        if self.selected_file_path and os.path.exists(os.path.dirname(self.selected_file_path)):
            start_dir = os.path.dirname(self.selected_file_path)
        elif self.document and getattr(self.document, "original_path", ""):
            orig_dir = os.path.dirname(self.document.original_path)
            if os.path.isdir(orig_dir):
                start_dir = orig_dir

        file_filter = (
            "Todos los Archivos (*.*);;"
            "Imágenes de Planos (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "Documentos PDF (*.pdf);;"
            "Planos CAD (*.dwg *.dxf *.svg);;"
            "Documentos Office (*.docx *.xlsx *.pptx *.doc *.xls)"
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo o Plano de la Librería",
            start_dir,
            file_filter
        )
        if file_path:
            abs_file = os.path.abspath(file_path)
            sm.set_last_library_dir(abs_file)
            self.selected_file_path = abs_file
            file_size_kb = os.path.getsize(abs_file) / 1024
            size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb / 1024:.2f} MB"
            self.file_path_edit.setText(f"{os.path.basename(abs_file)} ({size_str})")
            self.saved_path_edit.setText(abs_file)
            self.saved_path_edit.setToolTip(abs_file)

            if not self.title_edit.text().strip():
                base_name, _ = os.path.splitext(os.path.basename(abs_file))
                clean_t = base_name.replace("_", " ").replace("-", " ").title()
                if "plano" in clean_t.lower() or "planta" in clean_t.lower() or "piso" in clean_t.lower():
                    idx = self.category_combo.findData(LibraryCategory.FLOOR_PLAN.value)
                    if idx >= 0:
                        self.category_combo.setCurrentIndex(idx)
                self.title_edit.setText(clean_t)

            self._update_header_badges()

    def _on_open_current_file(self):
        target = self._resolve_saved_file_path()
        if not target or not os.path.isfile(target):
            QMessageBox.warning(self, "Archivo no encontrado", "El archivo no se encuentra en la ruta especificada.")
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(target)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', target])
            else:
                subprocess.Popen(['xdg-open', target])
        except Exception as e:
            QMessageBox.warning(self, "Error al abrir", f"No se pudo abrir el archivo:\n{e}")

    def _on_open_containing_folder(self):
        target = self._resolve_saved_file_path()
        if not target:
            return
        folder = target if os.path.isdir(target) else os.path.dirname(target)
        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Carpeta no encontrada", f"No existe la carpeta:\n{folder}")
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(folder)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta:\n{e}")

    def _on_cancel_clicked(self):
        if self.document is not None:
            self.selected_file_path = ""
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def validate_and_accept(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Campo Requerido", "Por favor ingrese el título del documento o plano.")
            self.title_edit.setFocus()
            return

        if not self.document and not self.selected_file_path:
            QMessageBox.warning(self, "Archivo Requerido", "Por favor seleccione un archivo para subir a la librería.")
            self.btn_browse.setFocus()
            return

        self.accept()

    def get_document_data(self) -> LibraryDocument:
        doc_id = self.document.id if self.document else f"doc_{uuid.uuid4().hex[:8]}"
        created_at = self.document.created_at if self.document else None

        checked_eqs = []
        for i in range(self.eq_list_widget.count()):
            item = self.eq_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_eqs.append(item.data(Qt.ItemDataRole.UserRole))

        tags_raw = self.tags_edit.text().split(",")
        tags = [t.strip() for t in tags_raw if t.strip()]

        doc = LibraryDocument(
            id=doc_id,
            title=self.title_edit.text().strip(),
            category=self.category_combo.currentData(),
            description=self.desc_edit.toPlainText().strip(),
            client_id=self.combo_client.currentData() or "",
            site_id=self.combo_site.currentData() or "",
            floor_area=self.floor_combo.currentText().strip(),
            equipment_ids=checked_eqs,
            tags=tags,
        )
        if self.document:
            doc.file_name = self.document.file_name
            doc.file_path = self.document.file_path
            doc.original_path = getattr(self.document, "original_path", "") or ""
            doc.file_size = self.document.file_size
            doc.mime_type = self.document.mime_type
            if created_at:
                doc.created_at = created_at
        if self.selected_file_path:
            doc.original_path = os.path.abspath(self.selected_file_path)

        return doc

    def get_source_file_path(self) -> Optional[str]:
        return self.selected_file_path if self.selected_file_path else None

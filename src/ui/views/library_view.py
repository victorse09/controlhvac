"""
Technical Library View for ControlHVAC CMMS.
Allows browsing, filtering, uploading, opening, and linking documentation with equipment.
"""
import os
import html
import shutil
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView,
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView, QComboBox,
    QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.core.models.enums import LibraryCategory, LIBRARY_CATEGORY_LABELS
from src.core.models.library import LibraryDocument
from src.ui.dialogs.library_dialog import LibraryDialog
from src.ui.icon_manager import IconManager
from src.ui.models.table_models import LibraryTableModel
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table


class LibraryView(QWidget):
    def __init__(self, library_service, equipment_service=None, client_service=None, parent=None):
        super().__init__(parent)
        self.library_service = library_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.documents = []
        self._selected_document: Optional[LibraryDocument] = None
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Stats Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_total = StatCard("Total Recursos", "0", IconManager.get_icon("library", "#38BDF8"), accent_color="#38BDF8")
        self.card_manuals = StatCard("Manuales Fabricante", "0", IconManager.get_icon("folder.svg", "#60A5FA"), accent_color="#60A5FA")
        self.card_datasheets = StatCard("Fichas Técnicas", "0", IconManager.get_icon("pdf.svg", "#818CF8"), accent_color="#818CF8")
        self.card_safety = StatCard("HDS / Seguridad", "0", IconManager.get_icon("warning.svg", "#F59E0B"), accent_color="#F59E0B")
        self.card_diagrams = StatCard("Planos y Esquemas", "0", IconManager.get_icon("equipment", "#10B981"), accent_color="#10B981")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_manuals)
        stats_layout.addWidget(self.card_datasheets)
        stats_layout.addWidget(self.card_safety)
        stats_layout.addWidget(self.card_diagrams)
        main_layout.addLayout(stats_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar documentos por título, archivo, etiquetas o descripción...")
        self.search_bar.textChanged.connect(self._apply_filters)

        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas las Categorías", "")
        for cat, label in LIBRARY_CATEGORY_LABELS.items():
            self.category_filter.addItem(label, cat.value if hasattr(cat, 'value') else cat)
        self.category_filter.currentIndexChanged.connect(self._apply_filters)

        self.equipment_filter = QComboBox()
        self.equipment_filter.addItem("Todos los Equipos", "")
        self._populate_equipment_filter()
        self.equipment_filter.currentIndexChanged.connect(self._apply_filters)

        self.btn_open_top = QPushButton(" Abrir Archivo")
        self.btn_open_top.setIcon(IconManager.get_icon("folder.svg", "#F8FAFC", 18))
        self.btn_open_top.setIconSize(QSize(18, 18))
        self.btn_open_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_top.setEnabled(False)
        self.btn_open_top.clicked.connect(self.on_open_file_clicked)

        self.btn_new = QPushButton(" Subir a Librería")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#000000", 18))
        self.btn_new.setIconSize(QSize(18, 18))
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new)

        toolbar.addWidget(self.search_bar, 2)
        toolbar.addWidget(self.category_filter, 1)
        toolbar.addWidget(self.equipment_filter, 1)
        toolbar.addWidget(self.btn_open_top)
        toolbar.addWidget(self.btn_new)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Table
        self.table = QTableView()
        self.model = LibraryTableModel([], equipment_service=self.equipment_service)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_double_click)
        self.splitter.addWidget(self.table)

        # Detail Frame
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        self.detail_frame.setMinimumWidth(360)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Header with actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel("Seleccione un documento")
        self.lbl_title.setObjectName("detailTitleLabel")
        self.lbl_title.setWordWrap(True)
        header_layout.addWidget(self.lbl_title, 1)

        self.btn_export_copy = QPushButton()
        self.btn_export_copy.setIcon(IconManager.get_icon("export.svg", "#F8FAFC", 18))
        self.btn_export_copy.setIconSize(QSize(18, 18))
        self.btn_export_copy.setFixedSize(36, 36)
        self.btn_export_copy.setToolTip("Guardar copia en el equipo...")
        self.btn_export_copy.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_copy.setEnabled(False)
        self.btn_export_copy.clicked.connect(self.on_export_copy_clicked)
        header_layout.addWidget(self.btn_export_copy)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar Información del Documento")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Documento")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        header_layout.addWidget(self.btn_delete)

        detail_layout.addLayout(header_layout)

        # Big Action Button for Opening
        self.btn_open_main = QPushButton(" Abrir Archivo en Visualizador")
        self.btn_open_main.setObjectName("primaryButton")
        self.btn_open_main.setIcon(IconManager.get_icon("folder.svg", "#000000", 18))
        self.btn_open_main.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_main.setEnabled(False)
        self.btn_open_main.clicked.connect(self.on_open_file_clicked)
        detail_layout.addWidget(self.btn_open_main)

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
        storage = getattr(self.library_service, "storage", None)
        setup_modern_table(
            self.table,
            storage=storage,
            settings_key="library_table",
            default_widths=[140, 195, 160, 85, 160, 105],
            splitter=self.splitter,
            default_splitter_sizes=[640, 380],
        )
        self._display_document_detail(None)

    def _populate_equipment_filter(self):
        self.equipment_filter.clear()
        self.equipment_filter.addItem("Todos los Equipos", "")
        if not self.equipment_service:
            return

        all_eqs = self.equipment_service.get_all_equipment()
        all_eqs.sort(key=lambda e: (e.tag or e.name or "").lower())
        for eq in all_eqs:
            self.equipment_filter.addItem(f"[{eq.tag}] {eq.name}", eq.id)

    def refresh_data(self):
        """Reload library documents and equipment filter."""
        self._populate_equipment_filter()
        self._apply_filters()
        self._update_stats()

    def _update_stats(self):
        stats = self.library_service.get_stats()
        self.card_total.set_value(str(stats.get("total", 0)))
        self.card_manuals.set_value(str(stats.get("manuals", 0)))
        self.card_datasheets.set_value(str(stats.get("datasheets", 0)))
        self.card_safety.set_value(str(stats.get("safety_sheets", 0)))
        self.card_diagrams.set_value(str(stats.get("diagrams", 0)))

    def _apply_filters(self):
        query = self.search_bar.text()
        category = self.category_filter.currentData() or None
        equipment_id = self.equipment_filter.currentData() or None

        self.documents = self.library_service.search_documents(
            query=query, category=category, equipment_id=equipment_id
        )
        self.model.set_data(self.documents)

        if self._selected_document and self._selected_document not in self.documents:
            self._display_document_detail(None)

    def on_selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()
            doc = self.model.get_item(row)
            self._display_document_detail(doc)
        else:
            self._display_document_detail(None)

    def _display_document_detail(self, doc: Optional[LibraryDocument]):
        self._selected_document = doc
        clear_layout_widgets(self.detail_content_layout)
        if not doc:
            self.lbl_title.setText("Seleccione un documento")
            self.btn_open_top.setEnabled(False)
            self.btn_open_main.setEnabled(False)
            self.btn_export_copy.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.detail_content_layout.addWidget(
                build_empty_detail_card("Haga clic en un documento de la lista para ver sus metadatos, equipos asociados y abrirlo.")
            )
            self.detail_content_layout.addStretch()
            return

        self.lbl_title.setText(f"{doc.title}")
        self.btn_open_top.setEnabled(True)
        self.btn_open_main.setEnabled(True)
        self.btn_export_copy.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        cat_label = LIBRARY_CATEGORY_LABELS.get(doc.category, doc.category)
        cat_upper = (doc.category or "").upper()
        if "SAFETY" in cat_upper:
            c_fg, c_bg = "#F59E0B", "#451A03"
        elif "DIAGRAM" in cat_upper:
            c_fg, c_bg = "#10B981", "#064E3B"
        elif "DATASHEET" in cat_upper:
            c_fg, c_bg = "#818CF8", "#1E1B4B"
        else:
            c_fg, c_bg = "#38BDF8", "#0C4A6E"

        self.detail_content_layout.addWidget(
            build_status_banner([
                ("CATEGORÍA DOCUMENTAL", cat_label, c_fg, c_bg),
                ("TAMAÑO ARCHIVO", doc.formatted_size, "#10B981", "#064E3B"),
            ])
        )

        created_fmt = (doc.created_at or "")[:10]
        if len(created_fmt) == 10 and created_fmt[4] == '-' and created_fmt[7] == '-':
            p = created_fmt.split('-')
            created_fmt = f"{p[2]}-{p[1]}-{p[0]}"

        tags_html = ""
        if doc.tags:
            for tag in doc.tags:
                tags_html += f"<span style='background-color: #1E293B; color: #38BDF8; padding: 2px 6px; border-radius: 4px; margin-right: 4px;'>#{html.escape(tag)}</span> "
        else:
            tags_html = "<i style='color: #64748B;'>Sin etiquetas</i>"

        saved_abs_path = self.library_service.get_absolute_file_path(doc) if self.library_service else (doc.file_path or "")
        orig_path = getattr(doc, "original_path", "") or ""
        file_exists = bool(saved_abs_path and os.path.isfile(saved_abs_path))
        path_status_badge = (
            "<span style='color: #10B981; font-weight: bold;'>● Archivo verificado</span>"
            if file_exists else
            "<span style='color: #F59E0B; font-weight: bold;'>● Sin archivo físico</span>"
        )

        info_rows = [
            ("Título", f"<b>{html.escape(doc.title or '')}</b>"),
            ("Nombre Archivo", f"<b style='color: #38BDF8;'>{html.escape(doc.file_name or 'N/A')}</b> ({path_status_badge})"),
            ("Ruta Guardada", f"<span style='color: #CBD5E1; font-size: 11px;'>{html.escape(saved_abs_path or doc.file_path or 'N/A')}</span>"),
        ]
        if orig_path and orig_path != saved_abs_path:
            info_rows.append(("Ruta de Origen", f"<span style='color: #94A3B8; font-size: 11px;'>{html.escape(orig_path)}</span>"))
        info_rows.extend([
            ("Piso / Planta", html.escape(doc.floor_area or "General / No especificado")),
            ("Fecha Registro", html.escape(created_fmt)),
            ("Etiquetas", tags_html),
        ])
        self.detail_content_layout.addWidget(
            build_section_card("Metadatos del Documento", "#38BDF8", build_kv_widget(info_rows))
        )

        # Associated equipment
        eq_lines = []
        if doc.equipment_ids:
            for eq_id in doc.equipment_ids:
                eq_label = html.escape(str(eq_id))
                if self.equipment_service:
                    eq = self.equipment_service.get_equipment(eq_id)
                    if eq:
                        c_name = getattr(eq, 'client_name', '')
                        if not c_name and self.client_service and getattr(eq, 'client_id', ''):
                            cl = self.client_service.get_client(eq.client_id)
                            if cl:
                                c_name = cl.company_name
                        extra = f" <span style='color: #94A3B8;'>({html.escape(c_name)})</span>" if c_name else ""
                        eq_label = f"<b style='color: #10B981;'>{html.escape(eq.tag)}</b> — {html.escape(eq.name)}{extra}"
                eq_lines.append(f"• {eq_label}")
        else:
            eq_lines.append("<i style='color: #94A3B8;'>Sin equipos específicos vinculados (Documento general).</i>")

        self.detail_content_layout.addWidget(
            build_section_card(f"Equipos Asociados ({len(doc.equipment_ids)})", "#10B981", build_rich_label("<br>".join(eq_lines)))
        )

        desc_txt = html.escape(doc.description).replace("\n", "<br>") if doc.description else "<i style='color: #64748B;'>Sin descripción registrada.</i>"
        self.detail_content_layout.addWidget(
            build_section_card("Descripción y Notas", "#A855F7", build_rich_label(desc_txt))
        )
        self.detail_content_layout.addStretch()

    def on_open_file_clicked(self):
        if not self._selected_document:
            return

        success = self.library_service.open_document(self._selected_document.id)
        if not success:
            QMessageBox.warning(
                self,
                "Archivo no encontrado",
                f"No se pudo abrir el archivo '{self._selected_document.file_name}'.\nVerifique que el archivo exista en la carpeta de la librería."
            )

    def on_export_copy_clicked(self):
        if not self._selected_document:
            return

        src_path = self.library_service.get_absolute_file_path(self._selected_document)
        if not src_path or not os.path.exists(src_path):
            QMessageBox.warning(self, "Error", "El archivo origen no existe en la librería.")
            return

        from src.app.state_manager import StateManager
        sm = StateManager()
        default_dir = sm.get_last_library_dir()
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Copia de Documento",
            os.path.join(default_dir, self._selected_document.file_name)
        )
        if dest_path:
            sm.set_last_library_dir(dest_path)
            try:
                shutil.copy2(src_path, dest_path)
                QMessageBox.information(self, "Copia Exitosa", f"Archivo guardado exitosamente en:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la copia:\n{str(e)}")

    def on_new(self):
        dialog = LibraryDialog(
            self,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            library_service=self.library_service
        )
        if dialog.exec():
            new_doc = dialog.get_document_data()
            source_file = dialog.get_source_file_path()
            saved_doc = self.library_service.save_document(new_doc, source_file)
            self.refresh_data()
            self._display_document_detail(saved_doc)

    def on_double_click(self, index):
        doc = self.model.get_item(index.row())
        if doc:
            self._display_document_detail(doc)
            dialog = LibraryDialog(
                self,
                document=doc,
                equipment_service=self.equipment_service,
                client_service=self.client_service,
                library_service=self.library_service,
                read_only=True
            )
            if dialog.exec():
                updated_doc = dialog.get_document_data()
                source_file = dialog.get_source_file_path()
                saved_doc = self.library_service.save_document(updated_doc, source_file)
                self.refresh_data()
                self._display_document_detail(saved_doc)

    def on_edit_clicked(self):
        if self._selected_document:
            dialog = LibraryDialog(
                self,
                document=self._selected_document,
                equipment_service=self.equipment_service,
                client_service=self.client_service,
                library_service=self.library_service,
                read_only=False
            )
            if dialog.exec():
                updated_doc = dialog.get_document_data()
                source_file = dialog.get_source_file_path()
                saved_doc = self.library_service.save_document(updated_doc, source_file)
                self.refresh_data()
                self._display_document_detail(saved_doc)

    def on_delete_clicked(self):
        if not self._selected_document:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de enviar el documento '{self._selected_document.title}' a la papelera de reciclaje?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.library_service.delete_document(self._selected_document.id)
            self._selected_document = None
            self.refresh_data()

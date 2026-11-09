from datetime import datetime
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeView, 
    QPushButton, QLabel, QFrame, QMessageBox, QComboBox, QMenu,
    QScrollArea, QHeaderView
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QSize
from PySide6.QtGui import QCursor
from src.ui.widgets.search_bar import SearchBar
from src.ui.models.equipment_tree_model import EquipmentTreeModel
from src.ui.dialogs.equipment_dialog import EquipmentDialog
from src.ui.icon_manager import IconManager
from src.core.models.equipment import format_technical_specs
from src.core.models.enums import (
    SYSTEM_TYPE_LABELS, OPERATIONAL_STATUS_LABELS, MAINTENANCE_FREQUENCY_LABELS,
    LIBRARY_CATEGORY_LABELS
)

class EquipmentView(QWidget):
    def __init__(self, equipment_service, client_service, inventory_service=None, custom_lists_service=None, incident_service=None, export_service=None, library_service=None, parent=None):
        super().__init__(parent)
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.custom_lists_service = custom_lists_service
        self.incident_service = incident_service
        self.export_service = export_service
        self.library_service = library_service
        self.storage = getattr(equipment_service, 'storage', None)
        self._restoring_ui_state = False
        self._expanded_keys: set[str] = set()
        self._selected_key: str = ""
        self.setup_ui()
        self.refresh_data(initial_load=True)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar por tag, nombre, modelo, serie...")
        self.search_bar.textChanged.connect(self._on_filter_changed)
        
        self.cb_type = QComboBox()
        self.cb_type.setMinimumWidth(130)
        self.cb_type.addItem("Todos los tipos", "")
        for stype, label in SYSTEM_TYPE_LABELS.items():
            val = stype.value if hasattr(stype, 'value') else str(stype)
            self.cb_type.addItem(label, val)
        self.cb_type.currentIndexChanged.connect(self._on_filter_changed)
        
        self.cb_status = QComboBox()
        self.cb_status.setMinimumWidth(130)
        self.cb_status.addItem("Todos los estados", "")
        for status, label in OPERATIONAL_STATUS_LABELS.items():
            val = status.value if hasattr(status, 'value') else str(status)
            self.cb_status.addItem(label, val)
        self.cb_status.currentIndexChanged.connect(self._on_filter_changed)

        self.cb_bms_status = QComboBox()
        self.cb_bms_status.setMinimumWidth(130)
        self.cb_bms_status.addItem("Estado BMS: Todos", "")
        if self.custom_lists_service:
            bms_opts = self.custom_lists_service.get_list("bms_status")
        else:
            bms_opts = ["Operativo", "En Falla", "Sin Grafica", "Sin Control", "Fuera de Servicio", "Inexistente"]
        for opt in bms_opts:
            self.cb_bms_status.addItem(f"BMS: {opt}", opt)
        self.cb_bms_status.currentIndexChanged.connect(self._on_filter_changed)
        
        # Separator Frame
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #334155; margin: 2px 2px;")
        
        self.btn_new = QPushButton()
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#FFFFFF", 18))
        self.btn_new.setIconSize(QSize(18, 18))
        self.btn_new.setFixedSize(36, 36)
        self.btn_new.setToolTip("Nuevo Equipo")
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new_equipment)

        self.btn_pdf = QPushButton()
        self.btn_pdf.setIcon(IconManager.get_icon("pdf.svg", "#38BDF8", 18))
        self.btn_pdf.setIconSize(QSize(18, 18))
        self.btn_pdf.setFixedSize(36, 36)
        self.btn_pdf.setToolTip("Generar Listados y Reportes PDF de Equipos (Por Piso, General, etc.)...")
        self.btn_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pdf.clicked.connect(self.on_export_pdf_dialog)
        
        toolbar.addWidget(self.search_bar, 1)
        toolbar.addWidget(self.cb_type)
        toolbar.addWidget(self.cb_status)
        toolbar.addWidget(self.cb_bms_status)
        toolbar.addWidget(sep)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_pdf)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Left: Tree
        self.tree = QTreeView()
        self.tree.setObjectName("equipmentModernTree")
        self.tree_model = EquipmentTreeModel(self.equipment_service, self.client_service, self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.tree_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.tree.setModel(self.proxy_model)
        self.tree.setAnimated(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.setIndentation(20)
        self.tree.setUniformRowHeights(False)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.tree.doubleClicked.connect(self.on_tree_double_clicked)
        self.tree.expanded.connect(self._on_node_expanded)
        self.tree.collapsed.connect(self._on_node_collapsed)
        
        # Context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        hdr = self.tree.header()
        hdr.setSectionsMovable(True)
        hdr.setSectionsClickable(True)
        hdr.setStretchLastSection(True)
        hdr.setMinimumSectionSize(65)
        for col_idx in range(7):
            hdr.setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Interactive)
        hdr.sectionResized.connect(self._on_header_resized)
        hdr.sectionMoved.connect(self._on_header_moved)
        self.splitter.addWidget(self.tree)

        # Right: Detail Panel
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)
        
        # Header layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        self.lbl_detail_icon = QLabel()
        self.lbl_detail_icon.setFixedSize(28, 28)
        self.lbl_detail_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_detail_icon.setStyleSheet("background: transparent; border: none;")
        self.lbl_detail_icon.setVisible(False)
        header_layout.addWidget(self.lbl_detail_icon)

        self.lbl_title = QLabel("Seleccione un equipo")
        self.lbl_title.setObjectName("detailTitleLabel")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        
        self.btn_report_incident = QPushButton()
        self.btn_report_incident.setIcon(IconManager.get_icon("fault.svg", "#EF4444", 18))
        self.btn_report_incident.setIconSize(QSize(18, 18))
        self.btn_report_incident.setFixedSize(36, 36)
        self.btn_report_incident.setToolTip("Reportar Avería / Incidencia")
        self.btn_report_incident.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_report_incident.setEnabled(False)
        self.btn_report_incident.clicked.connect(self.on_report_incident)
        header_layout.addWidget(self.btn_report_incident)

        self.btn_docs = QPushButton()
        self.btn_docs.setIcon(IconManager.get_icon("folder.svg", "#38BDF8", 18))
        self.btn_docs.setIconSize(QSize(18, 18))
        self.btn_docs.setFixedSize(36, 36)
        self.btn_docs.setToolTip("Documentos y Manuales de este Equipo (Librería)")
        self.btn_docs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_docs.setEnabled(False)
        self.btn_docs.clicked.connect(self.on_view_documents)
        header_layout.addWidget(self.btn_docs)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar Equipo seleccionado")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_equipment)
        header_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Equipo seleccionado")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete_equipment)
        header_layout.addWidget(self.btn_delete)
        
        self.btn_detail_pdf = QPushButton()
        self.btn_detail_pdf.setIcon(IconManager.get_icon("pdf.svg", "#EF4444", 18))
        self.btn_detail_pdf.setIconSize(QSize(18, 18))
        self.btn_detail_pdf.setFixedSize(36, 36)
        self.btn_detail_pdf.setToolTip("Exportar ficha técnica del equipo a PDF")
        self.btn_detail_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_detail_pdf.setEnabled(False)
        self.btn_detail_pdf.clicked.connect(self.on_export_single_pdf)
        header_layout.addWidget(self.btn_detail_pdf)
        
        detail_layout.addLayout(header_layout)
        
        # Scroll area for detail content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        detail_content = QWidget()
        self.detail_content_layout = QVBoxLayout(detail_content)
        self.detail_content_layout.setContentsMargins(0, 0, 4, 0)
        self.detail_content_layout.setSpacing(10)
        
        scroll.setWidget(detail_content)
        detail_layout.addWidget(scroll)
        
        self.splitter.addWidget(self.detail_frame)
        self.splitter.setSizes([620, 430])
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        self._load_ui_settings()
        self.clear_detail()

    def _clear_detail_cards(self):
        """Safely removes all dynamic card widgets from detail_content_layout."""
        while self.detail_content_layout.count() > 0:
            item = self.detail_content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()

    def _add_card_widget(self, title: str, accent_color: str, body_widget: QWidget):
        """Creates a native styled QFrame card with an accented header and adds it to the detail layout."""
        card = QFrame()
        card.setObjectName("eqSectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("eqCardHeader")
        header.setStyleSheet(
            f"QFrame#eqCardHeader {{"
            f"  border-bottom: 2px solid {accent_color};"
            f"}}"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 6, 12, 6)
        lbl_h = QLabel(title.upper())
        lbl_h.setStyleSheet(
            f"color: {accent_color}; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent; border: none;"
        )
        h_layout.addWidget(lbl_h)
        card_layout.addWidget(header)

        body_container = QWidget()
        body_container.setStyleSheet("background: transparent; border: none;")
        b_layout = QVBoxLayout(body_container)
        b_layout.setContentsMargins(12, 10, 12, 10)
        b_layout.setSpacing(6)
        b_layout.addWidget(body_widget)
        card_layout.addWidget(body_container)

        self.detail_content_layout.addWidget(card)

    def _build_kv_widget(self, pairs: list[tuple[str, str]]) -> QWidget:
        """Creates a native 2-column grid of alternating key-value rows."""
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        for idx, (label_txt, val_html) in enumerate(pairs):
            row_frame = QFrame()
            row_frame.setObjectName("kvRowEven" if idx % 2 == 0 else "kvRowOdd")
            r_layout = QHBoxLayout(row_frame)
            r_layout.setContentsMargins(8, 5, 8, 5)
            r_layout.setSpacing(8)

            lbl_k = QLabel(label_txt)
            lbl_k.setObjectName("kvKeyLabel")
            lbl_k.setWordWrap(True)
            lbl_k.setMinimumWidth(135)

            lbl_v = QLabel(val_html)
            lbl_v.setObjectName("kvValueLabel")
            lbl_v.setTextFormat(Qt.TextFormat.RichText)
            lbl_v.setWordWrap(True)

            r_layout.addWidget(lbl_k, 4)
            r_layout.addWidget(lbl_v, 6)
            v_layout.addWidget(row_frame)

        return container

    def _build_rich_label(self, html_text: str) -> QLabel:
        lbl = QLabel(html_text)
        lbl.setObjectName("richBodyLabel")
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        return lbl

    # --- UI State & JSON Persistence ---

    def _get_default_ui_settings(self) -> dict:
        return {
            "column_widths": [210, 175, 130, 125, 95, 110, 110],
            "column_visual_order": [0, 1, 2, 3, 4, 5, 6],
            "splitter_sizes": [620, 430],
            "expanded_nodes": [],
            "selected_node": ""
        }

    def _load_ui_settings(self):
        defaults = self._get_default_ui_settings()
        data = None
        if self.storage:
            try:
                data = self.storage.load("config/equipment_view_settings.json", default=None)
            except Exception:
                data = None

        if not isinstance(data, dict):
            data = defaults
            if self.storage:
                try:
                    self.storage.save("config/equipment_view_settings.json", data, backup=False)
                except Exception:
                    pass

        self._restoring_ui_state = True
        try:
            hdr = self.tree.header()
            col_count = self.tree_model.columnCount()

            # 1. Restore column widths
            widths = data.get("column_widths", defaults["column_widths"])
            if isinstance(widths, list):
                for logical_idx, w in enumerate(widths):
                    if logical_idx < col_count and isinstance(w, (int, float)) and w >= 40:
                        hdr.resizeSection(logical_idx, int(w))

            # 2. Restore column visual order
            visual_order = data.get("column_visual_order", defaults["column_visual_order"])
            if isinstance(visual_order, list) and len(visual_order) == col_count:
                for target_visual_idx, logical_idx in enumerate(visual_order):
                    if 0 <= logical_idx < col_count:
                        current_visual_idx = hdr.visualIndex(logical_idx)
                        if current_visual_idx != target_visual_idx and current_visual_idx >= 0:
                            hdr.moveSection(current_visual_idx, target_visual_idx)

            # 3. Restore splitter sizes
            sp_sizes = data.get("splitter_sizes", defaults["splitter_sizes"])
            if isinstance(sp_sizes, list) and len(sp_sizes) == 2 and all(isinstance(x, (int, float)) and x > 50 for x in sp_sizes):
                self.splitter.setSizes([int(sp_sizes[0]), int(sp_sizes[1])])

            # 4. Load expanded and selected node keys
            exp_list = data.get("expanded_nodes", [])
            if isinstance(exp_list, list):
                self._expanded_keys = set(str(k) for k in exp_list if k)
            sel_node = data.get("selected_node", "")
            if isinstance(sel_node, str):
                self._selected_key = sel_node
        except Exception as e:
            print(f"Error loading equipment view settings: {e}")
        finally:
            self._restoring_ui_state = False

    def _save_ui_settings(self):
        if self._restoring_ui_state or not self.storage:
            return
        try:
            hdr = self.tree.header()
            col_count = self.tree_model.columnCount()
            widths = [hdr.sectionSize(i) for i in range(col_count)]
            visual_order = [hdr.logicalIndex(v) for v in range(col_count)]
            sp_sizes = self.splitter.sizes()
            if not self.isVisible() or any(s <= 50 for s in sp_sizes):
                existing = self.storage.load("config/equipment_view_settings.json", default=None)
                if isinstance(existing, dict) and isinstance(existing.get("splitter_sizes"), list):
                    sp_sizes = existing["splitter_sizes"]
                else:
                    sp_sizes = self._get_default_ui_settings()["splitter_sizes"]

            settings_data = {
                "column_widths": widths,
                "column_visual_order": visual_order,
                "splitter_sizes": sp_sizes,
                "expanded_nodes": sorted(list(self._expanded_keys)),
                "selected_node": self._selected_key or ""
            }
            self.storage.save("config/equipment_view_settings.json", settings_data, backup=False)
        except Exception as e:
            print(f"Error saving equipment view settings: {e}")

    def _on_header_resized(self, logicalIndex: int, oldSize: int, newSize: int):
        if not self._restoring_ui_state:
            self._save_ui_settings()

    def _on_header_moved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int):
        if not self._restoring_ui_state:
            self._save_ui_settings()

    def _on_splitter_moved(self, pos: int, index: int):
        if not self._restoring_ui_state:
            self._save_ui_settings()

    def _on_node_expanded(self, proxy_index):
        if self._restoring_ui_state:
            return
        src_idx = self.proxy_model.mapToSource(proxy_index)
        if src_idx.isValid():
            item = src_idx.internalPointer()
            key = getattr(item, "node_key", "")
            if key:
                self._expanded_keys.add(key)
                self._save_ui_settings()

    def _on_node_collapsed(self, proxy_index):
        if self._restoring_ui_state:
            return
        src_idx = self.proxy_model.mapToSource(proxy_index)
        if src_idx.isValid():
            item = src_idx.internalPointer()
            key = getattr(item, "node_key", "")
            if key and key in self._expanded_keys:
                self._expanded_keys.discard(key)
                self._save_ui_settings()

    def _capture_current_tree_state(self):
        """Captures currently expanded and selected node keys from the live tree."""
        expanded = set()

        def walk(parent_proxy_idx):
            rows = self.proxy_model.rowCount(parent_proxy_idx)
            for r in range(rows):
                p_idx = self.proxy_model.index(r, 0, parent_proxy_idx)
                if not p_idx.isValid():
                    continue
                if self.tree.isExpanded(p_idx):
                    s_idx = self.proxy_model.mapToSource(p_idx)
                    if s_idx.isValid():
                        it = s_idx.internalPointer()
                        k = getattr(it, "node_key", "")
                        if k:
                            expanded.add(k)
                    walk(p_idx)

        from PySide6.QtCore import QModelIndex
        walk(QModelIndex())
        if expanded:
            self._expanded_keys = expanded

        indexes = self.tree.selectionModel().selectedIndexes() if self.tree.selectionModel() else []
        if indexes:
            s_idx = self.proxy_model.mapToSource(indexes[0])
            if s_idx.isValid():
                it = s_idx.internalPointer()
                self._selected_key = getattr(it, "node_key", "") or self._selected_key

    def _restore_tree_state(self, focus_key: str = ""):
        """Restores expanded nodes, selection, and scroll position without collapsing user context."""
        from PySide6.QtCore import QModelIndex, QItemSelectionModel
        target_sel_key = focus_key or self._selected_key
        self._restoring_ui_state = True
        matched_proxy_idx = None

        try:
            if not self._expanded_keys:
                # Default initial expansion: expand Clients and Sites (depth 1)
                self.tree.expandToDepth(1)
                # Populate _expanded_keys from this default expansion
                def collect_initial(parent_p_idx):
                    for r in range(self.proxy_model.rowCount(parent_p_idx)):
                        p_idx = self.proxy_model.index(r, 0, parent_p_idx)
                        if self.tree.isExpanded(p_idx):
                            s_idx = self.proxy_model.mapToSource(p_idx)
                            if s_idx.isValid():
                                k = getattr(s_idx.internalPointer(), "node_key", "")
                                if k:
                                    self._expanded_keys.add(k)
                            collect_initial(p_idx)
                collect_initial(QModelIndex())
            else:
                def restore_walk(parent_p_idx):
                    nonlocal matched_proxy_idx
                    for r in range(self.proxy_model.rowCount(parent_p_idx)):
                        p_idx = self.proxy_model.index(r, 0, parent_p_idx)
                        if not p_idx.isValid():
                            continue
                        s_idx = self.proxy_model.mapToSource(p_idx)
                        if s_idx.isValid():
                            it = s_idx.internalPointer()
                            k = getattr(it, "node_key", "")
                            if k in self._expanded_keys:
                                self.tree.setExpanded(p_idx, True)
                            if target_sel_key and k == target_sel_key:
                                matched_proxy_idx = p_idx
                        restore_walk(p_idx)

                restore_walk(QModelIndex())

            if matched_proxy_idx is not None and matched_proxy_idx.isValid():
                # Ensure all ancestor nodes of matched_proxy_idx are expanded
                parent_p = matched_proxy_idx.parent()
                while parent_p.isValid():
                    self.tree.setExpanded(parent_p, True)
                    s_parent = self.proxy_model.mapToSource(parent_p)
                    if s_parent.isValid():
                        pk = getattr(s_parent.internalPointer(), "node_key", "")
                        if pk:
                            self._expanded_keys.add(pk)
                    parent_p = parent_p.parent()

                self.tree.selectionModel().setCurrentIndex(
                    matched_proxy_idx,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows
                )
                self.tree.scrollTo(matched_proxy_idx)
        finally:
            self._restoring_ui_state = False

        self._save_ui_settings()

    def refresh_data(self, initial_load: bool = False, focus_key: str = ""):
        try:
            v_scroll = self.tree.verticalScrollBar().value() if self.tree.verticalScrollBar() else 0
            if not initial_load and self.tree_model.rowCount() > 0:
                self._capture_current_tree_state()

            self.tree_model.refresh()
            self._restore_tree_state(focus_key=focus_key)

            if not focus_key and self.tree.verticalScrollBar():
                self.tree.verticalScrollBar().setValue(v_scroll)
        except Exception as e:
            print(f"Error refreshing equipment tree: {e}")

    def _on_filter_changed(self):
        query = self.search_bar.text().strip()
        type_filter = self.cb_type.currentData()
        status_filter = self.cb_status.currentData()
        bms_filter = self.cb_bms_status.currentData() if hasattr(self, 'cb_bms_status') else ""
        
        terms = [re_escape(q) for q in query.split() if q]
        if type_filter:
            type_lbl = SYSTEM_TYPE_LABELS.get(type_filter, type_filter)
            for key_st, lbl_st in SYSTEM_TYPE_LABELS.items():
                if (key_st.value if hasattr(key_st, 'value') else str(key_st)) == type_filter:
                    type_lbl = lbl_st
                    break
            terms.append(f"({re_escape(type_filter)}|{re_escape(type_lbl)})")
        if status_filter:
            st_lbl = OPERATIONAL_STATUS_LABELS.get(status_filter, status_filter)
            for key_st, lbl_st in OPERATIONAL_STATUS_LABELS.items():
                if (key_st.value if hasattr(key_st, 'value') else str(key_st)) == status_filter:
                    st_lbl = lbl_st
                    break
            terms.append(f"({re_escape(status_filter)}|{re_escape(st_lbl)})")
        if bms_filter:
            terms.append(re_escape(bms_filter))
            
        if terms:
            regex_str = ".*".join(terms)
            self.proxy_model.setFilterRegularExpression(QRegularExpression(regex_str, QRegularExpression.PatternOption.CaseInsensitiveOption))
            self._restoring_ui_state = True
            self.tree.expandAll()
            self._restoring_ui_state = False
        else:
            self.proxy_model.setFilterRegularExpression(QRegularExpression())
            self._restore_tree_state()

    def get_selected_equipment(self):
        indexes = self.tree.selectionModel().selectedIndexes()
        if not indexes:
            return None
        src_index = self.proxy_model.mapToSource(indexes[0])
        if not src_index.isValid():
            return None
        item = src_index.internalPointer()
        if getattr(item, 'node_type', '') == "EQUIPMENT" and hasattr(item, 'equipment') and item.equipment:
            return item.equipment
        return None

    def clear_detail(self):
        if hasattr(self, 'lbl_detail_icon'):
            self.lbl_detail_icon.setVisible(False)
        self.lbl_title.setText("Seleccione un equipo")
        self._clear_detail_cards()
        msg_card = QFrame()
        msg_card.setObjectName("emptyDetailCard")
        m_layout = QVBoxLayout(msg_card)
        lbl = QLabel("Haga clic en un equipo del árbol a la izquierda para ver su ficha técnica, estado operativo, historial y especificaciones.")
        lbl.setObjectName("muted")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        m_layout.addWidget(lbl)
        self.detail_content_layout.addWidget(msg_card)
        self.detail_content_layout.addStretch()

        self.btn_report_incident.setEnabled(False)
        self.btn_docs.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        if hasattr(self, 'btn_detail_pdf'):
            self.btn_detail_pdf.setEnabled(False)

    def _get_operational_status_style(self, raw_status: str, status_label: str) -> tuple[str, str]:
        st = (raw_status or "").upper()
        lbl = (status_label or "").lower()
        if st == "OPERATIONAL" or "operativo" in lbl:
            return "#10B981", "#064E3B"
        elif st == "WARNING" or "observaci" in lbl or "advertencia" in lbl:
            return "#F59E0B", "#451A03"
        elif st == "FAULT" or "falla" in lbl:
            return "#EF4444", "#450A0A"
        elif st == "IN_MAINTENANCE" or "mantenimiento" in lbl:
            return "#3B82F6", "#1E3A8A"
        else:
            return "#94A3B8", "#1E293B"

    def _get_bms_status_style(self, bms_status_val: str) -> tuple[str, str]:
        bms = (bms_status_val or "").strip()
        if bms == "Operativo":
            return "#10B981", "#064E3B"
        elif bms in ("En Falla", "Sin Control"):
            return "#EF4444", "#450A0A"
        elif bms == "Sin Grafica":
            return "#F59E0B", "#451A03"
        else:
            return "#94A3B8", "#1E293B"

    def update_detail(self, eq):
        raw_stype_icon = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
        if hasattr(self, 'lbl_detail_icon'):
            pix = IconManager.get_pixmap(f"equipment/{str(raw_stype_icon).lower()}.svg", "#38BDF8", 24)
            if not pix.isNull():
                self.lbl_detail_icon.setPixmap(pix)
                self.lbl_detail_icon.setVisible(True)
            else:
                self.lbl_detail_icon.setVisible(False)
        self.lbl_title.setText(f"{eq.tag}")
        self.btn_report_incident.setEnabled(True)
        self.btn_docs.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)
        if hasattr(self, 'btn_detail_pdf'):
            self.btn_detail_pdf.setEnabled(True)

        self._clear_detail_cards()
        
        raw_stype = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
        stype = SYSTEM_TYPE_LABELS.get(eq.system_type, SYSTEM_TYPE_LABELS.get(raw_stype, raw_stype))
        
        raw_status = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
        status_str = OPERATIONAL_STATUS_LABELS.get(eq.status, OPERATIONAL_STATUS_LABELS.get(raw_status, raw_status))
        
        raw_freq = eq.maintenance_frequency.value if hasattr(eq.maintenance_frequency, 'value') else str(eq.maintenance_frequency)
        freq_str = MAINTENANCE_FREQUENCY_LABELS.get(eq.maintenance_frequency, MAINTENANCE_FREQUENCY_LABELS.get(raw_freq, raw_freq))
        
        bms_status_val = getattr(eq, 'bms_status', 'Operativo') or 'Operativo'
        
        # Colors for Operational Status and BMS Status
        op_fg, op_bg = self._get_operational_status_style(raw_status, status_str)
        bms_fg, bms_bg = self._get_bms_status_style(bms_status_val)

        # Top Status Banner (2 native pill badges side by side)
        banner_frame = QFrame()
        banner_frame.setObjectName("eqStatusBanner")
        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        banner_layout.setSpacing(12)

        # Left column: Operational Status
        op_box = QVBoxLayout()
        op_box.setSpacing(4)
        lbl_op_hdr = QLabel("ESTADO OPERATIVO")
        lbl_op_hdr.setObjectName("kvKeyLabel")
        lbl_op_hdr.setStyleSheet("font-size: 10px; font-weight: bold; background: transparent; border: none;")
        lbl_op_pill = QLabel(f"●  {status_str}")
        lbl_op_pill.setStyleSheet(
            f"background-color: {op_bg}; color: {op_fg}; border: 1px solid {op_fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 12px;"
        )
        op_box.addWidget(lbl_op_hdr)
        op_box.addWidget(lbl_op_pill)

        # Right column: BMS Status
        bms_box = QVBoxLayout()
        bms_box.setSpacing(4)
        lbl_bms_hdr = QLabel("ESTADO BMS / CONTROL")
        lbl_bms_hdr.setObjectName("kvKeyLabel")
        lbl_bms_hdr.setStyleSheet("font-size: 10px; font-weight: bold; background: transparent; border: none;")
        lbl_bms_pill = QLabel(f"●  {bms_status_val}")
        lbl_bms_pill.setStyleSheet(
            f"background-color: {bms_bg}; color: {bms_fg}; border: 1px solid {bms_fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 12px;"
        )
        bms_box.addWidget(lbl_bms_hdr)
        bms_box.addWidget(lbl_bms_pill)

        banner_layout.addLayout(op_box, 1)
        banner_layout.addLayout(bms_box, 1)
        self.detail_content_layout.addWidget(banner_frame)

        # 1. General & Identification Card
        bms_id_val = getattr(eq, 'bms_id', '')
        bms_id_html = f"<b style='color: #38BDF8;'>{html.escape(bms_id_val)}</b>" if bms_id_val else "<i style='color: #64748B;'>No asignado</i>"
        floor_val = getattr(eq, 'floor_area', '')
        floor_html = f"<b>{html.escape(floor_val)}</b>" if floor_val else "<i style='color: #64748B;'>Sin especificar</i>"
        op_inline_html = f"<b style='color: {op_fg};'>● {html.escape(status_str)}</b>"
        bms_inline_html = f"<b style='color: {bms_fg};'>● {html.escape(bms_status_val)}</b>"

        gen_rows = [
            ("Tag / Código", f"<b style='color: #38BDF8;'>{html.escape(eq.tag)}</b>"),
            ("Tipo de Sistema", f"<b>{html.escape(stype)}</b>"),
            ("Estado Operativo", op_inline_html),
            ("Estado BMS / Control", bms_inline_html),
            ("ID / Orden BMS", bms_id_html),
            ("Piso / Nivel / Área", floor_html),
            ("Ubicación Específica", html.escape(eq.location_description) if eq.location_description else "<span style='color: #64748B;'>N/A</span>"),
            ("Fabricante / Marca", html.escape(eq.manufacturer) if eq.manufacturer else "<span style='color: #64748B;'>N/A</span>"),
            ("Modelo", html.escape(eq.model) if eq.model else "<span style='color: #64748B;'>N/A</span>"),
            ("Nro. de Serie", html.escape(eq.serial) if eq.serial else "<span style='color: #64748B;'>N/A</span>"),
        ]
        self._add_card_widget("Identificación y Ubicación", "#38BDF8", self._build_kv_widget(gen_rows))

        # 2. Technical Specifications Card (Spanish labels)
        if eq.technical_specs:
            formatted_specs = format_technical_specs(eq.system_type, eq.technical_specs)
            if formatted_specs:
                spec_rows = [
                    (lbl, f"<b>{html.escape(val)}</b>")
                    for lbl, val in formatted_specs
                ]
                self._add_card_widget("Especificaciones Técnicas", "#F59E0B", self._build_kv_widget(spec_rows))

        # 3. Maintenance & Dates Card
        maint_rows = [
            ("Frecuencia Mant.", f"<b style='color: #A78BFA;'>{html.escape(freq_str)}</b>"),
            ("Fecha Instalación", html.escape(eq.installation_date) if eq.installation_date else "<span style='color: #64748B;'>N/A</span>"),
            ("Garantía Hasta", html.escape(eq.warranty_expiry) if eq.warranty_expiry else "<span style='color: #64748B;'>N/A</span>"),
            ("Último Servicio", html.escape(eq.last_service_date) if eq.last_service_date else "<span style='color: #64748B;'>N/A</span>"),
            ("Próximo Servicio", html.escape(eq.next_service_due) if eq.next_service_due else "<span style='color: #64748B;'>N/A</span>"),
        ]
        self._add_card_widget("Planificación y Fechas", "#8B5CF6", self._build_kv_widget(maint_rows))

        # 4. Notes Card
        if eq.notes:
            notes_html = html.escape(eq.notes).replace("\n", "<br>")
            self._add_card_widget("Notas y Observaciones", "#10B981", self._build_rich_label(notes_html))

        # 5. Linked Documents from Technical Library
        if hasattr(self, 'library_service') and self.library_service:
            try:
                docs = self.library_service.get_documents_for_equipment(eq.id)
                if docs:
                    doc_items = []
                    for doc in docs:
                        cat_label = LIBRARY_CATEGORY_LABELS.get(doc.category, doc.category)
                        doc_items.append(
                            f"• <b style='color: #38BDF8;'>[{html.escape(str(cat_label))}]</b> "
                            f"<b>{html.escape(doc.title)}</b> <span style='color: #94A3B8;'>({html.escape(doc.file_name)} - {html.escape(doc.formatted_size)})</span>"
                        )
                    self._add_card_widget("Documentos y Recursos Técnicos (Librería)", "#0EA5E9", self._build_rich_label("<br>".join(doc_items)))
                else:
                    empty_docs = "<i style='color: #94A3B8;'>Sin documentos asociados. Use el botón de carpeta superior para vincular un manual o datasheet.</i>"
                    self._add_card_widget("Documentos y Recursos Técnicos (Librería)", "#475569", self._build_rich_label(empty_docs))
            except Exception as e:
                print(f"Error fetching equipment library docs: {e}")

        # 6. Spare Parts Relationship
        sp_list = getattr(eq, 'spare_parts', []) or []
        if sp_list:
            inv_parts = {}
            if self.inventory_service:
                try:
                    for p in self.inventory_service.get_all_spare_parts():
                        inv_parts[p.name.lower()] = p
                except Exception:
                    pass

            sp_items = []
            for sp in sp_list:
                sp_name = sp.get('name', '') if isinstance(sp, dict) else str(sp)
                if not sp_name:
                    continue
                
                inv_p = inv_parts.get(sp_name.lower())
                if inv_p:
                    code_info = f" <span style='color: #94A3B8;'>[{html.escape(inv_p.part_number)}]</span>" if inv_p.part_number else ""
                    unit_str = getattr(inv_p, 'unit', 'unid')
                    stock_badge = (
                        f"<font color='#10B981'><b>{inv_p.quantity} {html.escape(unit_str)} en stock</b></font>"
                        if inv_p.quantity > 0 else "<font color='#EF4444'><b>Sin stock</b></font>"
                    )
                    loc_info = f" <span style='color: #94A3B8;'>- Loc: {html.escape(inv_p.location)}</span>" if inv_p.location else ""
                    sp_items.append(f"• <b>{html.escape(inv_p.name)}</b>{code_info}: {stock_badge}{loc_info}")
                else:
                    sp_items.append(f"• <b>{html.escape(sp_name)}</b>")
            if sp_items:
                self._add_card_widget("Repuestos Asociados / Compatibles", "#14B8A6", self._build_rich_label("<br>".join(sp_items)))

        # 7. Installed / Replaced Spare Parts History (from parts_history.json)
        if self.equipment_service:
            try:
                parts_history = self.equipment_service.get_parts_history(eq.id)
                if parts_history:
                    ph_items = []
                    for ph in parts_history[:8]:
                        dt_str = ph.get('date', '')
                        if "T" in dt_str:
                            try:
                                dt = datetime.fromisoformat(dt_str)
                                dt_str = dt.strftime("%d/%m/%Y")
                            except Exception:
                                dt_str = dt_str[:10]
                                
                        p_name = ph.get('part_name', 'Repuesto')
                        p_num = f" [{ph.get('part_number')}]" if ph.get('part_number') else ""
                        qty = ph.get('quantity', 1)
                        unit = ph.get('unit', 'unid')
                        reason = ph.get('reason', 'Asignación a equipo')
                        by_user = ph.get('performed_by', '')
                        ref_doc = ph.get('reference', '')
                        notes_txt = ph.get('notes', '')
                        
                        meta_details = []
                        if ref_doc:
                            meta_details.append(f"Ref/OT: {html.escape(str(ref_doc))}")
                        if by_user:
                            meta_details.append(f"Por: {html.escape(str(by_user))}")
                        meta_str = f" <span style='color: #94A3B8;'>({' | '.join(meta_details)})</span>" if meta_details else ""
                        
                        entry_html = (
                            f"• <b>[{html.escape(str(dt_str))}]</b> "
                            f"{qty} {html.escape(str(unit))} de <b>{html.escape(str(p_name))}</b>{html.escape(p_num)} — "
                            f"<font color='#38BDF8'>{html.escape(str(reason))}</font>{meta_str}"
                        )
                        if notes_txt:
                            entry_html += f"<br>&nbsp;&nbsp;&nbsp;<i style='color: #94A3B8;'>Obs: {html.escape(str(notes_txt))}</i>"
                        ph_items.append(entry_html)
                    self._add_card_widget("Historial de Repuestos e Insumos Utilizados", "#38BDF8", self._build_rich_label("<br>".join(ph_items)))
            except Exception as e:
                print(f"Error fetching equipment parts history: {e}")

        # 8. Incident, Repair & Improvement History
        if self.incident_service:
            try:
                incidents = self.incident_service.get_incidents_for_equipment(eq.id)
                if incidents:
                    inc_items = []
                    for inc in incidents[:6]:
                        st_raw = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
                        st_color = "#10B981" if st_raw == "RESUELTA" else "#EF4444" if st_raw == "REPORTADA" else "#3B82F6" if st_raw == "EN_REPARACION" else "#F59E0B"
                        entry_html = (
                            f"• <b>[{html.escape(str(inc.reported_date))}] {html.escape(str(inc.id))}:</b> "
                            f"{html.escape(str(inc.title))} - <font color='{st_color}'><b>{html.escape(str(inc.status_display))}</b></font> "
                            f"<span style='color: #94A3B8;'>({html.escape(str(inc.type_display))})</span>"
                        )
                        if inc.action_taken:
                            entry_html += f"<br>&nbsp;&nbsp;&nbsp;<i style='color: #CBD5E1;'>Trabajo/Mejora: {html.escape(str(inc.action_taken))}</i>"
                        inc_items.append(entry_html)
                    self._add_card_widget("Historial de Averías, Reparaciones y Mejoras", "#EF4444", self._build_rich_label("<br>".join(inc_items)))
            except Exception as e:
                print(f"Error fetching equipment incidents: {e}")

        self.detail_content_layout.addStretch()

    def on_view_documents(self):
        eq = self.get_selected_equipment()
        if not eq or not self.library_service:
            return

        docs = self.library_service.get_documents_for_equipment(eq.id)
        if docs:
            menu = QMenu(self)
            for d in docs:
                cat_label = LIBRARY_CATEGORY_LABELS.get(d.category, d.category)
                act = menu.addAction(f"Abrir [{cat_label}]: {d.title}")
                act.triggered.connect(lambda ch=False, doc_id=d.id: self.library_service.open_document(doc_id))
            menu.addSeparator()
            act_add = menu.addAction("+ Subir / Vincular otro documento en Librería...")
            act_add.triggered.connect(lambda: self._upload_doc_for_equipment(eq.id))
            menu.exec(QCursor.pos())
        else:
            self._upload_doc_for_equipment(eq.id)

    def _upload_doc_for_equipment(self, eq_id: str):
        if not self.library_service:
            return
        from src.ui.dialogs.library_dialog import LibraryDialog
        dialog = LibraryDialog(
            self,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            library_service=self.library_service,
            preselected_equipment_id=eq_id
        )
        if dialog.exec():
            new_doc = dialog.get_document_data()
            src_file = dialog.get_source_file_path()
            self.library_service.save_document(new_doc, src_file)
            eq = self.get_selected_equipment()
            if eq:
                self.update_detail(eq)

    def on_report_incident(self):
        eq = self.get_selected_equipment()
        if not eq:
            QMessageBox.warning(self, "Reportar Avería", "Debe seleccionar un equipo del árbol para reportar la avería.")
            return

        from src.ui.dialogs.incident_dialog import IncidentDialog
        dialog = IncidentDialog(
            parent=self,
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            inventory_service=self.inventory_service,
            preselected_equipment_id=eq.id
        )
        if dialog.exec() and self.incident_service:
            inc = dialog.get_incident()
            self.incident_service.save_incident(inc)
            if dialog.chk_update_eq_status.isChecked():
                self.incident_service.sync_equipment_status_from_incident(inc, self.equipment_service)
                # Reload eq after update
                updated_eq = self.equipment_service.get_equipment(eq.id)
                if updated_eq:
                    eq = updated_eq
            self.refresh_data()
            self.update_detail(eq)

    def on_selection_changed(self, selected=None, deselected=None):
        indexes = self.tree.selectionModel().selectedIndexes()
        if indexes and not self._restoring_ui_state:
            s_idx = self.proxy_model.mapToSource(indexes[0])
            if s_idx.isValid():
                k = getattr(s_idx.internalPointer(), "node_key", "")
                if k and k != self._selected_key:
                    self._selected_key = k
                    self._save_ui_settings()

        eq = self.get_selected_equipment()
        if eq:
            self.update_detail(eq)
            return

        indexes = self.tree.selectionModel().selectedIndexes()
        if not indexes:
            self.clear_detail()
            return
            
        src_index = self.proxy_model.mapToSource(indexes[0])
        if not src_index.isValid():
            self.clear_detail()
            return
        item = src_index.internalPointer()
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        
        node_type = getattr(item, 'node_type', '')
        self.btn_report_incident.setEnabled(False)
        self.btn_docs.setEnabled(False)
        if hasattr(self, 'btn_detail_pdf'):
            self.btn_detail_pdf.setEnabled(False)

        if node_type == "CLIENT":
            if hasattr(self, 'lbl_detail_icon'):
                self.lbl_detail_icon.setPixmap(IconManager.get_pixmap("nav/clients.svg", "#38BDF8", 22))
                self.lbl_detail_icon.setVisible(True)
            cname = getattr(item.raw_data, 'name', '') or getattr(item.raw_data, 'company_name', '')
            self.lbl_title.setText(f"Cliente: {cname}")
            self._clear_detail_cards()
            info_rows = [
                ("RUT / ID", html.escape(getattr(item.raw_data, 'tax_id', '') or 'N/A')),
                ("Contacto", html.escape(getattr(item.raw_data, 'contact_name', '') or 'N/A')),
                ("Teléfono", html.escape(getattr(item.raw_data, 'phone', '') or 'N/A')),
                ("Email", html.escape(getattr(item.raw_data, 'email', '') or 'N/A')),
                ("Instalaciones en árbol", f"<b>{item.child_count()} sedes</b>"),
            ]
            self._add_card_widget("Información del Cliente", "#38BDF8", self._build_kv_widget(info_rows))
            self.detail_content_layout.addStretch()
        elif node_type == "SITE":
            if hasattr(self, 'lbl_detail_icon'):
                self.lbl_detail_icon.setPixmap(IconManager.get_pixmap("actions/folder.svg", "#F59E0B", 22))
                self.lbl_detail_icon.setVisible(True)
            sname = getattr(item.raw_data, 'name', '')
            self.lbl_title.setText(f"Instalación: {sname}")
            self._clear_detail_cards()
            info_rows = [
                ("Dirección", html.escape(getattr(item.raw_data, 'address', '') or 'N/A')),
                ("Ciudad", html.escape(getattr(item.raw_data, 'city', '') or 'N/A')),
                ("Contacto en Sitio", html.escape(getattr(item.raw_data, 'site_contact', '') or 'N/A')),
                ("Niveles / Equipos", f"<b>{item.child_count()} registros directos</b>"),
            ]
            self._add_card_widget("Información de la Instalación", "#38BDF8", self._build_kv_widget(info_rows))
            self.detail_content_layout.addStretch()
        elif node_type == "AREA":
            if hasattr(self, 'lbl_detail_icon'):
                self.lbl_detail_icon.setPixmap(IconManager.get_pixmap("actions/folder.svg", "#A78BFA", 22))
                self.lbl_detail_icon.setVisible(True)
            fname = item.raw_data.get("floor_name", "") if isinstance(item.raw_data, dict) else str(item.raw_data)
            self.lbl_title.setText(f"Nivel / Piso: {fname}")
            self._clear_detail_cards()
            info_rows = [
                ("Piso / Sector", f"<b>{html.escape(fname)}</b>"),
                ("Total Equipos en Nivel", f"<b style='color: #10B981;'>{item.child_count()} equipos</b>"),
            ]
            self._add_card_widget("Resumen de Nivel / Área", "#F59E0B", self._build_kv_widget(info_rows))
            self.detail_content_layout.addWidget(
                self._build_rich_label("<span style='color: #94A3B8;'>Seleccione un equipo perteneciente a este nivel para visualizar su ficha técnica completa.</span>")
            )
            self.detail_content_layout.addStretch()
        else:
            self.clear_detail()

    def on_tree_double_clicked(self, proxy_index):
        src_index = self.proxy_model.mapToSource(proxy_index)
        item = src_index.internalPointer()
        if getattr(item, 'node_type', '') == "EQUIPMENT" and hasattr(item, 'equipment') and item.equipment:
            self.on_edit_equipment()

    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        src_index = self.proxy_model.mapToSource(index)
        item = src_index.internalPointer()
        menu = QMenu(self)
        
        if getattr(item, 'node_type', '') == "EQUIPMENT":
            act_edit = menu.addAction("Editar Equipo")
            act_edit.triggered.connect(self.on_edit_equipment)
            act_del = menu.addAction("Eliminar Equipo")
            act_del.triggered.connect(self.on_delete_equipment)
            menu.addSeparator()
            act_new = menu.addAction("Nuevo Equipo...")
            act_new.triggered.connect(self.on_new_equipment)
        elif getattr(item, 'node_type', '') in ("AREA", "SITE", "CLIENT"):
            act_new = menu.addAction("Nuevo Equipo aquí...")
            act_new.triggered.connect(self.on_new_equipment)

        menu.addSeparator()
        act_expand_all = menu.addAction("Expandir Todo el Árbol")
        act_expand_all.triggered.connect(self._expand_all_and_save)
        act_collapse_floors = menu.addAction("Contraer Pisos / Niveles")
        act_collapse_floors.triggered.connect(self._collapse_to_sites)
        act_reset_cols = menu.addAction("Restaurar Ancho y Orden de Columnas")
        act_reset_cols.triggered.connect(self._reset_columns_to_default)
            
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _expand_all_and_save(self):
        self._restoring_ui_state = True
        self.tree.expandAll()
        self._restoring_ui_state = False
        self._capture_current_tree_state()
        self._save_ui_settings()

    def _collapse_to_sites(self):
        self._restoring_ui_state = True
        self.tree.collapseAll()
        self.tree.expandToDepth(1)
        self._restoring_ui_state = False
        self._expanded_keys.clear()
        self._capture_current_tree_state()
        self._save_ui_settings()

    def _reset_columns_to_default(self):
        defaults = self._get_default_ui_settings()
        self._restoring_ui_state = True
        try:
            hdr = self.tree.header()
            col_count = self.tree_model.columnCount()
            for target_visual_idx, logical_idx in enumerate(defaults["column_visual_order"]):
                if 0 <= logical_idx < col_count:
                    current_visual_idx = hdr.visualIndex(logical_idx)
                    if current_visual_idx != target_visual_idx and current_visual_idx >= 0:
                        hdr.moveSection(current_visual_idx, target_visual_idx)
            for logical_idx, w in enumerate(defaults["column_widths"]):
                if logical_idx < col_count:
                    hdr.resizeSection(logical_idx, int(w))
            self.splitter.setSizes(defaults["splitter_sizes"])
        finally:
            self._restoring_ui_state = False
        self._save_ui_settings()

    def on_new_equipment(self):
        client_id = ""
        site_id = ""
        floor_area = ""
        
        indexes = self.tree.selectionModel().selectedIndexes()
        if indexes:
            src_index = self.proxy_model.mapToSource(indexes[0])
            item = src_index.internalPointer()
            node_type = getattr(item, 'node_type', '')
            if node_type == "CLIENT" and hasattr(item, 'raw_data') and item.raw_data:
                client_id = item.raw_data.id
            elif node_type == "SITE" and hasattr(item, 'raw_data') and item.raw_data:
                site_id = item.raw_data.id
                client_id = item.raw_data.client_id
            elif node_type == "AREA" and hasattr(item, 'raw_data') and isinstance(item.raw_data, dict):
                floor_area = item.raw_data.get("floor_name", "")
                if floor_area == "Sin Nivel / General":
                    floor_area = ""
                site = item.raw_data.get("site")
                if site:
                    site_id = site.id
                    client_id = site.client_id
            elif node_type == "EQUIPMENT" and hasattr(item, 'raw_data') and item.raw_data:
                eq = item.raw_data
                site_id = eq.site_id
                client_id = eq.client_id
                floor_area = getattr(eq, 'floor_area', '')

        dialog = EquipmentDialog(
            parent=self, 
            client_service=self.client_service,
            inventory_service=self.inventory_service,
            custom_lists_service=self.custom_lists_service,
            client_id=client_id, 
            site_id=site_id, 
            floor_area=floor_area
        )
        if dialog.exec():
            eq = dialog.get_equipment()
            self.equipment_service.save_equipment(eq)
            if self.incident_service:
                self.incident_service.sync_incident_from_equipment_change(eq)
            # Ensure parent client, site, and floor nodes are in _expanded_keys
            if eq.client_id:
                self._expanded_keys.add(f"CLIENT:{eq.client_id}")
            if eq.site_id:
                self._expanded_keys.add(f"SITE:{eq.site_id}")
                fl_name = (getattr(eq, 'floor_area', '') or '').strip() or "Sin Nivel / General"
                self._expanded_keys.add(f"AREA:{eq.site_id}:{fl_name}")
            new_key = f"EQUIPMENT:{eq.id}"
            self._selected_key = new_key
            self.refresh_data(focus_key=new_key)
            self.update_detail(eq)

    def on_edit_equipment(self):
        eq = self.get_selected_equipment()
        if not eq:
            return
            
        dialog = EquipmentDialog(
            parent=self, 
            client_service=self.client_service,
            inventory_service=self.inventory_service,
            custom_lists_service=self.custom_lists_service,
            equipment=eq
        )
        if dialog.exec():
            updated = dialog.get_equipment()
            self.equipment_service.save_equipment(updated)
            if self.incident_service:
                self.incident_service.sync_incident_from_equipment_change(updated)
            if updated.client_id:
                self._expanded_keys.add(f"CLIENT:{updated.client_id}")
            if updated.site_id:
                self._expanded_keys.add(f"SITE:{updated.site_id}")
                fl_name = (getattr(updated, 'floor_area', '') or '').strip() or "Sin Nivel / General"
                self._expanded_keys.add(f"AREA:{updated.site_id}:{fl_name}")
            edit_key = f"EQUIPMENT:{updated.id}"
            self._selected_key = edit_key
            self.refresh_data(focus_key=edit_key)
            self.update_detail(updated)

    def on_delete_equipment(self):
        eq = self.get_selected_equipment()
        if not eq:
            return
            
        reply = QMessageBox.question(
            self,
            "Eliminar Equipo",
            f"¿Está seguro de que desea eliminar el equipo '{eq.tag}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.equipment_service.delete_equipment(eq.id):
                self.refresh_data()
                self.clear_detail()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el equipo.")

    def on_export_pdf_dialog(self):
        if not self.export_service:
            QMessageBox.warning(self, "Exportar PDF", "Servicio de exportación no disponible.")
            return

        from src.ui.dialogs.equipment_pdf_dialog import EquipmentPdfDialog
        dialog = EquipmentPdfDialog(
            equipment_service=self.equipment_service,
            client_service=self.client_service,
            export_service=self.export_service,
            custom_lists_service=self.custom_lists_service,
            incident_service=self.incident_service,
            library_service=self.library_service,
            parent=self
        )
        dialog.exec()

    def on_export_single_pdf(self):
        eq = self.get_selected_equipment()
        if not eq:
            return
        if not self.export_service:
            QMessageBox.warning(self, "Exportar PDF", "Servicio de exportación no disponible.")
            return

        from PySide6.QtWidgets import QFileDialog
        import os, platform, subprocess
        
        default_name = f"Ficha_Equipo_{eq.tag.replace(' ', '_')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Ficha Técnica PDF", default_name, "PDF Files (*.pdf)"
        )
        if not file_path:
            return
            
        client_name = ""
        site_name = ""
        if self.client_service:
            client = self.client_service.get_client(eq.client_id)
            if client:
                client_name = client.company_name
                if eq.site_id:
                    site = self.client_service.get_site(eq.site_id, eq.client_id)
                    if site:
                        site_name = site.name
                            
        try:
            from src.app.state_manager import StateManager
            logo_path = StateManager().get_logo_path()
            self.export_service.export_single_equipment_pdf(
                equipment=eq,
                output_path=file_path,
                logo_path=logo_path,
                client_name=client_name,
                site_name=site_name,
                incident_service=self.incident_service,
                library_service=self.library_service
            )
            QMessageBox.information(self, "Exportación Exitosa", f"La ficha técnica se ha guardado en:\n{file_path}")
            # Open PDF
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', file_path])
            else:
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo generar el PDF:\n{str(e)}")

def re_escape(s: str) -> str:
    import re
    return re.escape(s)

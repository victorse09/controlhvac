from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QInputDialog,
    QMessageBox, QGroupBox, QSplitter, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from src.core.services.custom_lists_service import (
    EQUIPMENT_DROPDOWN_MAP, EQUIPMENT_GROUP_NAMES, DEFAULT_CUSTOM_LISTS
)
from src.ui.icon_manager import IconManager
from src.ui.dialogs.bulk_equipment_widget import _create_section_card

class CustomListsWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.custom_lists_service = getattr(main_window, 'custom_lists_service', None)
        if not self.custom_lists_service and getattr(main_window, 'storage', None):
            from src.core.services.custom_lists_service import CustomListsService
            self.custom_lists_service = CustomListsService(main_window.storage)

        self.current_key = "ahu_filter_type"
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header description
        lbl_info = QLabel("Administración de listas desplegables del sistema. Seleccione una lista a la izquierda para agregar, editar o eliminar opciones:")
        lbl_info.setObjectName("kvKeyLabel")
        lbl_info.setWordWrap(True)
        main_layout.addWidget(lbl_info)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # --- Left: Categories Tree ---
        left_card, left_widget = _create_section_card("1. Categorías y Listas Desplegables", "#38BDF8")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        left_layout.addWidget(self.tree)
        splitter.addWidget(left_card)

        # --- Right: Items Management Panel ---
        right_card, right_frame = _create_section_card("2. Opciones de la Lista Seleccionada", "#F59E0B")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        self.lbl_current_title = QLabel("Opciones Disponibles")
        self.lbl_current_title.setObjectName("h3")
        right_layout.addWidget(self.lbl_current_title)

        self.items_list = QListWidget()
        self.items_list.itemDoubleClicked.connect(self._edit_item)
        right_layout.addWidget(self.items_list)

        # Action buttons
        btn_row = QHBoxLayout()
        
        self.btn_add = QPushButton("Agregar Opción")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.setIcon(IconManager.get_icon("add.svg", "#000000"))
        self.btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add.clicked.connect(self._add_item)
        btn_row.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#38BDF8"))
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.clicked.connect(self._edit_item)
        btn_row.addWidget(self.btn_edit)

        self.btn_del = QPushButton("Eliminar")
        self.btn_del.setObjectName("dangerButton")
        self.btn_del.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF"))
        self.btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_del.clicked.connect(self._delete_item)
        btn_row.addWidget(self.btn_del)

        right_layout.addLayout(btn_row)

        # Secondary row: Reorder & Reset
        sec_row = QHBoxLayout()
        
        self.btn_up = QPushButton("Subir")
        self.btn_up.setIcon(IconManager.get_icon("arrow_up.svg", "#38BDF8"))
        self.btn_up.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_up.clicked.connect(self._move_up)
        sec_row.addWidget(self.btn_up)

        self.btn_down = QPushButton("Bajar")
        self.btn_down.setIcon(IconManager.get_icon("arrow_down.svg", "#38BDF8"))
        self.btn_down.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_down.clicked.connect(self._move_down)
        sec_row.addWidget(self.btn_down)
        
        sec_row.addStretch()

        self.btn_reset = QPushButton("Restaurar por Defecto")
        self.btn_reset.setIcon(IconManager.get_icon("refresh.svg", "#F59E0B"))
        self.btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reset.clicked.connect(self._reset_current_list)
        sec_row.addWidget(self.btn_reset)

        right_layout.addLayout(sec_row)
        splitter.addWidget(right_card)

        splitter.setSizes([300, 450])

        self._populate_tree()
        self._load_current_list()

    def _populate_tree(self):
        self.tree.clear()
        first_child = None

        for eq_type, dropdowns in EQUIPMENT_DROPDOWN_MAP.items():
            group_label = EQUIPMENT_GROUP_NAMES.get(eq_type, eq_type)
            parent_item = QTreeWidgetItem(self.tree, [group_label])
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            parent_item.setIcon(0, IconManager.get_equipment_icon(eq_type, "#0EA5E9"))

            for key, title, _ in dropdowns:
                child = QTreeWidgetItem(parent_item, [title])
                child.setData(0, Qt.ItemDataRole.UserRole, key)
                child.setData(0, Qt.ItemDataRole.UserRole + 1, f"{group_label} - {title}")
                if first_child is None:
                    first_child = child

        self.tree.expandAll()
        if first_child:
            self.tree.setCurrentItem(first_child)
            self.current_key = first_child.data(0, Qt.ItemDataRole.UserRole)
            self.lbl_current_title.setText(first_child.data(0, Qt.ItemDataRole.UserRole + 1))

    def _on_tree_item_clicked(self, item, column):
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if key:
            self.current_key = key
            title = item.data(0, Qt.ItemDataRole.UserRole + 1)
            self.lbl_current_title.setText(title or "Opciones Disponibles")
            self._load_current_list()

    def _load_current_list(self):
        self.items_list.clear()
        if self.custom_lists_service:
            items = self.custom_lists_service.get_list(self.current_key)
        else:
            items = DEFAULT_CUSTOM_LISTS.get(self.current_key, [])
        for val in items:
            self.items_list.addItem(val)

    def _save_items_from_ui(self):
        if not self.custom_lists_service:
            return
        items = []
        for i in range(self.items_list.count()):
            items.append(self.items_list.item(i).text().strip())
        self.custom_lists_service.set_list(self.current_key, items)

    def _add_item(self):
        if not self.custom_lists_service:
            QMessageBox.warning(self, "Listas", "Seleccione primero una carpeta de datos válida.")
            return
        text, ok = QInputDialog.getText(
            self,
            "Nueva Opción Desplegable",
            f"Ingrese el nombre de la nueva opción para:\n{self.lbl_current_title.text()}"
        )
        if ok and text.strip():
            item_text = text.strip()
            # Check duplicate
            items = [self.items_list.item(i).text() for i in range(self.items_list.count())]
            if item_text in items:
                QMessageBox.warning(self, "Atención", "La opción ingresada ya existe en la lista.")
                return
            self.items_list.addItem(item_text)
            self._save_items_from_ui()

    def _edit_item(self):
        if not self.custom_lists_service:
            return
        current_row = self.items_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Editar", "Seleccione una opción de la lista para editar.")
            return

        curr_item = self.items_list.item(current_row)
        old_val = curr_item.text()

        text, ok = QInputDialog.getText(
            self,
            "Editar Opción Desplegable",
            "Modifique el valor de la opción:",
            text=old_val
        )
        if ok and text.strip() and text.strip() != old_val:
            curr_item.setText(text.strip())
            self._save_items_from_ui()

    def _delete_item(self):
        if not self.custom_lists_service:
            return
        current_row = self.items_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Eliminar", "Seleccione una opción de la lista para eliminar.")
            return

        curr_item = self.items_list.item(current_row)
        val = curr_item.text()

        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Desea eliminar la opción '{val}' de la lista desplegable?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.items_list.takeItem(current_row)
            self._save_items_from_ui()

    def _move_up(self):
        row = self.items_list.currentRow()
        if row > 0:
            item = self.items_list.takeItem(row)
            self.items_list.insertItem(row - 1, item)
            self.items_list.setCurrentRow(row - 1)
            self._save_items_from_ui()

    def _move_down(self):
        row = self.items_list.currentRow()
        if 0 <= row < self.items_list.count() - 1:
            item = self.items_list.takeItem(row)
            self.items_list.insertItem(row + 1, item)
            self.items_list.setCurrentRow(row + 1)
            self._save_items_from_ui()

    def _reset_current_list(self):
        if not self.custom_lists_service:
            return
        reply = QMessageBox.question(
            self,
            "Restaurar Valores por Defecto",
            f"¿Está seguro de restaurar los valores iniciales para:\n{self.lbl_current_title.text()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.custom_lists_service.reset_list_to_default(self.current_key)
            self._load_current_list()

import os
from datetime import datetime
from typing import List, Optional
from PySide6.QtWidgets import (QDialogButtonBox, QInputDialog, QSplitter, QListWidget, 
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QDateEdit, QMessageBox, QInputDialog,
    QComboBox, QGroupBox, QScrollArea, QWidget, QTableWidget, QTableWidgetItem,
    QRadioButton, QButtonGroup, QLabel, QHeaderView, QAbstractItemView,
    QCompleter
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from ...core.models.work_order import WorkOrder, ChecklistItem, DEFAULT_CHECKLISTS
from src.core.services.checklist_template_service import ChecklistTemplateService
from ...core.models.enums import (
    WORK_ORDER_TYPE_LABELS, PRIORITY_LABELS, WORK_ORDER_STATUS_LABELS,
    GuideKind, GUIDE_KIND_LABELS, ServiceType, SERVICE_TYPE_LABELS,
    WorkOrderType, Priority, WorkOrderStatus
)
from src.ui.icon_manager import IconManager



class ChecklistTemplatesDialog(QDialog):
    def __init__(self, template_service, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrar Plantillas de Checklists")
        self.setMinimumSize(800, 600)
        self.template_service = template_service
        self.selected_template = []
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Templates list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        
        self.list_templates = QListWidget()
        self.list_templates.currentRowChanged.connect(self._on_template_selected)
        
        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("Nueva")
        self.btn_new.clicked.connect(self._on_new_template)
        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.clicked.connect(self._on_delete_template)
        
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_delete)
        
        left_layout.addWidget(QLabel("Plantillas:"))
        left_layout.addWidget(self.list_templates)
        left_layout.addLayout(btn_layout)
        
        # Right side: Template details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        
        self.table_tasks = QTableWidget(0, 4)
        self.table_tasks.setAlternatingRowColors(True)
        self.table_tasks.verticalHeader().setVisible(False)
        self.table_tasks.setHorizontalHeaderLabels(["Descripción de Tarea", "Categoría", "Medición / Estado", "Unidad"])
        self.table_tasks.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        tasks_btn_layout = QHBoxLayout()
        self.btn_add_task = QPushButton("Agregar Tarea")
        self.btn_add_task.clicked.connect(self._on_add_task)
        self.btn_remove_task = QPushButton("Eliminar Tarea")
        self.btn_remove_task.clicked.connect(self._on_remove_task)
        self.btn_save = QPushButton("Guíardar Plantilla")
        self.btn_save.clicked.connect(self._on_save_template)
        
        tasks_btn_layout.addWidget(self.btn_add_task)
        tasks_btn_layout.addWidget(self.btn_remove_task)
        tasks_btn_layout.addStretch()
        tasks_btn_layout.addWidget(self.btn_save)
        
        right_layout.addWidget(QLabel("Tareas de la plantilla:"))
        right_layout.addWidget(self.table_tasks)
        right_layout.addLayout(tasks_btn_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 550])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        self.btn_use = QPushButton("Usar en esta OT")
        self.btn_use.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
        self.btn_use.clicked.connect(self.accept)
        
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.clicked.connect(self.reject)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_close)
        bottom_layout.addWidget(self.btn_use)
        
        layout.addLayout(bottom_layout)

    def _load_templates(self):
        self.list_templates.clear()
        if not self.template_service: return
        templates = self.template_service.get_all_templates()
        for name in templates.keys():
            self.list_templates.addItem(name)

    def _on_template_selected(self, row):
        if row < 0: return
        name = self.list_templates.item(row).text()
        tasks = self.template_service.get_template(name)
        
        self.table_tasks.setRowCount(0)
        for t in tasks:
            r = self.table_tasks.rowCount()
            self.table_tasks.insertRow(r)
            self.table_tasks.setItem(r, 0, QTableWidgetItem(t.get('description', '')))
            self.table_tasks.setItem(r, 1, QTableWidgetItem(t.get('category', '')))
            self.table_tasks.setItem(r, 2, QTableWidgetItem(t.get('measurement', 'N/A')))
            self.table_tasks.setItem(r, 3, QTableWidgetItem(t.get('unit', '')))
            
    def _on_new_template(self):
        name, ok = QInputDialog.getText(self, "Nueva Plantilla", "Nombre de la plantilla:")
        if ok and name:
            self.list_templates.addItem(name)
            self.list_templates.setCurrentRow(self.list_templates.count() - 1)
            self.table_tasks.setRowCount(0)
            
    def _on_delete_template(self):
        item = self.list_templates.currentItem()
        if not item: return
        name = item.text()
        reply = QMessageBox.question(self, "Eliminar", f"Seguro que desea eliminar la plantilla '{name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            self.template_service.delete_template(name)
            self._load_templates()
            self.table_tasks.setRowCount(0)
            
    def _on_add_task(self):
        r = self.table_tasks.rowCount()
        self.table_tasks.insertRow(r)
        self.table_tasks.setItem(r, 0, QTableWidgetItem("Nueva tarea"))
        self.table_tasks.setItem(r, 1, QTableWidgetItem("Mecánico"))
        self.table_tasks.setItem(r, 2, QTableWidgetItem("N/A"))
        self.table_tasks.setItem(r, 3, QTableWidgetItem(""))
        self.table_tasks.editItem(self.table_tasks.item(r, 0))

    def _on_remove_task(self):
        selected = self.table_tasks.selectionModel().selectedRows()
        if selected:
            for idx in sorted([s.row() for s in selected], reverse=True):
                self.table_tasks.removeRow(idx)

    def _on_save_template(self):
        item = self.list_templates.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Debe seleccionar o crear una plantilla primero.")
            return
        name = item.text()
        tasks = []
        for i in range(self.table_tasks.rowCount()):
            tasks.append({
                "description": self.table_tasks.item(i, 0).text() if self.table_tasks.item(i, 0) else "",
                "category": self.table_tasks.item(i, 1).text() if self.table_tasks.item(i, 1) else "",
                "measurement": self.table_tasks.item(i, 2).text() if self.table_tasks.item(i, 2) else "",
                "unit": self.table_tasks.item(i, 3).text() if self.table_tasks.item(i, 3) else ""
            })
        if self.template_service:
            self.template_service.save_template(name, tasks)
            QMessageBox.information(self, "Éxito", "Plantilla guardada correctamente.")

    def accept(self):
        # Extract selected template tasks
        item = self.list_templates.currentItem()
        if not item:
            QMessageBox.warning(self, "Atención", "Debe seleccionar una plantilla para usarla.")
            return
            
        self.selected_template = []
        for i in range(self.table_tasks.rowCount()):
            self.selected_template.append({
                "description": self.table_tasks.item(i, 0).text() if self.table_tasks.item(i, 0) else "",
                "category": self.table_tasks.item(i, 1).text() if self.table_tasks.item(i, 1) else "",
                "measurement": self.table_tasks.item(i, 2).text() if self.table_tasks.item(i, 2) else "",
                "unit": self.table_tasks.item(i, 3).text() if self.table_tasks.item(i, 3) else ""
            })
        super().accept()


from PySide6.QtWidgets import QCheckBox

class PdfOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Exportación PDF")
        self.setMinimumWidth(400)
        
        self.options = {
            'print_general': True,
            'add_signature': True,
            'manual_checklist': False,
            'manual_materials': False,
            'include_history': False
        }
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.chk_general = QCheckBox("Imprimir la OT en general (datos actuales)")
        self.chk_general.setChecked(True)
        
        self.chk_signature = QCheckBox("Agregar espacio firma de cliente")
        self.chk_signature.setChecked(True)
        
        self.chk_manual_check = QCheckBox("Crear OT para llenado de checklist/mediciones a mano")
        
        self.chk_manual_mat = QCheckBox("Crear OT para registro de partes y piezas a mano")
        
        self.chk_history = QCheckBox("Incluir resumen de las dos últimas guías realizadas al equipo")
        
        layout.addWidget(QLabel("Seleccione qué desea incluir en el PDF:"))
        layout.addWidget(self.chk_general)
        layout.addWidget(self.chk_signature)
        layout.addWidget(self.chk_manual_check)
        layout.addWidget(self.chk_manual_mat)
        layout.addWidget(self.chk_history)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def accept(self):
        self.options['print_general'] = self.chk_general.isChecked()
        self.options['add_signature'] = self.chk_signature.isChecked()
        self.options['manual_checklist'] = self.chk_manual_check.isChecked()
        self.options['manual_materials'] = self.chk_manual_mat.isChecked()
        self.options['include_history'] = self.chk_history.isChecked()
        super().accept()

class SelectMaterialDialog(QDialog):
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Repuesto/Material")
        self.setMinimumWidth(400)
        self.inventory_service = inventory_service
        
        self.selected_name = ""
        self.selected_code = ""
        self.selected_unit = "unid"
        self.selected_qty = "1"
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.combo_part = QComboBox()
        self.combo_part.setEditable(True)
        self.combo_part.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Populate with parts
        if self.inventory_service:
            parts = self.inventory_service.get_all_spare_parts()
            # We want to display name, and keep code as userdata
            self.combo_part.addItem("", "") # empty manual option
            for p in parts:
                self.combo_part.addItem(f"{p.name} ({p.part_number})", p)
                
        self.combo_part.currentIndexChanged.connect(self._on_part_selected)
        
        self.edit_name = QLineEdit()
        self.edit_code = QLineEdit()
        self.edit_qty = QLineEdit("1")
        self.edit_unit = QLineEdit("unid")
        
        form_layout.addRow("Buscar / Seleccionar:", self.combo_part)
        form_layout.addRow("Nombre/Descripción:", self.edit_name)
        form_layout.addRow("Código / N° Parte:", self.edit_code)
        form_layout.addRow("Cantidad:", self.edit_qty)
        form_layout.addRow("Unidad:", self.edit_unit)
        
        layout.addLayout(form_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def _on_part_selected(self, index):
        if index > 0:
            part = self.combo_part.itemData(index)
            if part:
                self.edit_name.setText(part.name)
                self.edit_code.setText(part.part_number)
                self.edit_unit.setText("unid") # You can fetch unit if part has it
        
    def accept(self):
        self.selected_name = self.edit_name.text().strip()
        self.selected_code = self.edit_code.text().strip()
        self.selected_qty = self.edit_qty.text().strip()
        self.selected_unit = self.edit_unit.text().strip()
        
        if not self.selected_name:
            QMessageBox.warning(self, "Atención", "Debe ingresar un nombre o descripcin.")
            return
            
        super().accept()

class WorkOrderDialog(QDialog):
    def __init__(
        self, 
        parent=None, 
        equipment_list=None, 
        work_order: Optional[WorkOrder] = None, 
        guide_kind: str = GuideKind.SERVICE.value,
        preassigned_id: str = "",
        incident_id: str = "",
        inventory_service=None,
        client_service=None,
        technician_service=None,
        export_service=None,
        read_only: Optional[bool] = None,
        preselected_equipment_id: str = "",
        initial_title: str = "",
        initial_diagnosis: str = "",
        initial_technician: str = "",
        initial_priority: str = ""
    ):
        super().__init__(parent)
        self.equipment_list = equipment_list or []
        self.work_order = work_order
        self.preassigned_id = preassigned_id
        self.incident_id = incident_id
        self.inventory_service = inventory_service
        self.client_service = client_service
        self.technician_service = technician_service
        self.export_service = export_service
        if self.technician_service is None and hasattr(parent, 'technician_service'):
            self.technician_service = parent.technician_service
        if self.export_service is None and hasattr(parent, 'export_service'):
            self.export_service = parent.export_service
            
        self.template_service = ChecklistTemplateService(self.inventory_service.storage) if self.inventory_service else None
        self.start_date_str = ""
        self.completed_date_str = ""
        self.preselected_equipment_id = preselected_equipment_id
        self.initial_title = initial_title
        self.initial_diagnosis = initial_diagnosis
        self.initial_technician = initial_technician
        self.initial_priority = initial_priority
        
        # Determine guide kind
        if work_order:
            self.guide_kind = getattr(work_order, 'guide_kind', '') or (
                GuideKind.SERVICE.value if (work_order.id and work_order.id.startswith("OTS")) else GuideKind.MAINTENANCE.value
            )
        else:
            self.guide_kind = guide_kind

        # Start in read-only / view mode if opening existing work order
        self.is_read_only = (work_order is not None) if read_only is None else read_only
        self.resize(780, 840)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(8, 8, 8, 8)

        self._setup_header_banner()
        self._setup_equipment_section()
        self._setup_service_details_section()
        self._setup_tasks_section()
        self._setup_materials_section()
        self._setup_additional_notes_section()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        # Operational State buttons (inside the dialog)
        self.btn_cancel_wo = QPushButton("Anular Guía")
        self.btn_cancel_wo.setObjectName("dangerButton")
        self.btn_cancel_wo.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_cancel_wo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel_wo.setToolTip("Cancelar o anular esta orden de trabajo indicando el motivo")
        self.btn_cancel_wo.clicked.connect(self._on_cancel_work_clicked)
        
        self.btn_start_wo = QPushButton(" Iniciar Trabajo")
        self.btn_start_wo.setStyleSheet("background-color: #0284C7; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        self.btn_start_wo.setIcon(IconManager.get_icon("tools.svg", "#FFFFFF", 16))
        self.btn_start_wo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_start_wo.setToolTip("Iniciar atención técnica y habilitar el llenado de diagnóstico, trabajos y repuestos")
        self.btn_start_wo.clicked.connect(self._on_start_work_clicked)
        
        self.btn_complete_wo = QPushButton(" Completar Trabajo")
        self.btn_complete_wo.setStyleSheet("background-color: #059669; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        self.btn_complete_wo.setIcon(IconManager.get_icon("check.svg", "#FFFFFF", 16))
        self.btn_complete_wo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_complete_wo.setToolTip("Dar por finalizado y completado el servicio o mantenimiento")
        self.btn_complete_wo.clicked.connect(self._on_complete_work_clicked)
        
        btn_layout.addWidget(self.btn_cancel_wo)
        btn_layout.addWidget(self.btn_start_wo)
        btn_layout.addWidget(self.btn_complete_wo)
        btn_layout.addStretch()
        
        # Export PDF Button
        self.btn_export_pdf = QPushButton(" Generar PDF")
        self.btn_export_pdf.setIcon(IconManager.get_icon("download.svg", "#FFFFFF", 16))
        self.btn_export_pdf.setStyleSheet("background-color: #F15A29; color: #FFFFFF; font-weight: bold; padding: 6px 14px;")
        self.btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_pdf.clicked.connect(self._on_export_pdf_clicked)
        
        # View Mode Buttons
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_export_pdf)
        btn_layout.addWidget(self.btn_close)
        
        self.btn_edit_mode = QPushButton("Modificar Formulario")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#38BDF8", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))
        
        # Edit / New Mode Buttons
        self.btn_cancel = QPushButton("Descartar Cambios")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(btn_layout)

        if self.work_order:
            self._load_data()
        else:
            self._init_new_defaults()

        self.set_read_only(self.is_read_only)

    def _setup_header_banner(self):
        from PySide6.QtWidgets import QFrame
        banner = QFrame()
        banner.setObjectName("dialogHeaderBanner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        
        is_service = (self.guide_kind == GuideKind.SERVICE.value)
        icon_name = "tools.svg" if is_service else "calendar.svg"
        color = "#38BDF8" if is_service else "#10B981"
        guide_name = "GUÍA DE SERVICIO TÉCNICO (OTS)" if is_service else "GUÍA DE MANTENIMIENTO PREVENTIVO (OTM)"
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon(icon_name, color, 24).pixmap(24, 24))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        
        code_text = self.work_order.id if self.work_order else (self.preassigned_id or (f"OTS##### (Automático)" if is_service else f"OTM##### (Automático)"))
        inc_badge = f" &nbsp;|&nbsp; <span style='color: #F59E0B; font-weight: bold;'>Avería: {self.incident_id}</span>" if self.incident_id else ""
        self.lbl_banner_title = QLabel(f"<b>{guide_name}</b> &nbsp;|&nbsp; <span style='color: {color};'>{code_text}</span>{inc_badge}")
        self.lbl_banner_title.setStyleSheet("font-size: 13.5px; background: transparent; border: none;")
        
        banner_layout.addWidget(lbl_icon)
        banner_layout.addWidget(self.lbl_banner_title, 1)
        
        self.layout.addWidget(banner)

    def _setup_equipment_section(self):
        from src.ui.dialogs.equipment_dialog import _create_dialog_card
        self.gb_equip, eq_body = _create_dialog_card("1. Información del Equipo y Ubicación", "#38BDF8")
        eq_layout = QVBoxLayout(eq_body)
        eq_layout.setContentsMargins(16, 14, 16, 16)
        eq_layout.setSpacing(10)
        
        # Radio buttons for Registered vs Manual equipment (especially for Service guides)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(16)
        self.rb_registered = QRadioButton("Equipo Registrado en Sistema")
        self.rb_manual = QRadioButton("Ingreso Manual (Servicio Esporádico / No Registrado)")
        self.rb_registered.setChecked(True)
        
        self.equip_mode_group = QButtonGroup(self)
        self.equip_mode_group.addButton(self.rb_registered, 1)
        self.equip_mode_group.addButton(self.rb_manual, 2)
        self.equip_mode_group.buttonToggled.connect(self._on_equipment_mode_toggled)
        
        mode_layout.addWidget(self.rb_registered)
        mode_layout.addWidget(self.rb_manual)
        mode_layout.addStretch()
        eq_layout.addLayout(mode_layout)

        # Form for Registered Equipment
        self.widget_registered = QWidget()
        fl_reg = QFormLayout(self.widget_registered)
        fl_reg.setContentsMargins(0, 4, 0, 0)
        
        self.equipo_combo = QComboBox()
        self.equipo_combo.setEditable(True)
        self.equipo_combo.addItem("-- Seleccione un equipo --", None)
        for eq in self.equipment_list:
            display_text = f"{eq.tag} | {eq.system_type} - {eq.manufacturer} {eq.model_number}"
            self.equipo_combo.addItem(display_text, eq)
        self.equipo_combo.currentIndexChanged.connect(self._on_equipment_combo_changed)
        fl_reg.addRow("Seleccionar Equipo *:", self.equipo_combo)
        
        self.lbl_reg_details = QLabel("Ubicación: - | Cliente: - | Tipo: -")
        self.lbl_reg_details.setStyleSheet("color: #94A3B8; font-size: 11px; margin-left: 2px;")
        fl_reg.addRow("", self.lbl_reg_details)
        
        eq_layout.addWidget(self.widget_registered)

        # Form for Manual Equipment
        self.widget_manual = QWidget()
        fl_man = QFormLayout(self.widget_manual)
        fl_man.setContentsMargins(0, 4, 0, 0)
        
        self.manual_tag_edit = QLineEdit()
        self.manual_tag_edit.setPlaceholderText("Ej: UMA-05, Chiller Trane, Split Inverter...")
        
        self.manual_client_edit = QLineEdit()
        self.manual_client_edit.setPlaceholderText("Nombre del cliente o empresa")
        
        self.manual_site_edit = QLineEdit()
        self.manual_site_edit.setPlaceholderText("Instalación / Sede")
        
        self.manual_location_edit = QLineEdit()
        self.manual_location_edit.setPlaceholderText("Ej: Piso 3 - Sala de Servidores, Azotea Torre A...")
        
        fl_man.addRow("Nombre/Tag del Equipo *:", self.manual_tag_edit)
        fl_man.addRow("Cliente:", self.manual_client_edit)
        fl_man.addRow("Instalación / Sede:", self.manual_site_edit)
        fl_man.addRow("Ubicación Específica:", self.manual_location_edit)
        
        self.widget_manual.setVisible(False)
        eq_layout.addWidget(self.widget_manual)
        
        self.layout.addWidget(self.gb_equip)

    def _setup_service_details_section(self):
        from src.ui.dialogs.equipment_dialog import _create_dialog_card
        self.gb_general, gen_body = _create_dialog_card("2. Datos del Servicio / Orden de Trabajo", "#F59E0B")
        fl = QFormLayout(gen_body)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setSpacing(8)
        
        self.titulo_edit = QLineEdit()
        self.titulo_edit.setPlaceholderText("Título o resumen breve del servicio")
        
        # Service Type (for OTS) or Work Order Type
        self.tipo_servicio_combo = QComboBox()
        for st_val, st_lbl in SERVICE_TYPE_LABELS.items():
            self.tipo_servicio_combo.addItem(st_lbl, st_val)
            
        self.tipo_ot_combo = QComboBox()
        for t, label in WORK_ORDER_TYPE_LABELS.items():
            val = t.value if hasattr(t, 'value') else str(t)
            self.tipo_ot_combo.addItem(label, val)
            
        # Priority & Status
        self.prioridad_combo = QComboBox()
        for p, label in PRIORITY_LABELS.items():
            val = p.value if hasattr(p, 'value') else str(p)
            self.prioridad_combo.addItem(label, val)
            
        self.estado_combo = QComboBox()
        for s, label in WORK_ORDER_STATUS_LABELS.items():
            val = s.value if hasattr(s, 'value') else str(s)
            self.estado_combo.addItem(label, val)
            
        # Dates and Technician
        self.fecha_prog = QDateEdit()
        self.fecha_prog.setCalendarPopup(True)
        self.fecha_prog.setDate(QDate.currentDate())
        
        self.fecha_limite = QDateEdit()
        self.fecha_limite.setCalendarPopup(True)
        self.fecha_limite.setDate(QDate.currentDate().addDays(7))
        
        self.tecnico_edit = QLineEdit()
        self.tecnico_edit.setPlaceholderText("Nombre del técnico o responsable asignado")
        if self.technician_service:
            tech_names = self.technician_service.get_technician_names()
            if tech_names:
                completer = QCompleter(tech_names, self)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.tecnico_edit.setCompleter(completer)

        # Diagnosis and Work Performed
        self.diagnostico_edit = QTextEdit()
        self.diagnostico_edit.setMaximumHeight(65)
        self.diagnostico_edit.setPlaceholderText("Síntomas observados, falla reportada o diagnóstico inicial...")

        self.trabajo_edit = QTextEdit()
        self.trabajo_edit.setMaximumHeight(65)
        self.trabajo_edit.setPlaceholderText("Detalle de las reparaciones o acciones correctivas ejecutadas...")

        fl.addRow("Título *:", self.titulo_edit)
        
        if self.guide_kind == GuideKind.SERVICE.value:
            fl.addRow("Tipo de Servicio *:", self.tipo_servicio_combo)
        else:
            fl.addRow("Tipo de OT:", self.tipo_ot_combo)
            
        fl.addRow("Prioridad:", self.prioridad_combo)
        fl.addRow("Estado:", self.estado_combo)
        fl.addRow("Fecha Programada:", self.fecha_prog)
        fl.addRow("Fecha Límite:", self.fecha_limite)
        fl.addRow("Técnico Asignado:", self.tecnico_edit)
        fl.addRow("Diagnóstico / Motivo:", self.diagnostico_edit)
        fl.addRow("Trabajos Realizados:", self.trabajo_edit)
        
        self.layout.addWidget(self.gb_general)

    def _setup_tasks_section(self):
        from src.ui.dialogs.equipment_dialog import _create_dialog_card
        self.gb_tasks, tasks_body = _create_dialog_card("3. Checklist de Tareas / Procedimiento", "#10B981")
        vl = QVBoxLayout(tasks_body)
        vl.setContentsMargins(16, 14, 16, 16)
        vl.setSpacing(8)
        
        # Action buttons for tasks
        tb_layout = QHBoxLayout()
        tb_layout.setSpacing(6)
        
        self.btn_add_task = QPushButton("Agregar Tarea")
        self.btn_add_task.setIcon(IconManager.get_icon("add.svg", "#38BDF8", 14))
        self.btn_add_task.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_task.clicked.connect(self._on_add_task_row)
        
        self.btn_remove_task = QPushButton("Eliminar Tarea")
        self.btn_remove_task.setIcon(IconManager.get_icon("delete.svg", "#EF4444", 14))
        self.btn_remove_task.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remove_task.clicked.connect(self._on_remove_task_row)
        
        self.btn_templates = QPushButton("Plantillas...")
        self.btn_templates.setIcon(IconManager.get_icon("settings.svg", "#10B981", 14))
        self.btn_templates.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_templates.clicked.connect(self._on_open_templates)

        tb_layout.addWidget(QLabel("Lista de tareas a verificar o ejecutar:"))
        tb_layout.addStretch()
        tb_layout.addWidget(self.btn_add_task)
        tb_layout.addWidget(self.btn_remove_task)
        tb_layout.addWidget(self.btn_templates)
        vl.addLayout(tb_layout)
        
        self.table_tasks = QTableWidget(0, 4)
        self.table_tasks.setAlternatingRowColors(True)
        self.table_tasks.verticalHeader().setVisible(False)
        self.table_tasks.setHorizontalHeaderLabels(["Descripción de Tarea", "Categoría", "Medición / Estado", "Unidad"])
        self.table_tasks.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_tasks.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_tasks.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_tasks.verticalHeader().setDefaultSectionSize(36)
        self.table_tasks.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_tasks.setMinimumHeight(130)
        vl.addWidget(self.table_tasks)
        
        self.layout.addWidget(self.gb_tasks)

    def _setup_materials_section(self):
        from src.ui.dialogs.equipment_dialog import _create_dialog_card
        self.gb_materials, mat_body = _create_dialog_card("4. Materiales y Repuestos Utilizados", "#14B8A6")
        vl = QVBoxLayout(mat_body)
        vl.setContentsMargins(16, 14, 16, 16)
        vl.setSpacing(8)
        
        mat_btn_layout = QHBoxLayout()
        mat_btn_layout.setSpacing(6)
        
        self.btn_add_material = QPushButton("Agregar Repuesto/Material")
        self.btn_add_material.setIcon(IconManager.get_icon("add.svg", "#38BDF8", 14))
        self.btn_add_material.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_material.clicked.connect(self._on_add_material_row)
        
        self.btn_remove_material = QPushButton("Eliminar Fila")
        self.btn_remove_material.setIcon(IconManager.get_icon("delete.svg", "#EF4444", 14))
        self.btn_remove_material.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_remove_material.clicked.connect(self._on_remove_material_row)
        
        mat_btn_layout.addWidget(QLabel("Registro de insumos, filtros, correas, piezas:"))
        mat_btn_layout.addStretch()
        mat_btn_layout.addWidget(self.btn_add_material)
        mat_btn_layout.addWidget(self.btn_remove_material)
        vl.addLayout(mat_btn_layout)
        
        self.table_materials = QTableWidget(0, 4)
        self.table_materials.setAlternatingRowColors(True)
        self.table_materials.verticalHeader().setVisible(False)
        self.table_materials.setHorizontalHeaderLabels(["Descripción / Nombre Repuesto", "Código / N° Parte", "Cantidad", "Unidad"])
        self.table_materials.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_materials.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_materials.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_materials.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_materials.verticalHeader().setDefaultSectionSize(36)
        self.table_materials.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_materials.setMinimumHeight(110)
        vl.addWidget(self.table_materials)
        
        self.layout.addWidget(self.gb_materials)

    def _setup_additional_notes_section(self):
        from src.ui.dialogs.equipment_dialog import _create_dialog_card
        gb, notes_body = _create_dialog_card("5. Observaciones y Conclusiones", "#8B5CF6")
        fl = QFormLayout(notes_body)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setSpacing(8)
        
        self.obs_edit = QTextEdit()
        self.obs_edit.setMaximumHeight(65)
        self.obs_edit.setPlaceholderText("Observaciones generales, recomendaciones al cliente...")
        fl.addRow("Observaciones:", self.obs_edit)
        
        self.layout.addWidget(gb)

    def _on_equipment_mode_toggled(self, button, checked):
        if not checked: return
        is_manual = (button == self.rb_manual)
        self.widget_registered.setVisible(not is_manual)
        self.widget_manual.setVisible(is_manual)

    def _on_equipment_combo_changed(self):
        idx = self.equipo_combo.currentIndex()
        if idx > 0:
            eq = self.equipo_combo.itemData(idx)
            if eq:
                loc = eq.location_description or eq.floor_area or "Sin ubicación"
                self.lbl_reg_details.setText(f"Ubicación: <b>{loc}</b> | Fabricante: <b>{eq.manufacturer}</b> | Modelo: <b>{eq.model_number}</b>")
                
                # Auto-fill default checklists for maintenance if new
                if not self.work_order and self.table_tasks.rowCount() == 0 and eq.system_type in DEFAULT_CHECKLISTS:
                    tasks = DEFAULT_CHECKLISTS[eq.system_type]
                    for task in tasks:
                        row = self.table_tasks.rowCount()
                        self.table_tasks.insertRow(row)
                        self.table_tasks.setItem(row, 0, QTableWidgetItem(task.get("description", "")))
                        self.table_tasks.setItem(row, 1, QTableWidgetItem(task.get("category", "")))
                        self.table_tasks.setItem(row, 2, QTableWidgetItem(""))
                        self.table_tasks.setItem(row, 3, QTableWidgetItem(task.get("unit", "")))
        else:
            self.lbl_reg_details.setText("Ubicación: - | Cliente: - | Tipo: -")

    def _on_open_templates(self):
        if not self.template_service: return
        dialog = ChecklistTemplatesDialog(self.template_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Append tasks from template
            for task in dialog.selected_template:
                row = self.table_tasks.rowCount()
                self.table_tasks.insertRow(row)
                self.table_tasks.setItem(row, 0, QTableWidgetItem(task.get('description', '')))
                self.table_tasks.setItem(row, 1, QTableWidgetItem(task.get('category', '')))
                self.table_tasks.setItem(row, 2, QTableWidgetItem(task.get('measurement', 'N/A')))
                self.table_tasks.setItem(row, 3, QTableWidgetItem(task.get('unit', '')))

    def _on_add_task_row(self):
        row = self.table_tasks.rowCount()
        self.table_tasks.insertRow(row)
        self.table_tasks.setItem(row, 0, QTableWidgetItem("Nueva tarea"))
        self.table_tasks.setItem(row, 1, QTableWidgetItem("General"))
        self.table_tasks.setItem(row, 2, QTableWidgetItem(""))
        self.table_tasks.setItem(row, 3, QTableWidgetItem(""))
        self.table_tasks.editItem(self.table_tasks.item(row, 0))

    def _on_remove_task_row(self):
        selected = self.table_tasks.selectionModel().selectedRows()
        if selected:
            for idx in sorted([s.row() for s in selected], reverse=True):
                self.table_tasks.removeRow(idx)
        elif self.table_tasks.rowCount() > 0:
            self.table_tasks.removeRow(self.table_tasks.rowCount() - 1)

    def _on_add_material_row(self):
        dialog = SelectMaterialDialog(self.inventory_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            row = self.table_materials.rowCount()
            self.table_materials.insertRow(row)
            self.table_materials.setItem(row, 0, QTableWidgetItem(dialog.selected_name))
            self.table_materials.setItem(row, 1, QTableWidgetItem(dialog.selected_code))
            self.table_materials.setItem(row, 2, QTableWidgetItem(dialog.selected_qty))
            self.table_materials.setItem(row, 3, QTableWidgetItem(dialog.selected_unit))

    def _on_remove_material_row(self):
        selected = self.table_materials.selectionModel().selectedRows()
        if selected:
            for idx in sorted([s.row() for s in selected], reverse=True):
                self.table_materials.removeRow(idx)
        elif self.table_materials.rowCount() > 0:
            self.table_materials.removeRow(self.table_materials.rowCount() - 1)

    def _init_new_defaults(self):
        if self.guide_kind == GuideKind.SERVICE.value:
            self.titulo_edit.setText(self.initial_title or "Servicio Técnico / Reparación")
            idx = self.tipo_servicio_combo.findData(ServiceType.REPARACION.value)
            if idx >= 0: self.tipo_servicio_combo.setCurrentIndex(idx)
        else:
            self.titulo_edit.setText(self.initial_title or "Mantenimiento Preventivo Periódico")
            idx = self.tipo_ot_combo.findData(WorkOrderType.PREVENTIVE.value)
            if idx >= 0: self.tipo_ot_combo.setCurrentIndex(idx)

        if self.initial_diagnosis:
            self.diagnostico_edit.setPlainText(self.initial_diagnosis)
        if self.initial_technician:
            self.tecnico_edit.setText(self.initial_technician)
        if self.initial_priority:
            idx = self.prioridad_combo.findData(self.initial_priority)
            if idx >= 0: self.prioridad_combo.setCurrentIndex(idx)

        if self.preselected_equipment_id:
            self.rb_registered.setChecked(True)
            for i in range(self.equipo_combo.count()):
                eq = self.equipo_combo.itemData(i)
                if eq and eq.id == self.preselected_equipment_id:
                    self.equipo_combo.setCurrentIndex(i)
                    break

    def _load_data(self):
        wo = self.work_order
        if not wo: return
        
        self.titulo_edit.setText(wo.title or "")
        
        # Load guide kind
        self.guide_kind = getattr(wo, 'guide_kind', '') or (
            GuideKind.SERVICE.value if (wo.id and wo.id.startswith("OTS")) else GuideKind.MAINTENANCE.value
        )
        
        # Manual vs Registered
        is_manual = getattr(wo, 'is_manual_equipment', False)
        if is_manual or (not wo.equipment_id and wo.manual_equipment_tag):
            self.rb_manual.setChecked(True)
            self.manual_tag_edit.setText(wo.manual_equipment_tag or wo.equipment_tag or "")
            self.manual_client_edit.setText(getattr(wo, 'manual_client', '') or wo.client_name or "")
            self.manual_site_edit.setText(getattr(wo, 'manual_site', '') or wo.site_name or "")
            self.manual_location_edit.setText(getattr(wo, 'manual_location', '') or "")
        else:
            self.rb_registered.setChecked(True)
            for i in range(self.equipo_combo.count()):
                eq = self.equipo_combo.itemData(i)
                if eq and eq.id == wo.equipment_id:
                    self.equipo_combo.setCurrentIndex(i)
                    break

        # Service type / OT type
        st_val = getattr(wo, 'service_type', '')
        if st_val:
            idx = self.tipo_servicio_combo.findData(st_val)
            if idx >= 0: self.tipo_servicio_combo.setCurrentIndex(idx)
            
        wo_type = wo.work_order_type or wo.type
        idx = self.tipo_ot_combo.findData(wo_type.value if hasattr(wo_type, 'value') else str(wo_type))
        if idx >= 0: self.tipo_ot_combo.setCurrentIndex(idx)
        
        # Priority & Status
        idx = self.prioridad_combo.findData(wo.priority.value if hasattr(wo.priority, 'value') else str(wo.priority))
        if idx >= 0: self.prioridad_combo.setCurrentIndex(idx)
        
        idx = self.estado_combo.findData(wo.status.value if hasattr(wo.status, 'value') else str(wo.status))
        if idx >= 0: self.estado_combo.setCurrentIndex(idx)
        
        if wo.scheduled_date:
            try: self.fecha_prog.setDate(QDate.fromString(wo.scheduled_date[:10], Qt.DateFormat.ISODate))
            except: pass
            
        if wo.due_date:
            try: self.fecha_limite.setDate(QDate.fromString(wo.due_date[:10], Qt.DateFormat.ISODate))
            except: pass
            
        self.tecnico_edit.setText(wo.assigned_technician or getattr(wo, 'assigned_to', '') or "")
        self.diagnostico_edit.setPlainText(getattr(wo, 'diagnosis', '') or wo.description or "")
        self.trabajo_edit.setPlainText(getattr(wo, 'work_performed', '') or "")
        self.incident_id = getattr(wo, 'incident_id', '') or self.incident_id
        self.start_date_str = getattr(wo, 'start_date', '') or ""
        self.completed_date_str = getattr(wo, 'completed_date', '') or ""
        self.obs_edit.setPlainText(getattr(wo, 'observations', '') or "")

        # Tasks table
        self.table_tasks.setRowCount(0)
        for cl in (wo.checklist or []):
            row = self.table_tasks.rowCount()
            self.table_tasks.insertRow(row)
            desc = cl.description if hasattr(cl, 'description') else cl.get('description', '')
            cat = cl.category if hasattr(cl, 'category') else cl.get('category', '')
            val = cl.measured_value if hasattr(cl, 'measured_value') else cl.get('measured_value', '')
            unit = cl.unit if hasattr(cl, 'unit') else cl.get('unit', '')
            
            self.table_tasks.setItem(row, 0, QTableWidgetItem(str(desc)))
            self.table_tasks.setItem(row, 1, QTableWidgetItem(str(cat)))
            self.table_tasks.setItem(row, 2, QTableWidgetItem(str(val)))
            self.table_tasks.setItem(row, 3, QTableWidgetItem(str(unit)))

        # Materials table
        self.table_materials.setRowCount(0)
        materials = getattr(wo, 'materials_used', []) or getattr(wo, 'parts_used', [])
        for mat in (materials or []):
            row = self.table_materials.rowCount()
            self.table_materials.insertRow(row)
            if isinstance(mat, dict):
                m_desc = mat.get('name') or mat.get('description') or mat.get('part_name', '')
                m_code = mat.get('part_number') or mat.get('code', '')
                m_qty = str(mat.get('quantity', 1))
                m_unit = mat.get('unit', 'unid')
            else:
                m_desc = str(mat)
                m_code = ""
                m_qty = "1"
                m_unit = "unid"
                
            self.table_materials.setItem(row, 0, QTableWidgetItem(m_desc))
            self.table_materials.setItem(row, 1, QTableWidgetItem(m_code))
            self.table_materials.setItem(row, 2, QTableWidgetItem(m_qty))
            self.table_materials.setItem(row, 3, QTableWidgetItem(m_unit))

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        wo_code = self.work_order.id if self.work_order else (self.preassigned_id or "")
        guide_lbl = "Guía de Servicio (OTS)" if self.guide_kind == GuideKind.SERVICE.value else "Guía de Mantenimiento (OTM)"
        if self.work_order:
            if read_only:
                self.setWindowTitle(f"Detalle de {guide_lbl} - {wo_code}")
            else:
                self.setWindowTitle(f"Llenar / Editar {guide_lbl} - {wo_code}")
        else:
            self.setWindowTitle(f"Nueva {guide_lbl} - {wo_code}")

        # Toggle standard buttons
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Operational State buttons visibility inside view mode
        if read_only and self.work_order:
            st = self.estado_combo.currentData() or "SCHEDULED"
            if hasattr(st, 'value'): st = st.value
            st_str = str(st).upper()
            
            if st_str in ["SCHEDULED", "PENDING", "PROGRAMADA"]:
                self.btn_start_wo.setVisible(True)
                self.btn_complete_wo.setVisible(False)
                self.btn_cancel_wo.setVisible(True)
            elif st_str in ["IN_PROGRESS", "EN_PROGRESO", "EN° PROCESO"]:
                self.btn_start_wo.setVisible(False)
                self.btn_complete_wo.setVisible(True)
                self.btn_cancel_wo.setVisible(True)
            else: # COMPLETED or CANCELLED
                self.btn_start_wo.setVisible(False)
                self.btn_complete_wo.setVisible(False)
                self.btn_cancel_wo.setVisible(False)
        else:
            self.btn_start_wo.setVisible(False)
            self.btn_complete_wo.setVisible(False)
            self.btn_cancel_wo.setVisible(False)

        enabled = not read_only
        self.rb_registered.setEnabled(enabled)
        self.rb_manual.setEnabled(enabled)
        self.equipo_combo.setEnabled(enabled)
        self.manual_tag_edit.setReadOnly(read_only)
        self.manual_client_edit.setReadOnly(read_only)
        self.manual_site_edit.setReadOnly(read_only)
        self.manual_location_edit.setReadOnly(read_only)
        
        self.titulo_edit.setReadOnly(read_only)
        self.tipo_servicio_combo.setEnabled(enabled)
        self.tipo_ot_combo.setEnabled(enabled)
        self.prioridad_combo.setEnabled(enabled)
        self.estado_combo.setEnabled(enabled)
        self.fecha_prog.setEnabled(enabled)
        self.fecha_limite.setEnabled(enabled)
        self.tecnico_edit.setReadOnly(read_only)
        self.diagnostico_edit.setReadOnly(read_only)
        self.trabajo_edit.setReadOnly(read_only)
        self.obs_edit.setReadOnly(read_only)
        
        self.btn_add_task.setEnabled(enabled)
        self.btn_remove_task.setEnabled(enabled)
        self.btn_add_material.setEnabled(enabled)
        self.btn_remove_material.setEnabled(enabled)
        
        if read_only:
            self.table_tasks.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table_materials.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        else:
            self.table_tasks.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked | QTableWidget.EditTrigger.EditKeyPressed)
            self.table_materials.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked | QTableWidget.EditTrigger.EditKeyPressed)

    def _on_start_work_clicked(self):
        idx = self.estado_combo.findData(WorkOrderStatus.IN_PROGRESS.value)
        if idx >= 0:
            self.estado_combo.setCurrentIndex(idx)
        if not self.start_date_str:
            self.start_date_str = datetime.now().isoformat()
            
        self.set_read_only(False)
        self.diagnostico_edit.setFocus()
        QMessageBox.information(
            self,
            "Trabajo Iniciado",
            "La orden ha pasado a estado 'En Progreso'.\n\nEl formulario estááá ahora habilitado para que ingrese el diagnóstico, checklist, trabajos ejecutados y repuestos utilizados."
        )

    def _on_complete_work_clicked(self):
        inc_note = f"\nâ€¢ La avería/incidencia ({self.incident_id}) pasará a estado 'Resuelta'." if self.incident_id else ""
        reply = QMessageBox.question(
            self,
            "Completar Trabajo",
            f"Â¿Desea dar por finalizado y completado este trabajo?{inc_note}\nâ€¢ El equipo asociado pasará a estado 'Operativo'.\n\nAl continuar, el estado cambiará a 'Completada' y podrá revisar y guardar los detalles finales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            idx = self.estado_combo.findData(WorkOrderStatus.COMPLETED.value)
            if idx >= 0:
                self.estado_combo.setCurrentIndex(idx)
            self.completed_date_str = datetime.now().isoformat()
            self.set_read_only(False)
            self.trabajo_edit.setFocus()

    def _on_cancel_work_clicked(self):
        reason, ok = QInputDialog.getText(
            self,
            "Cancelar / Anular Guía",
            "Ingrese el motivo de la cancelación de esta orden de trabajo:"
        )
        if ok:
            if not reason.strip():
                QMessageBox.warning(self, "Validación", "Debe ingresar el motivo de cancelación.")
                return
            idx = self.estado_combo.findData(WorkOrderStatus.CANCELLED.value)
            if idx >= 0:
                self.estado_combo.setCurrentIndex(idx)
            current_obs = self.obs_edit.toPlainText().strip()
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            cancel_note = f"[CANCELADA ({stamp}): {reason.strip()}]"
            self.obs_edit.setPlainText(f"{current_obs}\n{cancel_note}".strip())
            self.validate_and_accept()

    def _on_cancel_clicked(self):
        if self.work_order:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def validate_and_accept(self):
        if not self.titulo_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El título de la orden de trabajo es obligatorio.")
            self.titulo_edit.setFocus()
            return
            
        is_manual = self.rb_manual.isChecked()
        if is_manual:
            if not self.manual_tag_edit.text().strip():
                QMessageBox.warning(self, "Validación", "Debe ingresar el nombre o Tag del equipo en modo manual.")
                self.manual_tag_edit.setFocus()
                return
        else:
            if self.equipo_combo.currentIndex() <= 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un equipo de la lista o cambiar a 'Ingreso Manual'.")
                self.equipo_combo.setFocus()
                return
                
        self.accept()

    def get_work_order(self) -> WorkOrder:
        is_manual = self.rb_manual.isChecked()
        eq = self.equipo_combo.itemData(self.equipo_combo.currentIndex()) if not is_manual else None
        
        # Build checklist
        checklist = []
        for i in range(self.table_tasks.rowCount()):
            desc = self.table_tasks.item(i, 0).text() if self.table_tasks.item(i, 0) else ""
            cat = self.table_tasks.item(i, 1).text() if self.table_tasks.item(i, 1) else ""
            val = self.table_tasks.item(i, 2).text() if self.table_tasks.item(i, 2) else ""
            unit = self.table_tasks.item(i, 3).text() if self.table_tasks.item(i, 3) else ""
            if desc.strip():
                checklist.append(ChecklistItem(
                    id=f"item_{i+1}",
                    description=desc.strip(),
                    category=cat.strip(),
                    measured_value=val.strip(),
                    unit=unit.strip()
                ))

        # Build materials
        materials = []
        for i in range(self.table_materials.rowCount()):
            m_desc = self.table_materials.item(i, 0).text() if self.table_materials.item(i, 0) else ""
            m_code = self.table_materials.item(i, 1).text() if self.table_materials.item(i, 1) else ""
            m_qty = self.table_materials.item(i, 2).text() if self.table_materials.item(i, 2) else "1"
            m_unit = self.table_materials.item(i, 3).text() if self.table_materials.item(i, 3) else "unid"
            if m_desc.strip():
                try:
                    qty_val = float(m_qty.replace(',', '.'))
                except ValueError:
                    qty_val = 1.0
                materials.append({
                    "name": m_desc.strip(),
                    "part_number": m_code.strip(),
                    "quantity": qty_val,
                    "unit": m_unit.strip()
                })

        wo_id = self.work_order.id if self.work_order else (self.preassigned_id or "")
        
        # Equipment attributes
        if is_manual:
            eq_id = ""
            eq_tag = self.manual_tag_edit.text().strip()
            man_tag = eq_tag
            man_client = self.manual_client_edit.text().strip()
            man_site = self.manual_site_edit.text().strip()
            man_loc = self.manual_location_edit.text().strip()
            site_id = ""
            client_id = ""
        else:
            eq_id = eq.id if eq else ""
            eq_tag = eq.tag if eq else ""
            man_tag = ""
            man_client = ""
            man_site = ""
            man_loc = ""
            site_id = eq.site_id if eq else ""
            client_id = eq.client_id if eq else ""

        # Guide kind and service type
        service_type = self.tipo_servicio_combo.currentData() if self.guide_kind == GuideKind.SERVICE.value else ""
        wo_type = self.tipo_ot_combo.currentData() if self.guide_kind != GuideKind.SERVICE.value else WorkOrderType.CORRECTIVE.value

        return WorkOrder(
            id=wo_id,
            equipment_id=eq_id,
            equipment_tag=eq_tag,
            site_id=site_id,
            site_name=man_site,
            client_id=client_id,
            client_name=man_client,
            title=self.titulo_edit.text().strip(),
            description=self.diagnostico_edit.toPlainText().strip(),
            work_order_type=wo_type,
            priority=self.prioridad_combo.currentData(),
            status=self.estado_combo.currentData(),
            scheduled_date=self.fecha_prog.date().toString(Qt.DateFormat.ISODate),
            start_date=self.start_date_str,
            completed_date=self.completed_date_str,
            due_date=self.fecha_limite.date().toString(Qt.DateFormat.ISODate),
            assigned_technician=self.tecnico_edit.text().strip(),
            checklist=checklist,
            guide_kind=self.guide_kind,
            service_type=service_type,
            is_manual_equipment=is_manual,
            manual_equipment_tag=man_tag,
            manual_location=man_loc,
            manual_client=man_client,
            manual_site=man_site,
            diagnosis=self.diagnostico_edit.toPlainText().strip(),
            work_performed=self.trabajo_edit.toPlainText().strip(),
            materials_used=materials,
            observations=self.obs_edit.toPlainText().strip(),
            incident_id=self.incident_id
        )

    def _on_export_pdf_clicked(self):
        from PySide6.QtWidgets import QApplication, QFileDialog
        
        export_svc = self.export_service
        if not export_svc:
            app = QApplication.instance()
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'export_service'):
                    export_svc = widget.export_service
                    break
            
        if not export_svc:
            QMessageBox.warning(self, "Error", "No se encontró el servicio de exportación.")
            return

        try:
            wo = self.get_work_order()
        except Exception:
            wo = self.work_order
            
        if not wo:
            QMessageBox.warning(self, "Aviso", "No hay datos válidos para exportar.")
            return
            
        # ASK OPTIONS FIRST
        opt_dialog = PdfOptionsDialog(self)
        if opt_dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        options = opt_dialog.options
        
        # Build history if requested
        if options.get('include_history'):
            eq_id = self.equipo_combo.currentData()
            history_text = "Sin historial."
            
            # Find equipment_service
            app = QApplication.instance()
            eq_svc = None
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'equipment_service'):
                    eq_svc = widget.equipment_service
                    break
                    
            if eq_svc and eq_id:
                try:
                    hist = eq_svc.get_service_history(eq_id)
                    hist = sorted(hist, key=lambda x: x.date, reverse=True)[:2]
                    if hist:
                        lines = []
                        for h in hist:
                            d = h.date.split('T')[0] if h.date else 'N/A'
                            lines.append(f"• [{d}] {h.description} (Tipo: {h.type}) - Ref: {h.reference_id}")
                        history_text = "\n".join(lines)
                except Exception as e:
                    pass
            options['history_text'] = history_text
            
        wo_id = wo.id if wo.id else "Nueva_Guia"
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Guardar Informe PDF", f"Guia_{wo_id}.pdf", "Archivos PDF (*.pdf)"
        )
        
        if file_name:
            try:
                logo_path = ""
                app = QApplication.instance()
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'state_manager'):
                        logo_path = widget.state_manager.get_logo_path()
                        break
                        
                export_svc.export_work_order_pdf(wo, file_name, logo_path=logo_path, options=options)
                QMessageBox.information(self, "Éxito", f"PDF generado correctamente:\n{file_name}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Error al generar PDF:\n{str(e)}")

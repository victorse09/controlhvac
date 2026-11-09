"""
Technician Dialog for ControlHVAC CMMS.
Allows creating, viewing, and editing technician profiles.
"""
import uuid
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QComboBox, QMessageBox, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.core.models.enums import (
    TechnicianStatus, TECHNICIAN_STATUS_LABELS,
    TechnicianSpecialty, TECHNICIAN_SPECIALTY_LABELS
)
from src.core.models.technician import Technician
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class TechnicianDialog(QDialog):
    def __init__(self, parent=None, technician: Technician = None, read_only: bool = None):
        super().__init__(parent)
        self.technician = technician
        self.is_read_only = (technician is not None) if read_only is None else read_only
        self.resize(560, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        hb_layout = QHBoxLayout(header_banner)
        hb_layout.setContentsMargins(14, 10, 14, 10)
        hb_layout.setSpacing(12)
        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(40, 40)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon("technician.svg", "#8B5CF6", 20).pixmap(20, 20))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        tname = getattr(self.technician, 'full_name', '') if self.technician else "Nuevo Técnico"
        lbl_t = QLabel(f"Ficha de Técnico Especialista  —  {tname}")
        lbl_t.setObjectName("detailTitleLabel")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Especialidad técnica, estado operativo, contacto y certificaciones")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(lbl_t)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)
        layout.addWidget(header_banner)

        card, card_body = _create_dialog_card("Información Personal y Especialidad", "#8B5CF6")
        form_layout = QFormLayout(card_body)
        form_layout.setContentsMargins(16, 14, 16, 16)
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Ej: Juan")
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Ej: Pérez González")

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: 12.345.678-9")

        self.specialty_combo = QComboBox()
        for spec, label in TECHNICIAN_SPECIALTY_LABELS.items():
            self.specialty_combo.addItem(label, spec.value if hasattr(spec, 'value') else spec)

        self.status_combo = QComboBox()
        for st, label in TECHNICIAN_STATUS_LABELS.items():
            self.status_combo.addItem(label, st.value if hasattr(st, 'value') else st)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Ej: +56 9 1234 5678")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Ej: tecnico@controlhvac.cl")

        self.license_edit = QLineEdit()
        self.license_edit.setPlaceholderText("Ej: SEC Clase B - N° 987654")

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Observaciones, certificaciones adicionales, herramientas asignadas...")
        self.notes_edit.setMaximumHeight(80)

        form_layout.addRow("Nombres *:", self.first_name_edit)
        form_layout.addRow("Apellidos *:", self.last_name_edit)
        form_layout.addRow("RUT / Código *:", self.code_edit)
        form_layout.addRow("Especialidad *:", self.specialty_combo)
        form_layout.addRow("Estado *:", self.status_combo)
        form_layout.addRow("Teléfono:", self.phone_edit)
        form_layout.addRow("Correo Electrónico:", self.email_edit)
        form_layout.addRow("Certificación / SEC:", self.license_edit)
        form_layout.addRow("Notas:", self.notes_edit)

        layout.addWidget(card, 1)

        # Buttons
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)
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

        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)

        layout.addWidget(footer_bar)

        if self.technician:
            self._load_data()

        self.set_read_only(self.is_read_only)

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only

        if self.technician:
            self.setWindowTitle(
                f"Técnico: {self.technician.full_name}" if read_only 
                else f"Editar Técnico: {self.technician.full_name}"
            )
        else:
            self.setWindowTitle("Nuevo Técnico")

        # Set enabled states
        self.first_name_edit.setReadOnly(read_only)
        self.last_name_edit.setReadOnly(read_only)
        self.code_edit.setReadOnly(read_only)
        self.specialty_combo.setEnabled(not read_only)
        self.status_combo.setEnabled(not read_only)
        self.phone_edit.setReadOnly(read_only)
        self.email_edit.setReadOnly(read_only)
        self.license_edit.setReadOnly(read_only)
        self.notes_edit.setReadOnly(read_only)

        # Toggle button visibility
        self.btn_close.setVisible(read_only and self.technician is not None)
        self.btn_edit_mode.setVisible(read_only and self.technician is not None)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

    def _load_data(self):
        t = self.technician
        self.first_name_edit.setText(t.first_name)
        self.last_name_edit.setText(t.last_name)
        self.code_edit.setText(t.code)

        idx = self.specialty_combo.findData(t.specialty)
        if idx >= 0:
            self.specialty_combo.setCurrentIndex(idx)

        idx = self.status_combo.findData(t.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        self.phone_edit.setText(t.phone)
        self.email_edit.setText(t.email)
        self.license_edit.setText(t.license_number)
        self.notes_edit.setText(t.notes)

    def _on_cancel_clicked(self):
        if self.technician is not None:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def validate_and_accept(self):
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        code = self.code_edit.text().strip()

        if not first_name:
            QMessageBox.warning(self, "Campo Requerido", "Por favor ingrese el nombre del técnico.")
            self.first_name_edit.setFocus()
            return

        if not last_name:
            QMessageBox.warning(self, "Campo Requerido", "Por favor ingrese los apellidos del técnico.")
            self.last_name_edit.setFocus()
            return

        if not code:
            QMessageBox.warning(self, "Campo Requerido", "Por favor ingrese el RUT o código del técnico.")
            self.code_edit.setFocus()
            return

        self.accept()

    def get_technician_data(self) -> Technician:
        tech_id = self.technician.id if self.technician else f"tech_{uuid.uuid4().hex[:8]}"
        created_at = self.technician.created_at if self.technician else None

        tech = Technician(
            id=tech_id,
            code=self.code_edit.text().strip(),
            first_name=self.first_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            specialty=self.specialty_combo.currentData(),
            status=self.status_combo.currentData(),
            phone=self.phone_edit.text().strip(),
            email=self.email_edit.text().strip(),
            license_number=self.license_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip()
        )
        if created_at:
            tech.created_at = created_at
        return tech

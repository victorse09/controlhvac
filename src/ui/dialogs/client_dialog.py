from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QDateEdit, QMessageBox, QFrame, QLabel
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from ...core.models.client import Client
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card

class ClientDialog(QDialog):
    def __init__(self, parent=None, client=None, read_only=None):
        super().__init__(parent)
        self.client = client
        
        # Start in read-only / view mode if opening existing client
        self.is_read_only = (client is not None) if read_only is None else read_only
        self.resize(560, 540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Banner
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
        lbl_icon.setPixmap(IconManager.get_icon("clients.svg", "#38BDF8", 20).pixmap(20, 20))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        cname = getattr(self.client, 'company_name', '') if self.client else "Nuevo Cliente"
        lbl_t = QLabel(f"Ficha de Cliente  —  {cname}")
        lbl_t.setObjectName("detailTitleLabel")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Datos comerciales, contacto y vigencia de contrato")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(lbl_t)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)
        layout.addWidget(header_banner)

        card, card_body = _create_dialog_card("Información Comercial y Contacto", "#38BDF8")
        form_layout = QFormLayout(card_body)
        form_layout.setContentsMargins(16, 14, 16, 16)
        form_layout.setSpacing(10)
        
        self.empresa_edit = QLineEdit()
        self.rut_edit = QLineEdit()
        self.contacto_edit = QLineEdit()
        self.telefono_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.direccion_edit = QLineEdit()
        self.contrato_edit = QLineEdit()
        
        self.inicio_contrato = QDateEdit()
        self.inicio_contrato.setCalendarPopup(True)
        self.inicio_contrato.setDate(QDate.currentDate())
        
        self.fin_contrato = QDateEdit()
        self.fin_contrato.setCalendarPopup(True)
        self.fin_contrato.setDate(QDate.currentDate().addYears(1))
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(80)

        form_layout.addRow("Empresa *:", self.empresa_edit)
        form_layout.addRow("RUT *:", self.rut_edit)
        form_layout.addRow("Nombre Contacto:", self.contacto_edit)
        form_layout.addRow("Teléfono:", self.telefono_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Dirección:", self.direccion_edit)
        form_layout.addRow("Nro. Contrato:", self.contrato_edit)
        form_layout.addRow("Inicio Contrato:", self.inicio_contrato)
        form_layout.addRow("Fin Contrato:", self.fin_contrato)
        form_layout.addRow("Notas:", self.notas_edit)

        layout.addWidget(card, 1)

        # Buttons
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        # View Mode Buttons
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)
        
        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))
        
        # Edit / New Mode Buttons
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

        if self.client:
            self._load_data()

        self.set_read_only(self.is_read_only)

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        if self.client:
            cname = getattr(self.client, 'company_name', '') or getattr(self.client, 'name', '')
            if read_only:
                self.setWindowTitle(f"Detalle de Cliente - {cname}")
            else:
                self.setWindowTitle(f"Editar Cliente - {cname}")
        else:
            self.setWindowTitle("Nuevo Cliente")

        # Toggle Button Visibility
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Toggle Form Fields
        enabled = not read_only
        self.empresa_edit.setReadOnly(read_only)
        self.rut_edit.setReadOnly(read_only)
        self.contacto_edit.setReadOnly(read_only)
        self.telefono_edit.setReadOnly(read_only)
        self.email_edit.setReadOnly(read_only)
        self.direccion_edit.setReadOnly(read_only)
        self.contrato_edit.setReadOnly(read_only)
        self.inicio_contrato.setEnabled(enabled)
        self.fin_contrato.setEnabled(enabled)
        self.notas_edit.setReadOnly(read_only)

    def _on_cancel_clicked(self):
        if self.client:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _load_data(self):
        self.empresa_edit.setText(self.client.company_name)
        self.rut_edit.setText(self.client.tax_id)
        self.contacto_edit.setText(self.client.contact_name)
        self.telefono_edit.setText(self.client.contact_phone)
        self.email_edit.setText(self.client.contact_email)
        self.direccion_edit.setText(self.client.address)
        self.contrato_edit.setText(self.client.contract_number)
        
        if self.client.contract_start:
            try:
                self.inicio_contrato.setDate(QDate.fromString(self.client.contract_start[:10], Qt.DateFormat.ISODate))
            except: pass
        if self.client.contract_end:
            try:
                self.fin_contrato.setDate(QDate.fromString(self.client.contract_end[:10], Qt.DateFormat.ISODate))
            except: pass
            
        self.notas_edit.setPlainText(self.client.notes)

    def validate_and_accept(self):
        if not self.empresa_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo Empresa es obligatorio.")
            return
        if not self.rut_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo RUT es obligatorio.")
            return
            
        self.accept()

    def get_client(self) -> Client:
        client_id = self.client.id if self.client else ""
        return Client(
            id=client_id,
            company_name=self.empresa_edit.text().strip(),
            tax_id=self.rut_edit.text().strip(),
            contact_name=self.contacto_edit.text().strip(),
            contact_phone=self.telefono_edit.text().strip(),
            contact_email=self.email_edit.text().strip(),
            address=self.direccion_edit.text().strip(),
            contract_number=self.contrato_edit.text().strip(),
            contract_start=self.inicio_contrato.date().toString(Qt.DateFormat.ISODate),
            contract_end=self.fin_contrato.date().toString(Qt.DateFormat.ISODate),
            notes=self.notas_edit.toPlainText().strip()
        )

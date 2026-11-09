from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFrame, QLabel
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from ...core.models.client import InstallationSite
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card

class SiteDialog(QDialog):
    def __init__(self, parent=None, client_id=None, site=None, read_only=None):
        super().__init__(parent)
        self.client_id = client_id
        self.site = site
        
        if site:
            self.client_id = site.client_id
            
        # Start in read-only / view mode if opening existing site
        self.is_read_only = (site is not None) if read_only is None else read_only
        self.resize(520, 500)

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
        lbl_icon.setPixmap(IconManager.get_icon("site.svg", "#10B981", 20).pixmap(20, 20))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        sname = getattr(self.site, 'name', '') if self.site else "Nueva Instalación"
        lbl_t = QLabel(f"Instalación / Sede  —  {sname}")
        lbl_t.setObjectName("detailTitleLabel")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Ubicación física y datos de contacto de la instalación")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(lbl_t)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)
        layout.addWidget(header_banner)

        card, card_body = _create_dialog_card("Datos de la Instalación", "#10B981")
        form_layout = QFormLayout(card_body)
        form_layout.setContentsMargins(16, 14, 16, 16)
        form_layout.setSpacing(10)
        
        self.nombre_edit = QLineEdit()
        self.direccion_edit = QLineEdit()
        self.contacto_edit = QLineEdit()
        self.telefono_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setMaximumHeight(60)
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(60)

        form_layout.addRow("Nombre *:", self.nombre_edit)
        form_layout.addRow("Dirección:", self.direccion_edit)
        form_layout.addRow("Persona de Contacto:", self.contacto_edit)
        form_layout.addRow("Teléfono:", self.telefono_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Descripción:", self.descripcion_edit)
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

        if self.site:
            self._load_data()

        self.set_read_only(self.is_read_only)

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        if self.site:
            sname = getattr(self.site, 'name', '')
            if read_only:
                self.setWindowTitle(f"Detalle de Instalación - {sname}")
            else:
                self.setWindowTitle(f"Editar Instalación - {sname}")
        else:
            self.setWindowTitle("Nueva Instalación")

        # Toggle Button Visibility
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Toggle Form Fields
        self.nombre_edit.setReadOnly(read_only)
        self.direccion_edit.setReadOnly(read_only)
        self.contacto_edit.setReadOnly(read_only)
        self.telefono_edit.setReadOnly(read_only)
        self.email_edit.setReadOnly(read_only)
        self.descripcion_edit.setReadOnly(read_only)
        self.notas_edit.setReadOnly(read_only)

    def _on_cancel_clicked(self):
        if self.site:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _load_data(self):
        self.nombre_edit.setText(self.site.name)
        self.direccion_edit.setText(self.site.address)
        self.contacto_edit.setText(self.site.contact_person)
        self.telefono_edit.setText(self.site.contact_phone)
        self.email_edit.setText(self.site.contact_email)
        self.descripcion_edit.setPlainText(self.site.description)
        self.notas_edit.setPlainText(self.site.notes)

    def validate_and_accept(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo Nombre es obligatorio.")
            return
        self.accept()

    def get_site(self) -> InstallationSite:
        site_id = self.site.id if self.site else ""
        return InstallationSite(
            id=site_id,
            client_id=self.client_id,
            name=self.nombre_edit.text().strip(),
            address=self.direccion_edit.text().strip(),
            contact_person=self.contacto_edit.text().strip(),
            contact_phone=self.telefono_edit.text().strip(),
            contact_email=self.email_edit.text().strip(),
            description=self.descripcion_edit.toPlainText().strip(),
            notes=self.notas_edit.toPlainText().strip()
        )

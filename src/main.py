import sys
import os
import traceback
import faulthandler

# Suppress noisy KDE/Qt icon-theme warnings on Linux desktops (e.g. kf.iconthemes: Icon theme "AdwaitaLegacy" not found)
os.environ.setdefault("QT_LOGGING_RULES", "kf.iconthemes.debug=false;kf.iconthemes.warning=false")

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QLoggingCategory

faulthandler.enable()
QLoggingCategory.setFilterRules("kf.iconthemes.debug=false\nkf.iconthemes.warning=false")

from src.app.config import AppConfig, APP_NAME, APP_ORGANIZATION, APP_VERSION
from src.app.state_manager import StateManager
from src.ui.theme import apply_theme
from src.ui.icon_manager import IconManager
from src.ui.main_window import MainWindow

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler to show error messages to the user."""
    traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("Excepción no manejada:", traceback_str, file=sys.stderr)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Error Crítico")
    msg.setText("Ha ocurrido un error inesperado en la aplicación.")
    msg.setInformativeText(str(exc_value))
    msg.setDetailedText(traceback_str)
    msg.exec()

def main():
    # Set High-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # Global exception hook
    sys.excepthook = global_exception_handler
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    
    # Determine project root path relative to this file (support PyInstaller frozen executable)
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    assets_dir = os.path.join(base_dir, "assets")
    icons_dir = os.path.join(assets_dir, "icons")
    
    # Initialize IconManager
    IconManager.init(icons_dir)

    # Initialize Configuration and State
    config = AppConfig()
    state_manager = StateManager()

    # Show Splash Screen immediately for instant feedback
    from src.ui.splash_screen import SplashScreen
    splash = SplashScreen(logo_path=state_manager.get_logo_path())
    splash.show()
    splash.set_progress(20, "Cargando temas y configuración...")

    # Apply saved theme
    apply_theme(app, state_manager.get_theme())

    # Set app icon
    app_icon = IconManager.get_icon("app_icon")
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    splash.set_progress(50, "Cargando interfaz y servicios...")

    # Create MainWindow (views are loaded lazily on demand)
    main_window = MainWindow(config, state_manager)
    main_window.setObjectName("MainWindow")
    
    splash.set_progress(85, "Restaurando estado de trabajo...")

    # Restore window state
    state_manager.restore_window_state(main_window)
    
    splash.set_progress(100, "¡Listo!")

    # Show main window and finish splash
    main_window.show()
    splash.close()
    
    # Run event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

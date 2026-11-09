import os
import sys
import string
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

THEME_LABELS = {
    "slate": "Midnight Pro (Oscuro Moderno)",
    "navy_vibrant": "Cyber Cyan / Neón (Alto Contraste)",
    "titanium": "Titanium Dark (Gris Oscuro & Ámbar)",
    "nordic": "Nordic Teal (Frío Profesional)",
    "purple_vibrant": "Neon Violet (Vibrante)",
    "emerald": "Emerald Matrix (Verde Técnico)",
    "light_vibrant": "Light Studio (Tema Claro Moderno)",
}

THEMES = {
    # 1. Midnight Pro (Deep rich slate with vibrant electric blue accent)
    'slate': {
        'BG_PRIMARY': '#090D16',
        'BG_SECONDARY': '#111827',
        'BG_SURFACE': '#1F2937',
        'BG_HOVER': '#374151',
        'ROW_ALT': '#0D1526',
        'TREE_CLIENT_BG': '#17223B',
        'TREE_SITE_BG': '#151F34',
        'TREE_AREA_BG': '#131C2E',
        'SELECTION_BG': '#0F2942',
        'SELECTION_BORDER': '#0284C7',
        'HEADER_BG': '#0F172A',
        'CARD_BG': '#0F172A',
        'CARD_HEADER_BG': '#1E293B',
        'KV_EVEN_BG': '#0F172A',
        'KV_ODD_BG': '#131C31',
        'ACCENT_PRIMARY': '#38BDF8',
        'ACCENT_HOVER': '#60A5FA',
        'ACCENT_PRESSED': '#0284C7',
        'TEXT_PRIMARY': '#F8FAFC',
        'TEXT_SECONDARY': '#CBD5E1',
        'TEXT_MUTED': '#94A3B8',
        'BORDER': '#1E293B',
        'BORDER_LIGHT': '#334155',
        'STATUS_OK': '#10B981',
        'STATUS_WARN': '#F59E0B',
        'STATUS_ERROR': '#EF4444',
        'STATUS_INFO': '#38BDF8',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 2. Cyber Cyan / Neo-Blue (Futuristic deep navy and glowing cyan)
    'navy_vibrant': {
        'BG_PRIMARY': '#050B14',
        'BG_SECONDARY': '#0E1726',
        'BG_SURFACE': '#18263E',
        'BG_HOVER': '#22385C',
        'ROW_ALT': '#0A1322',
        'TREE_CLIENT_BG': '#13233D',
        'TREE_SITE_BG': '#101F36',
        'TREE_AREA_BG': '#0D1A2E',
        'SELECTION_BG': '#072D45',
        'SELECTION_BORDER': '#00B4D8',
        'HEADER_BG': '#0A1424',
        'CARD_BG': '#0A1322',
        'CARD_HEADER_BG': '#18263E',
        'KV_EVEN_BG': '#0A1322',
        'KV_ODD_BG': '#101E34',
        'ACCENT_PRIMARY': '#00E5FF',
        'ACCENT_HOVER': '#38EFFF',
        'ACCENT_PRESSED': '#00B4D8',
        'TEXT_PRIMARY': '#FFFFFF',
        'TEXT_SECONDARY': '#E2E8F0',
        'TEXT_MUTED': '#94A3B8',
        'BORDER': '#1A2942',
        'BORDER_LIGHT': '#2D446B',
        'STATUS_OK': '#00E676',
        'STATUS_WARN': '#FFD600',
        'STATUS_ERROR': '#FF3D71',
        'STATUS_INFO': '#00E5FF',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 3. Titanium Dark (Warm industrial dark with warm amber/orange accent)
    'titanium': {
        'BG_PRIMARY': '#121214',
        'BG_SECONDARY': '#1C1C1F',
        'BG_SURFACE': '#29292E',
        'BG_HOVER': '#3B3B42',
        'ROW_ALT': '#17171B',
        'TREE_CLIENT_BG': '#26262C',
        'TREE_SITE_BG': '#222228',
        'TREE_AREA_BG': '#1E1E24',
        'SELECTION_BG': '#33240F',
        'SELECTION_BORDER': '#D97706',
        'HEADER_BG': '#18181C',
        'CARD_BG': '#16161A',
        'CARD_HEADER_BG': '#26262C',
        'KV_EVEN_BG': '#16161A',
        'KV_ODD_BG': '#1E1E24',
        'ACCENT_PRIMARY': '#F59E0B',
        'ACCENT_HOVER': '#FBBF24',
        'ACCENT_PRESSED': '#D97706',
        'TEXT_PRIMARY': '#F9FAFB',
        'TEXT_SECONDARY': '#D1D5DB',
        'TEXT_MUTED': '#9CA3AF',
        'BORDER': '#29292E',
        'BORDER_LIGHT': '#40404A',
        'STATUS_OK': '#10B981',
        'STATUS_WARN': '#F59E0B',
        'STATUS_ERROR': '#EF4444',
        'STATUS_INFO': '#60A5FA',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 4. Nordic Teal (Calm cool arctic dark with fresh mint/teal accent)
    'nordic': {
        'BG_PRIMARY': '#0B1319',
        'BG_SECONDARY': '#131F27',
        'BG_SURFACE': '#1E2F3B',
        'BG_HOVER': '#2A3F4E',
        'ROW_ALT': '#0F1921',
        'TREE_CLIENT_BG': '#1A2B36',
        'TREE_SITE_BG': '#172630',
        'TREE_AREA_BG': '#14212A',
        'SELECTION_BG': '#0D3333',
        'SELECTION_BORDER': '#0D9488',
        'HEADER_BG': '#0F1A22',
        'CARD_BG': '#0E1820',
        'CARD_HEADER_BG': '#1E2F3B',
        'KV_EVEN_BG': '#0E1820',
        'KV_ODD_BG': '#14222C',
        'ACCENT_PRIMARY': '#14B8A6',
        'ACCENT_HOVER': '#2DD4BF',
        'ACCENT_PRESSED': '#0D9488',
        'TEXT_PRIMARY': '#F0FDFA',
        'TEXT_SECONDARY': '#CCFBF1',
        'TEXT_MUTED': '#94A3B8',
        'BORDER': '#1E2F3B',
        'BORDER_LIGHT': '#2E4759',
        'STATUS_OK': '#10B981',
        'STATUS_WARN': '#F59E0B',
        'STATUS_ERROR': '#EF4444',
        'STATUS_INFO': '#14B8A6',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 5. Neon Violet (Modern synthwave/cyber dark with vivid purple/pink accent)
    'purple_vibrant': {
        'BG_PRIMARY': '#0D0914',
        'BG_SECONDARY': '#171024',
        'BG_SURFACE': '#261B3B',
        'BG_HOVER': '#382856',
        'ROW_ALT': '#120C1D',
        'TREE_CLIENT_BG': '#241838',
        'TREE_SITE_BG': '#1F1531',
        'TREE_AREA_BG': '#1B122B',
        'SELECTION_BG': '#2B1548',
        'SELECTION_BORDER': '#9333EA',
        'HEADER_BG': '#140E20',
        'CARD_BG': '#120C1D',
        'CARD_HEADER_BG': '#261B3B',
        'KV_EVEN_BG': '#120C1D',
        'KV_ODD_BG': '#1A1229',
        'ACCENT_PRIMARY': '#A855F7',
        'ACCENT_HOVER': '#C084FC',
        'ACCENT_PRESSED': '#9333EA',
        'TEXT_PRIMARY': '#FAF5FF',
        'TEXT_SECONDARY': '#E9D5FF',
        'TEXT_MUTED': '#A8A29E',
        'BORDER': '#261B3B',
        'BORDER_LIGHT': '#402E63',
        'STATUS_OK': '#10B981',
        'STATUS_WARN': '#F59E0B',
        'STATUS_ERROR': '#EF4444',
        'STATUS_INFO': '#A855F7',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 6. Emerald Matrix (Deep forest dark with high-contrast emerald green)
    'emerald': {
        'BG_PRIMARY': '#06140E',
        'BG_SECONDARY': '#0C2118',
        'BG_SURFACE': '#153326',
        'BG_HOVER': '#1E4736',
        'ROW_ALT': '#091A13',
        'TREE_CLIENT_BG': '#132E22',
        'TREE_SITE_BG': '#10281E',
        'TREE_AREA_BG': '#0D2219',
        'SELECTION_BG': '#0A3625',
        'SELECTION_BORDER': '#059669',
        'HEADER_BG': '#091B14',
        'CARD_BG': '#091912',
        'CARD_HEADER_BG': '#153326',
        'KV_EVEN_BG': '#091912',
        'KV_ODD_BG': '#0E261C',
        'ACCENT_PRIMARY': '#10B981',
        'ACCENT_HOVER': '#34D399',
        'ACCENT_PRESSED': '#059669',
        'TEXT_PRIMARY': '#ECFDF5',
        'TEXT_SECONDARY': '#D1FAE5',
        'TEXT_MUTED': '#94A3B8',
        'BORDER': '#153326',
        'BORDER_LIGHT': '#22523D',
        'STATUS_OK': '#10B981',
        'STATUS_WARN': '#F59E0B',
        'STATUS_ERROR': '#EF4444',
        'STATUS_INFO': '#38BDF8',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    },
    # 7. Light Studio (Clean modern light theme with crisp borders and blue accent)
    'light_vibrant': {
        'BG_PRIMARY': '#F8FAFC',
        'BG_SECONDARY': '#FFFFFF',
        'BG_SURFACE': '#F1F5F9',
        'BG_HOVER': '#E2E8F0',
        'ROW_ALT': '#F8FAFC',
        'TREE_CLIENT_BG': '#E0F2FE',
        'TREE_SITE_BG': '#F1F5F9',
        'TREE_AREA_BG': '#F8FAFC',
        'SELECTION_BG': '#E0F2FE',
        'SELECTION_BORDER': '#0284C7',
        'HEADER_BG': '#F1F5F9',
        'CARD_BG': '#FFFFFF',
        'CARD_HEADER_BG': '#F1F5F9',
        'KV_EVEN_BG': '#FFFFFF',
        'KV_ODD_BG': '#F8FAFC',
        'ACCENT_PRIMARY': '#0284C7',
        'ACCENT_HOVER': '#0369A1',
        'ACCENT_PRESSED': '#0C4A6E',
        'TEXT_PRIMARY': '#0F172A',
        'TEXT_SECONDARY': '#334155',
        'TEXT_MUTED': '#64748B',
        'BORDER': '#E2E8F0',
        'BORDER_LIGHT': '#CBD5E1',
        'STATUS_OK': '#059669',
        'STATUS_WARN': '#D97706',
        'STATUS_ERROR': '#DC2626',
        'STATUS_INFO': '#0284C7',
        'BORDER_RADIUS': '8px',
        'BORDER_RADIUS_SM': '6px',
    }
}

_ACTIVE_THEME_NAME = 'slate'
PALETTE = THEMES['slate']

_STYLESHEET_CACHE = {}

def get_active_theme_name() -> str:
    return _ACTIVE_THEME_NAME

def get_current_palette() -> dict:
    return THEMES.get(_ACTIVE_THEME_NAME, THEMES['slate'])

def load_stylesheet(theme_name: str = 'slate') -> str:
    """Loads the QSS template and substitutes palette variables (cached)."""
    if theme_name in _STYLESHEET_CACHE:
        return _STYLESHEET_CACHE[theme_name]

    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    qss_path = os.path.join(base_dir, 'assets', 'styles', 'dark_theme.qss')
    
    if not os.path.exists(qss_path):
        return ""
        
    palette = THEMES.get(theme_name, THEMES['slate'])
    
    with open(qss_path, 'r', encoding='utf-8') as f:
        template_str = f.read()
        
    template = string.Template(template_str)
    result = template.safe_substitute(palette)
    _STYLESHEET_CACHE[theme_name] = result
    return result

def apply_theme(app_or_widget, theme_name: str = 'slate'):
    """Applies the stylesheet and default font to the application."""
    global _ACTIVE_THEME_NAME, PALETTE
    if theme_name not in THEMES:
        theme_name = 'slate'
    _ACTIVE_THEME_NAME = theme_name
    PALETTE = THEMES[theme_name]
    stylesheet = load_stylesheet(theme_name)
    if hasattr(app_or_widget, 'setStyleSheet'):
        app_or_widget.setStyleSheet(stylesheet)
    if hasattr(app_or_widget, 'setFont'):
        font = QFont("Segoe UI", 10)
        app_or_widget.setFont(font)

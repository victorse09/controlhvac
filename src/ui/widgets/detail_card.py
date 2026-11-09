"""
Reusable native Qt detail panel & card builders for ControlHVAC CMMS.
Provides the modern dark card aesthetic (accented section headers, alternating
key-value rows, status pill banners, and empty state cards) across all views.
"""
import html
from typing import Sequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea
)
from PySide6.QtCore import Qt


def clear_layout_widgets(layout: QVBoxLayout):
    """Safely removes and schedules deletion for all widgets/spacers in a layout."""
    while layout.count() > 0:
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.hide()
            w.setParent(None)
            w.deleteLater()


def build_section_card(title: str, accent_color: str, body_widget: QWidget) -> QFrame:
    """Creates a native styled QFrame card with an accented header and body widget."""
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
        f"color: {accent_color}; font-size: 11px; font-weight: bold; "
        f"letter-spacing: 0.5px; background: transparent; border: none;"
    )
    h_layout.addWidget(lbl_h)
    card_layout.addWidget(header)

    body_container = QWidget()
    body_container.setObjectName("eqCardBody")
    b_layout = QVBoxLayout(body_container)
    b_layout.setContentsMargins(12, 10, 12, 10)
    b_layout.setSpacing(6)
    b_layout.addWidget(body_widget)
    card_layout.addWidget(body_container)

    return card


def build_kv_widget(pairs: Sequence[tuple[str, str]], label_min_width: int = 130) -> QWidget:
    """Creates a native 2-column list of alternating key-value rows."""
    container = QWidget()
    container.setObjectName("eqCardBody")
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
        lbl_k.setMinimumWidth(label_min_width)

        lbl_v = QLabel(str(val_html))
        lbl_v.setObjectName("kvValueLabel")
        lbl_v.setTextFormat(Qt.TextFormat.RichText)
        lbl_v.setWordWrap(True)

        r_layout.addWidget(lbl_k, 4)
        r_layout.addWidget(lbl_v, 6)
        v_layout.addWidget(row_frame)

    return container


def build_rich_label(html_text: str) -> QLabel:
    """Creates a word-wrapped RichText QLabel with consistent styling."""
    lbl = QLabel(html_text)
    lbl.setObjectName("richBodyLabel")
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setWordWrap(True)
    return lbl


def build_status_banner(badges: Sequence[tuple[str, str, str, str]]) -> QFrame:
    """
    Creates a horizontal status banner with 1 or more color-coded pill badges.
    Each tuple in `badges` is: (caption_upper, badge_text, fg_hex, bg_hex)
    """
    banner = QFrame()
    banner.setObjectName("eqStatusBanner")
    banner_layout = QHBoxLayout(banner)
    banner_layout.setContentsMargins(12, 10, 12, 10)
    banner_layout.setSpacing(12)

    for caption, text, fg_color, bg_color in badges:
        col_w = QWidget()
        col_w.setStyleSheet("background: transparent; border: none;")
        col_l = QVBoxLayout(col_w)
        col_l.setContentsMargins(0, 0, 0, 0)
        col_l.setSpacing(4)

        lbl_cap = QLabel(caption.upper())
        lbl_cap.setObjectName("kvKeyLabel")
        lbl_cap.setStyleSheet("font-size: 10px; font-weight: bold; letter-spacing: 0.5px; background: transparent;")
        lbl_badge = QLabel(f"● {text}")
        lbl_badge.setStyleSheet(
            f"background-color: {bg_color}; color: {fg_color}; "
            f"border: 1px solid {fg_color}; border-radius: 6px; "
            f"padding: 5px 10px; font-weight: bold; font-size: 12px;"
        )
        col_l.addWidget(lbl_cap)
        col_l.addWidget(lbl_badge)
        banner_layout.addWidget(col_w, 1)

    return banner


def build_empty_detail_card(message: str) -> QFrame:
    """Creates a clean empty-state card when no item is selected."""
    msg_card = QFrame()
    msg_card.setObjectName("emptyDetailCard")
    m_layout = QVBoxLayout(msg_card)
    lbl = QLabel(message)
    lbl.setObjectName("muted")
    lbl.setWordWrap(True)
    lbl.setStyleSheet("font-size: 13px; background: transparent; border: none;")
    m_layout.addWidget(lbl)
    return msg_card

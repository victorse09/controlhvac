"""
Reusable helper for modernizing QTableView widgets across ControlHVAC CMMS
and persisting user-adjusted column widths, column visual order, and splitter sizes
in `config/ui_tables_settings.json`.
"""
from typing import Optional, Sequence
from PySide6.QtWidgets import QTableView, QHeaderView, QSplitter


UI_TABLES_SETTINGS_PATH = "config/ui_tables_settings.json"


def setup_modern_table(
    table: QTableView,
    storage=None,
    settings_key: str = "",
    default_widths: Optional[Sequence[int]] = None,
    splitter: Optional[QSplitter] = None,
    default_splitter_sizes: Optional[Sequence[int]] = None,
):
    """
    Configures a QTableView with interactive & movable columns, modern row styling,
    and automatic JSON persistence for column widths, column order, and splitter sizes.
    """
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(31)
    table.setShowGrid(False)

    hdr = table.horizontalHeader()
    hdr.setSectionsMovable(True)
    hdr.setSectionsClickable(True)
    hdr.setStretchLastSection(True)
    hdr.setMinimumSectionSize(55)

    model = table.model()
    col_count = model.columnCount() if model else 0
    for c_idx in range(col_count):
        hdr.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Interactive)

    # Apply initial default column widths if provided
    if default_widths and col_count:
        for idx, w in enumerate(default_widths):
            if idx < col_count and isinstance(w, (int, float)) and w >= 40:
                hdr.resizeSection(idx, int(w))

    if splitter and default_splitter_sizes and len(default_splitter_sizes) == 2:
        splitter.setSizes([int(default_splitter_sizes[0]), int(default_splitter_sizes[1])])

    if not storage or not settings_key:
        return

    state = {"restoring": True}

    def _load():
        state["restoring"] = True
        try:
            all_data = storage.load(UI_TABLES_SETTINGS_PATH, default={})
            if not isinstance(all_data, dict):
                all_data = {}
            entry = all_data.get(settings_key)
            if not isinstance(entry, dict):
                return

            c_cnt = table.model().columnCount() if table.model() else col_count
            widths = entry.get("column_widths")
            if isinstance(widths, list):
                for logical_idx, w in enumerate(widths):
                    if logical_idx < c_cnt and isinstance(w, (int, float)) and w >= 40:
                        hdr.resizeSection(logical_idx, int(w))

            visual_order = entry.get("column_visual_order")
            if isinstance(visual_order, list) and len(visual_order) == c_cnt:
                for target_visual_idx, logical_idx in enumerate(visual_order):
                    if 0 <= logical_idx < c_cnt:
                        current_visual_idx = hdr.visualIndex(logical_idx)
                        if current_visual_idx != target_visual_idx and current_visual_idx >= 0:
                            hdr.moveSection(current_visual_idx, target_visual_idx)

            if splitter is not None:
                sp_sizes = entry.get("splitter_sizes")
                if isinstance(sp_sizes, list) and len(sp_sizes) == 2 and all(isinstance(x, (int, float)) and x > 50 for x in sp_sizes):
                    splitter.setSizes([int(sp_sizes[0]), int(sp_sizes[1])])
        except Exception as e:
            print(f"Error loading table settings for {settings_key}: {e}")
        finally:
            state["restoring"] = False

    def _save(*_args):
        if state["restoring"] or not storage:
            return
        try:
            all_data = storage.load(UI_TABLES_SETTINGS_PATH, default={})
            if not isinstance(all_data, dict):
                all_data = {}
            prev_entry = all_data.get(settings_key, {})
            if not isinstance(prev_entry, dict):
                prev_entry = {}

            c_cnt = table.model().columnCount() if table.model() else col_count
            widths = [hdr.sectionSize(i) for i in range(c_cnt)]
            visual_order = [hdr.logicalIndex(v) for v in range(c_cnt)]

            new_entry = {
                "column_widths": widths,
                "column_visual_order": visual_order,
            }

            if splitter is not None:
                sp_sizes = splitter.sizes()
                if not table.isVisible() or any(s <= 50 for s in sp_sizes):
                    sp_sizes = prev_entry.get("splitter_sizes") or list(default_splitter_sizes or [550, 450])
                new_entry["splitter_sizes"] = sp_sizes

            all_data[settings_key] = new_entry
            storage.save(UI_TABLES_SETTINGS_PATH, all_data, backup=False)
        except Exception as e:
            print(f"Error saving table settings for {settings_key}: {e}")

    _load()
    hdr.sectionResized.connect(_save)
    hdr.sectionMoved.connect(_save)
    if splitter is not None:
        splitter.splitterMoved.connect(_save)

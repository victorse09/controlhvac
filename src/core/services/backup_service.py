"""
Backup and Restore Service for ControlHVAC CMMS.

Handles:
- Creating ZIP archives with embedded backup_manifest.json
- Calculating checksums and gathering module summaries
- Inspecting ZIP archives and comparing them to current data directory (Missing/Deleted, Modified, Identical)
- Full restore, missing-only restore, and selective module/file restore
- Automatic safety snapshots prior to restoration
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.data.json_storage import JsonStorageEngine


MODULE_LABELS = {
    "clients": "🏢 Clientes y Sedes",
    "equipment": "❄️ Inventario de Equipos",
    "incidents": "🚨 Averías e Incidencias",
    "work_orders": "📋 Órdenes de Trabajo y Guías",
    "maintenance_schedules": "📅 Programaciones de Mantenimiento",
    "inventory": "🔧 Repuestos y Herramientas",
    "library": "📚 Librería Técnica y Planos",
    "technicians": "👷 Técnicos y Personal",
    "config": "⚙️ Listas y Configuraciones",
    "recycle_bin": "🗑️ Papelera de Reciclaje",
    "photos": "📷 Fotografías y Evidencias",
    "other": "📁 Otros Archivos",
}

MANIFEST_FILENAME = "backup_manifest.json"


def _classify_path_module(rel_path: str) -> str:
    """Determine module classification for a relative file path."""
    normalized = rel_path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    first = parts[0].lower() if parts else ""
    if first in MODULE_LABELS:
        return first
    return "other"


def _compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _compute_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


class BackupService:
    """Service to create and restore backup ZIP archives with JSON manifest."""

    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage

    @property
    def base_dir(self) -> str:
        return self.storage.base_dir

    @property
    def backups_dir(self) -> str:
        b_dir = os.path.join(self.base_dir, "backups")
        os.makedirs(b_dir, exist_ok=True)
        return b_dir

    @property
    def safety_snapshots_dir(self) -> str:
        s_dir = os.path.join(self.backups_dir, "pre_restore_safety_snapshots")
        os.makedirs(s_dir, exist_ok=True)
        return s_dir

    # -------------------------------------------------------------------------
    # 1. CREATE BACKUP
    # -------------------------------------------------------------------------

    def create_backup(
        self,
        output_zip_path: Optional[str] = None,
        custom_name: Optional[str] = None,
        comments: str = "",
        include_photos: bool = True
    ) -> Dict[str, Any]:
        """Create a complete backup ZIP archive containing all system data and backup_manifest.json.

        Args:
            output_zip_path: Custom destination path. If None, saves in backups_dir.
            custom_name: Optional custom name prefix.
            comments: Optional description or note for this backup.
            include_photos: Whether to include the photos folder.

        Returns:
            Dictionary with backup metadata and output file path.
        """
        now_dt = datetime.now(timezone.utc)
        now_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_zip_path:
            name_part = f"_{custom_name.strip()}" if custom_name and custom_name.strip() else ""
            filename = f"backup_ControlHVAC_{now_tag}{name_part}.zip"
            output_zip_path = os.path.join(self.backups_dir, filename)

        # Ensure target directory exists
        out_dir = os.path.dirname(output_zip_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        files_manifest: List[Dict[str, Any]] = []
        modules_summary: Dict[str, Dict[str, Any]] = {k: {"files_count": 0, "items_count": 0, "total_bytes": 0} for k in MODULE_LABELS}

        # Gather files from base_dir (excluding backups, tmp, bak)
        all_entries: List[Tuple[str, str]] = []  # (abs_path, rel_path)

        for root, dirs, files in os.walk(self.base_dir):
            # Avoid walking into backups directory
            rel_root = os.path.relpath(root, self.base_dir).replace("\\", "/")
            if rel_root == "backups" or rel_root.startswith("backups/"):
                continue
            if not include_photos and (rel_root == "photos" or rel_root.startswith("photos/")):
                continue

            for file in files:
                # Exclude temp / backup files and existing manifests
                if file.endswith((".tmp", ".bak", ".lock", "~")):
                    continue
                if file == MANIFEST_FILENAME:
                    continue

                abs_p = os.path.join(root, file)
                rel_p = os.path.relpath(abs_p, self.base_dir).replace("\\", "/")

                # Don't backup the output zip file if it was created inside base_dir
                if os.path.abspath(abs_p) == os.path.abspath(output_zip_path):
                    continue

                all_entries.append((abs_p, rel_p))

        # Build file manifest and compute hashes
        total_uncompressed_bytes = 0
        for abs_p, rel_p in all_entries:
            try:
                f_stat = os.stat(abs_p)
                f_size = f_stat.st_size
                mod_time = datetime.fromtimestamp(f_stat.st_mtime, timezone.utc).isoformat()
                sha256 = _compute_sha256(abs_p)
                module_name = _classify_path_module(rel_p)

                total_uncompressed_bytes += f_size
                if module_name in modules_summary:
                    modules_summary[module_name]["files_count"] += 1
                    modules_summary[module_name]["total_bytes"] += f_size
                else:
                    modules_summary["other"]["files_count"] += 1
                    modules_summary["other"]["total_bytes"] += f_size

                files_manifest.append({
                    "path": rel_p,
                    "size": f_size,
                    "sha256": sha256,
                    "modified_at": mod_time,
                    "module": module_name
                })
            except Exception:
                pass

        # Estimate record counts from storage indices or JSONs
        record_counts = self._count_system_records()
        for k, count in record_counts.items():
            if k in modules_summary:
                modules_summary[k]["items_count"] = count

        manifest_data = {
            "backup_version": "2.0",
            "created_at": now_dt.isoformat(),
            "created_at_local": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "app_name": "ControlHVAC CMMS",
            "app_version": "1.0.0",
            "comments": comments.strip(),
            "source_data_dir": self.base_dir,
            "summary": {
                "total_files": len(files_manifest),
                "total_uncompressed_bytes": total_uncompressed_bytes,
                **record_counts
            },
            "modules": modules_summary,
            "files": files_manifest
        }

        # Write ZIP archive
        temp_zip = output_zip_path + ".tmp"
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zip_out:
            # 1. Write backup_manifest.json
            manifest_json_bytes = json.dumps(manifest_data, indent=2, ensure_ascii=False).encode("utf-8")
            zip_out.writestr(MANIFEST_FILENAME, manifest_json_bytes)

            # 2. Write all data files
            for abs_p, rel_p in all_entries:
                try:
                    zip_out.write(abs_p, rel_p)
                except Exception:
                    pass

        # Atomic rename to final zip path
        if os.path.exists(output_zip_path):
            os.remove(output_zip_path)
        shutil.move(temp_zip, output_zip_path)

        return {
            "success": True,
            "zip_path": output_zip_path,
            "file_size": os.path.getsize(output_zip_path),
            "manifest": manifest_data
        }

    def _count_system_records(self) -> Dict[str, int]:
        """Read existing counts from JSON storage."""
        counts = {
            "clients": 0,
            "equipment": 0,
            "incidents": 0,
            "work_orders": 0,
            "maintenance_schedules": 0,
            "technicians": 0,
            "library": 0,
            "inventory": 0,
            "recycle_bin": 0
        }
        try:
            cl_idx = self.storage.load_index("clients") or {}
            counts["clients"] = len(cl_idx)
        except Exception:
            pass

        try:
            eq_idx = self.storage.load_index("equipment") or {}
            counts["equipment"] = len(eq_idx)
        except Exception:
            pass

        try:
            inc_idx = self.storage.load_index("incidents") or {}
            counts["incidents"] = len(inc_idx)
        except Exception:
            pass

        try:
            wo_idx = self.storage.load_index("work_orders") or {}
            counts["work_orders"] = len(wo_idx)
        except Exception:
            pass

        try:
            tech_idx = self.storage.load_index("technicians") or {}
            counts["technicians"] = len(tech_idx)
        except Exception:
            pass

        try:
            lib_idx = self.storage.load_index("library") or {}
            counts["library"] = len(lib_idx)
        except Exception:
            pass

        try:
            tools = self.storage.load("inventory/tools.json") or []
            spares = self.storage.load("inventory/spare_parts.json") or []
            counts["inventory"] = (len(tools) if isinstance(tools, list) else 0) + (len(spares) if isinstance(spares, list) else 0)
        except Exception:
            pass

        try:
            schedules = self.storage.load("maintenance_schedules/schedules.json") or []
            counts["maintenance_schedules"] = len(schedules) if isinstance(schedules, list) else 0
        except Exception:
            pass

        try:
            rec_idx = self.storage.load_index("recycle_bin") or {}
            counts["recycle_bin"] = len(rec_idx)
        except Exception:
            pass

        return counts

    # -------------------------------------------------------------------------
    # 2. INSPECT & COMPARE BACKUP ARCHIVE
    # -------------------------------------------------------------------------

    def inspect_backup_archive(self, zip_path: str) -> Dict[str, Any]:
        """Inspect a backup ZIP archive, read manifest (or generate one dynamically),

        and compare all files against current working directory.

        Status for each file:
        - MISSING: File is in backup but missing/deleted in current data directory.
        - MODIFIED: File exists in both but size or SHA-256 differs.
        - IDENTICAL: File exists and matches SHA-256 in current data directory.
        """
        if not os.path.exists(zip_path) or not zipfile.is_zipfile(zip_path):
            raise ValueError(f"El archivo especificado no es un archivo ZIP válido: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as z:
            namelist = z.namelist()
            manifest_data: Optional[Dict[str, Any]] = None

            if MANIFEST_FILENAME in namelist:
                try:
                    with z.open(MANIFEST_FILENAME) as mf:
                        manifest_data = json.loads(mf.read().decode("utf-8"))
                except Exception:
                    manifest_data = None

            # If no manifest found or invalid, construct synthetic manifest from zip entries
            if not manifest_data:
                manifest_data = self._synthesize_manifest_from_zip(z)

            # Analyze files and compare with current directory
            files_analysis: List[Dict[str, Any]] = []
            status_counts = {"MISSING": 0, "MODIFIED": 0, "IDENTICAL": 0}
            modules_status: Dict[str, Dict[str, int]] = {
                k: {"total": 0, "missing": 0, "modified": 0, "identical": 0}
                for k in MODULE_LABELS
            }

            for file_entry in manifest_data.get("files", []):
                rel_p = file_entry.get("path", "").replace("\\", "/")
                if not rel_p or rel_p == MANIFEST_FILENAME:
                    continue

                b_size = file_entry.get("size", 0)
                b_sha = file_entry.get("sha256", "")
                mod_name = file_entry.get("module") or _classify_path_module(rel_p)

                cur_abs_p = os.path.join(self.base_dir, rel_p)
                if not os.path.exists(cur_abs_p):
                    status = "MISSING"
                    status_counts["MISSING"] += 1
                else:
                    cur_size = os.path.getsize(cur_abs_p)
                    if cur_size != b_size:
                        status = "MODIFIED"
                        status_counts["MODIFIED"] += 1
                    else:
                        cur_sha = _compute_sha256(cur_abs_p)
                        if b_sha and cur_sha == b_sha:
                            status = "IDENTICAL"
                            status_counts["IDENTICAL"] += 1
                        else:
                            status = "MODIFIED"
                            status_counts["MODIFIED"] += 1

                # Update module breakdown
                if mod_name not in modules_status:
                    modules_status[mod_name] = {"total": 0, "missing": 0, "modified": 0, "identical": 0}
                modules_status[mod_name]["total"] += 1
                modules_status[mod_name][status.lower()] += 1

                files_analysis.append({
                    "path": rel_p,
                    "module": mod_name,
                    "module_label": MODULE_LABELS.get(mod_name, "📁 " + mod_name.capitalize()),
                    "size": b_size,
                    "sha256": b_sha,
                    "modified_at": file_entry.get("modified_at", ""),
                    "status": status  # "MISSING", "MODIFIED", "IDENTICAL"
                })

            return {
                "zip_path": zip_path,
                "zip_size": os.path.getsize(zip_path),
                "manifest": manifest_data,
                "status_counts": status_counts,
                "modules_status": modules_status,
                "files": files_analysis
            }

    def _synthesize_manifest_from_zip(self, z: zipfile.ZipFile) -> Dict[str, Any]:
        """Construct synthetic manifest data for legacy zip files without backup_manifest.json."""
        files_manifest = []
        modules_summary = {k: {"files_count": 0, "items_count": 0, "total_bytes": 0} for k in MODULE_LABELS}
        total_bytes = 0

        for info in z.infolist():
            if info.is_dir():
                continue
            rel_p = info.filename.replace("\\", "/").strip("/")
            if rel_p == MANIFEST_FILENAME:
                continue

            f_size = info.file_size
            total_bytes += f_size
            data = z.read(info.filename)
            sha256 = _compute_bytes_sha256(data)
            mod_name = _classify_path_module(rel_p)

            if mod_name in modules_summary:
                modules_summary[mod_name]["files_count"] += 1
                modules_summary[mod_name]["total_bytes"] += f_size
            else:
                modules_summary["other"]["files_count"] += 1
                modules_summary["other"]["total_bytes"] += f_size

            files_manifest.append({
                "path": rel_p,
                "size": f_size,
                "sha256": sha256,
                "modified_at": datetime(*info.date_time).isoformat() if info.date_time else "",
                "module": mod_name
            })

        return {
            "backup_version": "1.0 (Legado)",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_at_local": "Fecha desconocida (archivo legado)",
            "app_name": "ControlHVAC CMMS",
            "app_version": "1.0.0",
            "comments": "Respaldo importado sin manifiesto original",
            "source_data_dir": "",
            "summary": {
                "total_files": len(files_manifest),
                "total_uncompressed_bytes": total_bytes
            },
            "modules": modules_summary,
            "files": files_manifest
        }

    # -------------------------------------------------------------------------
    # 3. RESTORE BACKUP
    # -------------------------------------------------------------------------

    def restore_backup(
        self,
        zip_path: str,
        restore_mode: str = "FULL",  # "FULL", "MISSING_ONLY", "SELECTIVE"
        selected_files: Optional[Set[str]] = None,
        selected_modules: Optional[Set[str]] = None,
        overwrite_existing: bool = True,
        create_safety_snapshot: bool = True
    ) -> Dict[str, Any]:
        """Restore files from a backup ZIP archive.

        Args:
            zip_path: Path to the backup ZIP archive.
            restore_mode:
                - 'FULL': Restore all files (overwriting existing).
                - 'MISSING_ONLY': Only restore files missing in current data dir.
                - 'SELECTIVE': Restore files specified in selected_files/modules.
            selected_files: Set of relative paths to restore if mode is 'SELECTIVE'.
            selected_modules: Set of module names to restore if mode is 'SELECTIVE'.
            overwrite_existing: Whether to overwrite existing files (relevant for SELECTIVE).
            create_safety_snapshot: Whether to automatically create a snapshot before restoring.

        Returns:
            Dictionary with restoration results (restored count, skipped count, errors, snapshot path).
        """
        inspection = self.inspect_backup_archive(zip_path)
        all_files = inspection["files"]

        # 1. Determine which files to extract
        files_to_restore: List[Dict[str, Any]] = []
        skipped_count = 0

        for f_info in all_files:
            rel_p = f_info["path"]
            status = f_info["status"]
            mod_name = f_info["module"]

            if restore_mode == "FULL":
                files_to_restore.append(f_info)

            elif restore_mode == "MISSING_ONLY":
                if status == "MISSING":
                    files_to_restore.append(f_info)
                else:
                    skipped_count += 1

            elif restore_mode == "SELECTIVE":
                match_file = selected_files and rel_p in selected_files
                match_mod = selected_modules and mod_name in selected_modules
                if match_file or match_mod:
                    if status != "MISSING" and not overwrite_existing:
                        skipped_count += 1
                    else:
                        files_to_restore.append(f_info)
                else:
                    skipped_count += 1

        if not files_to_restore:
            return {
                "success": True,
                "restored_count": 0,
                "skipped_count": skipped_count,
                "safety_snapshot": None,
                "errors": [],
                "message": "No hay archivos seleccionados o que requieran restauración."
            }

        # 2. Safety snapshot
        safety_snapshot_path = None
        if create_safety_snapshot:
            try:
                now_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_name = f"safety_snapshot_before_restore_{now_tag}.zip"
                snap_target = os.path.join(self.safety_snapshots_dir, snap_name)
                snap_res = self.create_backup(
                    output_zip_path=snap_target,
                    custom_name="SafetySnapshot",
                    comments=f"Snapshot automático previo a restauración de {os.path.basename(zip_path)}"
                )
                safety_snapshot_path = snap_res.get("zip_path")
            except Exception as snap_err:
                print(f"Warning: Failed to create safety snapshot: {snap_err}")

        # 3. Extract selected files
        restored_count = 0
        errors = []

        with zipfile.ZipFile(zip_path, "r") as z:
            for f_info in files_to_restore:
                rel_p = f_info["path"]
                target_abs_p = os.path.join(self.base_dir, rel_p)

                try:
                    # Ensure parent directory exists
                    os.makedirs(os.path.dirname(target_abs_p), exist_ok=True)

                    # Extract file content
                    data = z.read(rel_p)
                    with open(target_abs_p, "wb") as out_f:
                        out_f.write(data)

                    restored_count += 1
                except Exception as ex:
                    errors.append(f"Error restaurando {rel_p}: {ex}")

        # 4. Rebuild storage indices if JSON files were restored
        self._rebuild_indices_after_restore()

        return {
            "success": len(errors) == 0,
            "restored_count": restored_count,
            "skipped_count": skipped_count,
            "safety_snapshot": safety_snapshot_path,
            "errors": errors
        }

    def _rebuild_indices_after_restore(self):
        """Ensure all storage index files are consistent after files have been overwritten/restored."""
        try:
            # Re-index clients
            self.storage.rebuild_index("clients", "id", name_field="company_name")
        except Exception:
            pass

        try:
            # Re-index equipment
            self.storage.rebuild_index("equipment", "id", name_field="tag")
        except Exception:
            pass

        try:
            # Re-index incidents
            self.storage.rebuild_index("incidents", "id", name_field="title")
        except Exception:
            pass

        try:
            # Re-index work orders
            self.storage.rebuild_index("work_orders", "id", name_field="order_number")
        except Exception:
            pass

        try:
            # Re-index technicians
            self.storage.rebuild_index("technicians", "id", name_field="full_name")
        except Exception:
            pass

        try:
            # Re-index library
            self.storage.rebuild_index("library", "id", name_field="title")
        except Exception:
            pass

        try:
            # Re-index recycle bin
            self.storage.rebuild_index("recycle_bin", "id", name_field="original_id")
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 4. LIST AVAILABLE BACKUPS
    # -------------------------------------------------------------------------

    def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available ZIP backups in the backups directory with quick metadata."""
        if not os.path.exists(self.backups_dir):
            return []

        backups = []
        for item in os.listdir(self.backups_dir):
            if not item.endswith(".zip") or item.startswith("safety_snapshot_"):
                continue

            zip_p = os.path.join(self.backups_dir, item)
            if not os.path.isfile(zip_p):
                continue

            try:
                f_stat = os.stat(zip_p)
                created_dt = datetime.fromtimestamp(f_stat.st_mtime)

                manifest_summary = {}
                manifest_date = ""
                comments = ""

                # Fast inspect header
                try:
                    with zipfile.ZipFile(zip_p, "r") as z:
                        if MANIFEST_FILENAME in z.namelist():
                            with z.open(MANIFEST_FILENAME) as mf:
                                m_data = json.loads(mf.read().decode("utf-8"))
                                manifest_summary = m_data.get("summary", {})
                                manifest_date = m_data.get("created_at_local", "")
                                comments = m_data.get("comments", "")
                except Exception:
                    pass

                backups.append({
                    "filename": item,
                    "path": zip_p,
                    "size": f_stat.st_size,
                    "size_mb": round(f_stat.st_size / (1024 * 1024), 2),
                    "created_at": created_dt.strftime("%d-%m-%Y %H:%M:%S"),
                    "manifest_date": manifest_date or created_dt.strftime("%d-%m-%Y %H:%M:%S"),
                    "comments": comments,
                    "summary": manifest_summary
                })
            except Exception:
                pass

        # Sort descending by modification time / filename
        backups.sort(key=lambda x: x["filename"], reverse=True)
        return backups

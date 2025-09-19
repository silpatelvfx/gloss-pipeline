# utils/paths_nyc.py
# Centralized path helpers for the NYC pipeline.
# - Discovers job codes & project folders
# - Resolves GlossPost roots and IN-{code}/VFX-NY
# - Locates (or creates) the Approved folder
# - Provides NUKE/PROGRESS path helpers for script creation

from __future__ import annotations
import os
import re
from typing import Optional, Tuple, List

try:
    import nuke  # optional; only used for messaging
except Exception:
    nuke = None

# --- Roots (adjust here if your mounts change) ---
GLOSS_ROOT = "/Volumes/san-01/GlossPost"
CLOUD_ROOT = "/Volumes/san-01/CloudSync"

# Approved subfolders
APPROVED_NEW_SUB   = "APPROVED_RETOUCH"          # under IN-{code}
APPROVED_OLD_CHAIN = ["FOOTAGE_CLOUD", "APPROVED_RETOUCH_CLOUD"]  # under CloudSync job

# NYC specific: IN-{code}/VFX-NY moved outside FOOTAGE per your specs
VFX_NY_DIRNAME = "VFX-NY"

# --- Job code detection ---
_JOB_CODE_RE = re.compile(r"(^|[^\d])(?P<code>\d{6})(?!\d)")

def extract_job_code(text: str) -> Optional[str]:
    """
    Find a 6-digit job code in the provided text.
    """
    if not text:
        return None
    m = _JOB_CODE_RE.search(text)
    return m.group("code") if m else None

# --- Small helpers ---
def _norm(path: str) -> str:
    return path.replace("\\", "/") if path else path

def _listdir_safe(path: str) -> List[str]:
    try:
        return os.listdir(path)
    except Exception:
        return []

def _nuke_print(msg: str):
    if nuke:
        try:
            nuke.tprint(msg)
            return
        except Exception:
            pass
    # Fallback for non-Nuke contexts
    print(msg)


# --- add near the top (below imports) ---
def _ask_which_approved(new_path: str, old_path: str, creating: bool = False):
    """
    Show a dialog with buttons: New, Legacy, Cancel.
    Returns "new", "old", or None (cancel).
    If PySide is unavailable, falls back to a small nuke.Panel with OK/Cancel.
    """
    title = "Select Approved Folder"
    action = "create" if creating else "use"
    msg = (f"Choose which Approved path to {action}:\n\n"
           f"New (GlossPost):\n{new_path}\n\n"
           f"Legacy (CloudSync):\n{old_path}")

    # Try PySide (preferred: 3 real buttons)
    try:
        try:
            from PySide6 import QtWidgets
        except Exception:
            from PySide2 import QtWidgets

        box = QtWidgets.QMessageBox()
        box.setWindowTitle(title)
        box.setText(msg)
        btn_new    = box.addButton("New",    QtWidgets.QMessageBox.AcceptRole)
        btn_legacy = box.addButton("Legacy", QtWidgets.QMessageBox.ActionRole)
        btn_cancel = box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton(btn_new)  # default to NEW
        box.exec_()

        clicked = box.clickedButton()
        if clicked == btn_cancel:
            return None
        if clicked == btn_legacy:
            return "old"
        return "new"
    except Exception:
        pass

    # Fallback: nuke.Panel + pulldown (OK/Cancel)
    try:
        p = nuke.Panel(title)
        p.addEnumerationPulldown("Choice", "New Legacy")
        ok = p.show()
        if not ok:
            return None
        choice = p.value("Choice")
        return "new" if choice == "New" else "old"
    except Exception:
        # Last resort: default to NEW
        return "new"



# --- Project folder resolution ---
def find_project_folder_by_job_code(job_code: str) -> Optional[str]:
    """
    Return the GlossPost *project folder name* that starts with the job code,
    e.g., '101181_CK_FA25_Mens_CLOUD' for job_code='101181'.
    """
    if not job_code:
        return None
    for name in sorted(_listdir_safe(GLOSS_ROOT)):
        if name.startswith(job_code):
            return name
    return None

def resolve_project_folder_from_path(file_path: str) -> Optional[str]:
    """
    Resolve the GlossPost project folder for a given file path.

    Strategy:
      1) If path already includes GlossPost, return the folder after 'GlossPost'.
      2) If path is under CloudSync, extract job code from the next folder and look it up in GlossPost.
      3) Else, try to extract a 6-digit job code from the entire path and look it up.
    """
    fp = _norm(file_path or "")
    if not fp:
        return None

    parts = fp.split("/")
    if "GlossPost" in parts:
        try:
            idx = parts.index("GlossPost")
            return parts[idx + 1]
        except Exception:
            pass

    if "CloudSync" in parts:
        try:
            idx = parts.index("CloudSync")
            cloud_proj = parts[idx + 1] if idx + 1 < len(parts) else None
            code = extract_job_code(cloud_proj or "")
            if code:
                found = find_project_folder_by_job_code(code)
                if found:
                    return found
        except Exception:
            pass

    # Fallback: scan entire path for a 6-digit code and resolve
    code = extract_job_code(fp)
    if code:
        return find_project_folder_by_job_code(code)
    return None

def job_code_from_project_folder(project_folder: str) -> Optional[str]:
    """
    Given a GlossPost project folder like '101181_CK_FA25_Mens_CLOUD',
    return '101181'.
    """
    if not project_folder:
        return None
    head = project_folder.split("_", 1)[0]
    return head if head.isdigit() and len(head) == 6 else None

# --- Core NYC paths ---
def glosspost_project_root(project_folder: str) -> Optional[str]:
    if not project_folder:
        return None
    return _norm(os.path.join(GLOSS_ROOT, project_folder))

def glosspost_in_root(project_folder: str, job_code: Optional[str] = None) -> Optional[str]:
    """
    /Volumes/san-01/GlossPost/{project_folder}/IN-{job_code}
    """
    if not project_folder:
        return None
    code = job_code or job_code_from_project_folder(project_folder)
    if not code:
        return None
    return _norm(os.path.join(GLOSS_ROOT, project_folder, f"IN-{code}"))

def vfx_ny_dir(project_folder: str, job_code: Optional[str] = None) -> Optional[str]:
    """
    /Volumes/san-01/GlossPost/{project_folder}/IN-{job_code}/VFX-NY
    """
    in_root = glosspost_in_root(project_folder, job_code)
    if not in_root:
        return None
    return _norm(os.path.join(in_root, VFX_NY_DIRNAME))

def progress_nuke_base(project_folder: str) -> Optional[str]:
    """
    /Volumes/san-01/GlossPost/{project_folder}/PROGRESS-{job_code}/NUKE
    """
    if not project_folder:
        return None
    code = job_code_from_project_folder(project_folder)
    if not code:
        return None
    return _norm(os.path.join(GLOSS_ROOT, project_folder, f"PROGRESS-{code}", "NUKE"))

# --- Approved paths ---
def approved_new_path(project_folder: str, job_code: Optional[str] = None) -> Optional[str]:
    """
    /Volumes/san-01/GlossPost/{project_folder}/IN-{job_code}/APPROVED_RETOUCH
    """
    in_root = glosspost_in_root(project_folder, job_code)
    if not in_root:
        return None
    return _norm(os.path.join(in_root, APPROVED_NEW_SUB))

def approved_old_path(job_code: str) -> Optional[str]:
    """
    /Volumes/san-01/CloudSync/{cloud_project}/FOOTAGE_CLOUD/APPROVED_RETOUCH_CLOUD
    where {cloud_project} starts with the job code.
    """
    if not job_code:
        return None
    cloud_proj = next((f for f in _listdir_safe(CLOUD_ROOT) if f.startswith(job_code)), None)
    if not cloud_proj:
        return None
    p = os.path.join(CLOUD_ROOT, cloud_proj, *APPROVED_OLD_CHAIN)
    return _norm(p)

def ensure_dir(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        _nuke_print(f"[NYC PATHS] Failed to create directory: {path}\n{e}")
        return False

def find_approved_folder(job_code: str, job_folder_hint: Optional[str] = None) -> Optional[str]:
    """
    Locate (or create) the Approved folder for a job.
    Preference:
      - If only NEW exists -> use NEW
      - Else if only OLD exists -> use OLD
      - If both exist -> ask: New / Legacy / Cancel (default New)
      - If neither exists but both are resolvable -> ask which to create
      - If only one is resolvable -> create that one
    """
    if not job_code:
        if nuke:
            nuke.message("❌ No job code provided.")
        return None

    # Resolve project folder under GlossPost
    project_folder = job_folder_hint or find_project_folder_by_job_code(job_code)

    new_path = approved_new_path(project_folder, job_code) if project_folder else None
    old_path = approved_old_path(job_code)

    new_exists = bool(new_path and os.path.exists(new_path))
    old_exists = bool(old_path and os.path.exists(old_path))

    # Fast paths when only one exists
    if new_exists and not old_exists:
        return new_path
    if old_exists and not new_exists:
        return old_path

    # Both paths exist -> ask user which to use
    if new_exists and old_exists:
        choice = _ask_which_approved(new_path, old_path, creating=False)
        if choice is None:
            return None  # cancel
        return new_path if choice == "new" else old_path

    # Neither exists but both are resolvable -> ask which to create
    if new_path and old_path:
        choice = _ask_which_approved(new_path, old_path, creating=True)
        if choice is None:
            return None  # cancel
        target = new_path if choice == "new" else old_path
        return target if ensure_dir(target) else None

    # Only one path is resolvable -> create that one
    target = new_path or old_path
    if target and ensure_dir(target):
        return target

    # Could not resolve anything
    if nuke:
        nuke.message("❌ No valid job folder found for Approved.")
    return None


# --- Convenience wrappers used by ops ---
def derive_job_from_path(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Given any file path (MOV or EXR), return (job_code, project_folder).
    - Tries embedded GlossPost first
    - Falls back to CloudSync + code
    - Lastly scans whole path for a 6-digit code
    """
    p = _norm(path or "")
    if not p:
        return None, None

    # Project folder
    project_folder = resolve_project_folder_from_path(p)
    # Job code: prefer from project folder name if available
    code = job_code_from_project_folder(project_folder) if project_folder else None
    if not code:
        code = extract_job_code(p)

    return code, project_folder

def open_in_finder(path: str) -> bool:
    """
    Open a directory in Finder (macOS). Returns True on success.
    """
    try:
        if path and os.path.isdir(path):
            import subprocess
            subprocess.Popen(["open", path])
            return True
    except Exception as e:
        _nuke_print(f"[NYC PATHS] Failed to open Finder: {path}\n{e}")
    return False

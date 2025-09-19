import os
import re
import glob
import shutil
import subprocess
import nuke

from gloss_utils import constants as C
from gloss_utils.nuke_helpers import (
    get_selected_nodes,
    select_single_node,
    log_info,
    log_warning,
    log_error,
    safe_get_knob,
    connect_nodes,
)


# ===============================
# Sequence utilities (robust)
# ===============================
try:
    from gloss_utils.sequences import (
        normalize_padding,
        get_glob_pattern,
        resolve_frame_path,
        is_sequence,
        derive_shot_from_sequence_dir,
    )
except Exception as e:
    log_warning(f"Sequence utils not fully available yet: {e}")
    def normalize_padding(path: str) -> str:
        path = re.sub(r'(#+)', lambda m: f"%0{len(m.group(1))}d", path)
        path = re.sub(r'%d(?!\d)', '%04d', path)
        return path
    def get_glob_pattern(file_path: str) -> str:
        file_path = normalize_padding(file_path)
        file_path = re.sub(r'%0(\d+)d', lambda m: '?' * int(m.group(1)), file_path)
        return file_path
    def resolve_frame_path(path: str, frame: int) -> str:
        path = normalize_padding(path)
        return re.sub(r'%0(\d+)d', lambda m: f"{frame:0{int(m.group(1))}d}", path)
    def is_sequence(read_node) -> bool:
        try:
            fp = nuke.filename(read_node)
            return bool(re.search(r'%0?\d*d|#+|\.\d+\.[A-Za-z0-9]+$', fp or ""))
        except Exception:
            return False
    def derive_shot_from_sequence_dir(path_or_read):
        try:
            p = nuke.filename(path_or_read) if hasattr(path_or_read, "Class") else path_or_read
            return os.path.basename(os.path.dirname(p)) if p else None
        except Exception:
            return None

# ===============================
# NYC paths (centralized)
# ===============================
try:
    from gloss_utils.paths_nyc import (
        find_approved_folder,
        derive_job_from_path,
        progress_nuke_base,
    )
except Exception as e:
    log_warning(f"NYC path utils not fully available yet: {e}")
    def derive_job_from_path(path: str):
        parts = (path or "").split("/")
        job_code = next((p[:6] for p in parts if p[:6].isdigit()), None)
        job_folder = next((p for p in parts if job_code and p.startswith(job_code)), None)
        return job_code, job_folder
    def progress_nuke_base(project_folder: str):
        if not project_folder:
            return None
        code = project_folder.split("_", 1)[0]
        return f"/Volumes/san-01/GlossPost/{project_folder}/PROGRESS-{code}/NUKE"
    def find_approved_folder(job_code, job_folder_hint=None):
        gloss_root = "/Volumes/san-01/GlossPost"
        cloud_root = "/Volumes/san-01/CloudSync"
        gloss_proj = next((f for f in os.listdir(gloss_root) if f.startswith(job_code)), None)
        cloud_proj = next((f for f in os.listdir(cloud_root) if f.startswith(job_code)), None)
        gloss_path = os.path.join(gloss_root, gloss_proj, f"IN-{job_code}", "APPROVED_RETOUCH") if gloss_proj else None
        cloud_path = os.path.join(cloud_root, cloud_proj, "FOOTAGE_CLOUD", "APPROVED_RETOUCH_CLOUD") if cloud_proj else None
        if gloss_path and os.path.exists(gloss_path): return gloss_path
        if cloud_path and os.path.exists(cloud_path): return cloud_path
        use_new = nuke.ask((f"No approved folder found.\n\nNew → {gloss_path}\nOld → {cloud_path}\n\nUse NEW?")) if gloss_path and cloud_path else True
        target = gloss_path if use_new else cloud_path
        if target:
            try:
                os.makedirs(target, exist_ok=True); return target
            except Exception as e:
                nuke.message(f"❌ Failed to create approved folder:\n{target}\n\n{e}")
        else:
            nuke.message("❌ No valid job folder found.")
        return None

# ===============================
# Small helpers
# ===============================
def _clipboard_set(text: str):
    try:
        from PySide6 import QtWidgets
    except Exception:
        from PySide2 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.clipboard().setText(text)

def _selected_read():
    reads = get_selected_nodes("Read")
    if reads:
        return reads[0]
    nuke.message("Select a Read node first.")
    return None

def _clean_base_mov_name(name: str) -> str:
    """MOVs: strip pipeline suffixes (Comp/CHN/Roto/Track/DN/PreComp) to form a stable base."""
    m = re.match(r'^(.+?)(?:_(?:Comp.*|CHN.*|Roto.*|Track.*|DN.*|PreComp.*))?$', name, re.IGNORECASE)
    return m.group(1) if m else name

def _shot_key(read) -> str | None:
    """
    Stable match key for pairing:
      - Sequences: parent folder name
      - MOV: cleaned base name (without pipeline suffixes)
    """
    p = nuke.filename(read)
    if not p:
        return None
    if is_sequence(read):
        return derive_shot_from_sequence_dir(read)
    base = os.path.splitext(os.path.basename(p))[0]
    return _clean_base_mov_name(base)

# ===============================
# Node color utilities
# ===============================
def set_node_color(hex_color_value):
    try:
        node = _selected_read() or nuke.selectedNode()
        node['tile_color'].setValue(hex_color_value)
    except Exception:
        nuke.message("Select a node to set its color.")

def reset_node_color():
    try:
        node = _selected_read() or nuke.selectedNode()
        node['tile_color'].setValue(0)
    except Exception:
        nuke.message("Select a node to reset its color.")

# ===============================
# File/clipboard utilities
# ===============================
def copy_file_path():
    read = _selected_read()
    if not read:
        return
    try:
        evaluated = read['file'].evaluate()
        _clipboard_set(evaluated)
        nuke.message("File path copied to clipboard.")
    except Exception as e:
        log_error(f"Unable to copy file path: {e}")
        nuke.message("Unable to copy file path.")

def go_to_directory():
    read = _selected_read()
    if not read:
        return
    try:
        dir_path = os.path.dirname(read['file'].evaluate())
        if os.path.exists(dir_path):
            subprocess.Popen(['open', dir_path])
        else:
            nuke.message(f"Directory does not exist:\n{dir_path}")
    except Exception as e:
        log_error(f"Go to directory failed: {e}")
        nuke.message(f"❌ Error:\n{e}")

def copy_shot_filename():
    read = _selected_read()
    if not read:
        return
    try:
        file_path = read['file'].evaluate()
        clean = nuke.callbacks.filenameFilter(file_path)
        _clipboard_set(os.path.basename(clean))
        nuke.message("Filename copied to clipboard.")
    except Exception as e:
        log_error(f"Copy shot filename failed: {e}")
        nuke.message("Unable to copy filename.")

# ===============================
# QC tools
# ===============================
def _find_original_read_for(read):
    key = _shot_key(read)
    if not key:
        return None
    for node in nuke.allNodes("Read"):
        if node is read:
            continue
        alt_key = _shot_key(node)
        if alt_key != key:
            continue
        alt_path = nuke.filename(node)
        if not alt_path:
            continue
        alt_name = os.path.basename(alt_path)
        if re.search(r'_(Comp|CHN|Roto|Track|DN|PreComp)\b', alt_name, re.IGNORECASE):
            continue
        return node
    return None

def qc_compare_with_original():
    read = _selected_read()
    if not read:
        return
    if not nuke.filename(read):
        nuke.message("❌ Selected Read node has no file path.")
        return

    original = _find_original_read_for(read)
    if not original:
        nuke.message("❌ Original shot not found.")
        return

    merge = nuke.createNode("Merge2")
    merge.setInput(0, original)
    merge.setInput(1, read)
    merge["operation"].setValue("difference")
    merge["label"].setValue("QC: Diff vs Original")
    merge["note_font_size"].setValue(30)
    merge["tile_color"].setValue(0x6666FFFF)
    merge.setXpos((original.xpos() + read.xpos()) // 2)
    merge.setYpos(max(original.ypos(), read.ypos()) + 100)
    log_info("QC compare merge created.")

def toggle_wipe_viewer():
    read = _selected_read()
    if not read:
        return

    viewer = nuke.activeViewer().node()
    if not viewer:
        nuke.message("No active viewer.")
        return

    original = _find_original_read_for(read)
    if not original:
        nuke.message("❌ Original shot not found.")
        return

    # Remove any prior QC compare node
    for node in nuke.allNodes("Merge2"):
        if node['label'].value() == "QC: Diff vs Original":
            nuke.delete(node)

    viewer.setInput(0, original)
    viewer.setInput(1, read)

    wipe_enabled = viewer['wipeactive'].value()
    viewer['wipeactive'].setValue(0 if wipe_enabled else 1)
    state = "ON" if not wipe_enabled else "OFF"
    nuke.message(f"🔀 Wipe mode turned {state} (A = Original, B = Selected).")
    log_info(f"Wipe toggled {state}.")

# ===============================
# Approved folder flow (centralized paths)
# ===============================
def copy_to_approved():
    read = _selected_read()
    if not read:
        return
    try:
        evaluated_path = read['file'].evaluate()
        job_code, project_folder = derive_job_from_path(evaluated_path)
        if not job_code:
            nuke.message("Could not determine job code.")
            return

        approved_root = find_approved_folder(job_code, project_folder)
        if not approved_root:
            return

        if is_sequence(read):
            shot_name = derive_shot_from_sequence_dir(read) or os.path.basename(os.path.dirname(evaluated_path))
            approved_seq_dir = os.path.join(approved_root, shot_name)
            os.makedirs(approved_seq_dir, exist_ok=True)

            glob_pattern = get_glob_pattern(evaluated_path)
            files = sorted(glob.glob(glob_pattern.replace('\\', '/')))
            if not files:
                nuke.message(f"No files matched:\n{glob_pattern}")
                return

            for f in files:
                shutil.copy(f, os.path.join(approved_seq_dir, os.path.basename(f)))

            set_node_color(C.COLOR_NYC)  # or a specific “approved” color if you prefer
            nuke.message(f"✅ Copied {len(files)} frames to:\n{approved_seq_dir}")

        else:
            dst_path = os.path.join(approved_root, os.path.basename(evaluated_path))
            if os.path.exists(dst_path):
                if not nuke.ask(f"File already exists:\n{dst_path}\n\nOverwrite?"):
                    return
            shutil.copy(evaluated_path, dst_path)
            set_node_color(C.COLOR_NYC)
            nuke.message(f"✅ Copied to:\n{dst_path}")

    except Exception as e:
        log_error(f"Copy to approved failed: {e}")
        nuke.message(f"❌ Error:\n{str(e)}")

def go_to_approved_directory():
    read = _selected_read()
    if not read:
        return
    try:
        file_path = read['file'].evaluate()
        job_code, project_folder = derive_job_from_path(file_path)
        if not job_code:
            nuke.message("Could not determine job code.")
            return

        approved_folder = find_approved_folder(job_code, project_folder)
        if not approved_folder:
            return

        subprocess.Popen(["open", approved_folder])
    except Exception as e:
        log_error(f"Open approved directory failed: {e}")
        nuke.message(f"❌ Error:\n{str(e)}")

def import_approved_version():
    read = _selected_read()
    if not read:
        return
    try:
        file_path = read['file'].evaluate()
        job_code, project_folder = derive_job_from_path(file_path)
        if not job_code:
            nuke.message("Could not determine job code.")
            return

        approved_root = find_approved_folder(job_code, project_folder)
        if not approved_root:
            return

        if is_sequence(read):
            shot_name = derive_shot_from_sequence_dir(read) or os.path.basename(os.path.dirname(file_path))
            approved_dir = os.path.join(approved_root, shot_name)
            if not os.path.isdir(approved_dir):
                nuke.message(f"Approved sequence directory not found:\n{approved_dir}")
                return

            image_files = sorted(
                f for f in glob.glob(os.path.join(approved_dir, '*'))
                if re.search(r"\.(exr|dpx|jpg|jpeg|tif|tiff|png)$", f, re.IGNORECASE)
            )
            if not image_files:
                nuke.message(f"No image sequence files found in:\n{approved_dir}")
                return

            first_frame_name = os.path.basename(image_files[0])
            m = re.match(r"^(.*?)(\d+)(\.[a-zA-Z0-9]+)$", first_frame_name)
            if m:
                prefix, padding, ext = m.groups()
                pad_len = len(padding)
                approved_path = os.path.join(approved_dir, f"{prefix}%0{pad_len}d{ext}")
            else:
                approved_path = image_files[0]
        else:
            approved_path = os.path.join(approved_root, os.path.basename(file_path))
            if not os.path.exists(approved_path):
                nuke.message("Approved file not found.")
                return

        new_node = nuke.createNode("Read", f"file {{{approved_path}}}")
        new_node['first'].setValue(read['first'].value())
        new_node['last'].setValue(read['last'].value())
        new_node['origfirst'].setValue(read['first'].value())
        new_node['origlast'].setValue(read['last'].value())
        new_node['tile_color'].setValue(C.COLOR_REVIEW_NEEDED)
        log_info("Imported approved version.")

    except Exception as e:
        log_error(f"Import approved version failed: {e}")
        nuke.message(f"❌ Error:\n{str(e)}")

# ===============================
# Launch Nuke helpers
# ===============================
def launch_nuke_with_script(script_path):
    try:
        apps = "/Applications"
        versions = sorted([f for f in os.listdir(apps) if f.startswith("Nuke")], reverse=True)
        for version in versions:
            app_folder = os.path.join(apps, version)
            variants = [f for f in os.listdir(app_folder)
                        if f.startswith("NukeX") and f.endswith(".app") and "Non-Commercial" not in f]
            for app_name in variants:
                app_path = os.path.join(app_folder, app_name)
                if os.path.isdir(app_path):
                    subprocess.Popen(["open", "-a", app_path, script_path])
                    return
        nuke.message("❌ Could not find a full version of NukeX.")
    except Exception as e:
        log_error(f"Launch Nuke failed: {e}")
        nuke.message(f"🚫 Launch failed:\n{e}")

# ===============================
# Task script creation (uses progress_nuke_base)
# ===============================
def create_task_script(task_name):
    read = _selected_read()
    if not read:
        return
    try:
        file_path = nuke.filename(read)
        first_frame = int(read.firstFrame())

        # Validate existence at first frame
        concrete_first = resolve_frame_path(file_path, first_frame) if is_sequence(read) else file_path
        if not os.path.exists(concrete_first):
            nuke.message("Invalid file path.")
            return

        # Clip/shot name
        if is_sequence(read):
            clip = derive_shot_from_sequence_dir(read)
        else:
            clip = os.path.splitext(os.path.basename(file_path))[0]
        if not clip:
            nuke.message("Could not derive clip/shot name.")
            return

        width, height = read.width(), read.height()
        first = int(read['first'].value())
        last = int(read['last'].value())
        fps = read.metadata("input/framesPerSecond") or 23.976

        # Resolve project folder & PROGRESS-*/NUKE base
        _, project_folder = derive_job_from_path(file_path)
        base = progress_nuke_base(project_folder) if project_folder else None
        if not base:
            nuke.message("Could not resolve NUKE project base.")
            return

        tag = "NYC" if task_name == "COMP" else task_name
        pattern = f"{clip}_{tag}_v"

        shot_folder = os.path.join(base, clip, "Scripts", task_name)
        if os.path.exists(shot_folder):
            existing = sorted(f for f in os.listdir(shot_folder) if f.startswith(pattern) and f.endswith(".nk"))
            if existing:
                latest_script = os.path.join(shot_folder, existing[-1])
                if os.path.exists(latest_script):
                    launch_nuke_with_script(latest_script)
                    return

        confirm = nuke.ask(
            f"Create new {task_name} script?\n"
            f"Clip: {clip}\nRes: {width}x{height}\nFPS: {fps}\nFrames: {first} - {last}"
        )
        if not confirm:
            return

        os.makedirs(shot_folder, exist_ok=True)
        format_name = f"Clip_{width}x{height}"
        if format_name not in [f.name() for f in nuke.formats()]:
            nuke.addFormat(f"{width} {height} 0 0 {width} {height} 1 {format_name}")

        new_script_path = os.path.join(shot_folder, f"{clip}_{tag}_v01.nk")
        with open(new_script_path, "w") as f:
            f.write(f"""Root {{
 format \"{format_name}\"
 first_frame {first}
 last_frame {last}
 lock_range true
 fps {fps}
}}""")
        launch_nuke_with_script(new_script_path)

    except Exception as e:
        log_error(f"Create task script failed: {e}")
        nuke.message(f"❌ Script creation failed:\n{e}")

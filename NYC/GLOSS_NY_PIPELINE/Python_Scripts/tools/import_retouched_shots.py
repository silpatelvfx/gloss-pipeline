import os, re, nuke
# PySide6 / PySide2 compatibility
try:
    from PySide6 import QtWidgets
except Exception:
    from PySide2 import QtWidgets

# Use pipeline roots
try:
    from gloss_utils.paths_nyc import CLOUD_ROOT, extract_job_code
except Exception:
    CLOUD_ROOT = "/Volumes/san-01/CloudSync"
    def extract_job_code(text: str):
        m = re.search(r"(^|[^\d])(\d{6})(?!\d)", text or "")
        return m.group(2) if m else None

def _find_cloudsync_project(job_code: str):
    """Find the CloudSync project folder that starts with the job code."""
    if not (job_code and os.path.exists(CLOUD_ROOT)):
        return None
    try:
        for name in sorted(os.listdir(CLOUD_ROOT)):
            if name.startswith(job_code):
                return name
    except Exception:
        pass
    return None

def _get_existing_paths():
    return {nuke.filename(node) for node in nuke.allNodes("Read")}

def _get_existing_read_nodes():
    reads = {}
    for node in nuke.allNodes("Read"):
        path = nuke.filename(node)
        if path:
            base_name = os.path.basename(path)
            name_only = os.path.splitext(base_name)[0]
            reads[name_only] = node
    return reads

def _strip_retouch_suffix(name):
    # Remove suffix like _CHNv001, _CHN001, etc.
    return re.sub(r"_CHN[vV]?\d{3,}", "", name)

def _derive_cloudsync_job_from_scene():
    """
    Look at any Read path:
      - If it's under CloudSync, return that job folder.
      - Else, if it's under GlossPost, extract a job code and map to a CloudSync project folder.
    """
    for node in nuke.allNodes("Read"):
        fp = nuke.filename(node) or ""
        if "/CloudSync/" in fp:
            m = re.search(r"/CloudSync/([^/]+)/", fp)
            if m:
                return m.group(1)
        # Try inferring from job code
        code = extract_job_code(fp)
        if code:
            cloud = _find_cloudsync_project(code)
            if cloud:
                return cloud
    return None

def _create_backdrop(label, nodes):
    if not nodes:
        return
    bd = nuke.createNode("BackdropNode")
    bd["label"].setValue(label)
    bd["note_font_size"].setValue(30)
    bd["tile_color"].setValue(0x87CEFAFF)  # Light blue
    bd["z_order"].setValue(-1)

    margin_x, margin_y = 100, 60
    min_x = min(n.xpos() for n in nodes)
    max_x = max(n.xpos() + n.screenWidth() for n in nodes)
    min_y = min(n.ypos() for n in nodes)
    max_y = max(n.ypos() + n.screenHeight() for n in nodes)

    bd["xpos"].setValue(min_x - margin_x)
    bd["ypos"].setValue(min_y - margin_y)
    bd["bdwidth"].setValue((max_x - min_x) + 2 * margin_x)
    bd["bdheight"].setValue((max_y - min_y) + 2 * margin_y)

def import_retouched_shots():
    job_folder = _derive_cloudsync_job_from_scene()
    if not job_folder:
        nuke.message("❌ Could not determine CloudSync job folder from any Read node (or job code).")
        return

    base_path = os.path.join(CLOUD_ROOT, job_folder, "VFX-CHN", "RETOUCH")
    if not os.path.exists(base_path):
        nuke.message(f"❌ RETOUCH folder not found at:\n{base_path}")
        return

    # Prompt: latest or all
    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("Import RETOUCH Shots")
    msg_box.setText("Which RETOUCH folder(s) should be scanned?")
    latest_btn = msg_box.addButton("Latest Only", QtWidgets.QMessageBox.AcceptRole)
    all_btn    = msg_box.addButton("All",         QtWidgets.QMessageBox.ActionRole)
    cancel_btn = msg_box.addButton("Cancel",      QtWidgets.QMessageBox.RejectRole)
    msg_box.exec_()

    selected_btn = msg_box.clickedButton()
    if selected_btn == cancel_btn:
        return

    all_date_folders = sorted([f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))])
    if not all_date_folders:
        nuke.message("❌ No date folders found inside RETOUCH.")
        return

    date_folders_to_process = [all_date_folders[-1]] if selected_btn == latest_btn else all_date_folders

    existing_paths = _get_existing_paths()
    existing_reads = _get_existing_read_nodes()
    total_imported = 0

    xpos_fallback = 0
    ypos_default = 1000

    for date_folder in date_folders_to_process:
        date_path = os.path.join(base_path, date_folder)
        if not os.path.isdir(date_path):
            continue

        unmatched_nodes = []

        for file in sorted(os.listdir(date_path)):
            if file.startswith(".") or not file.lower().endswith(".mov") or "chn" not in file.lower():
                continue

            full_path = os.path.join(date_path, file).replace("\\", "/")
            if full_path in existing_paths:
                continue

            try:
                base_name = os.path.splitext(file)[0]
                base_match_name = _strip_retouch_suffix(base_name)

                if base_match_name in existing_reads:
                    base_node = existing_reads[base_match_name]
                    xpos = base_node.xpos()
                    ypos = base_node.ypos() + 150
                else:
                    xpos = xpos_fallback
                    ypos = ypos_default
                    xpos_fallback += 250

                read_node = nuke.createNode("Read", f"file {{{full_path}}}")
                read_node.setXpos(xpos)
                read_node.setYpos(ypos)

                if base_match_name not in existing_reads:
                    unmatched_nodes.append(read_node)

                total_imported += 1

            except Exception as e:
                nuke.message(f"❌ Failed to load: {full_path}\n\n{str(e)}")

        if unmatched_nodes:
            _create_backdrop(f"Unmatched - {date_folder}", unmatched_nodes)

    if total_imported == 0:
        nuke.message("✅ All RETOUCH shots are already imported!")
    else:
        nuke.message(f"✅ Imported {total_imported} RETOUCH clip(s)")

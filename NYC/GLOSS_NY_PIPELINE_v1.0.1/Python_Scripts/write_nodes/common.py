# write_nodes/common.py
# Shared helpers for write nodes: detect/choose output type and apply defaults.
import os, re, nuke

MOV_EXTS  = (".mov", ".mp4")
SEQ_EXTS  = (".exr", ".dpx", ".png", ".tif", ".tiff", ".jpg", ".jpeg")

def _counts_from_scene():
    """Count media types from current Read nodes (selected first, else all)."""
    reads = nuke.selectedNodes("Read") or nuke.allNodes("Read")
    counts = {"mov": 0, "exr": 0, "dpx": 0, "png": 0, "other_seq": 0}
    for r in reads:
        p = (nuke.filename(r) or "").lower()
        if not p:
            continue
        if p.endswith(MOV_EXTS):
            counts["mov"] += 1
            continue
        # sequence detection
        is_numbered = bool(re.search(r'%0?\d+d|#+|\.\d+\.[a-z0-9]+$', p))
        if p.endswith(".exr") or ("%0" in p and ".exr" in p):
            counts["exr"] += 1
        elif p.endswith(".dpx") or ("%0" in p and ".dpx" in p):
            counts["dpx"] += 1
        elif p.endswith(".png") or ("%0" in p and ".png" in p):
            counts["png"] += 1
        elif is_numbered or p.endswith(SEQ_EXTS):
            counts["other_seq"] += 1
    return counts

def choose_output_type():
    """
    Returns one of: 'mov', 'exr', 'dpx', 'png' or None if canceled.
    Default logic:
      - if only MOV present -> 'mov'
      - if only EXR/DPX/PNG present -> that one (EXR wins ties among seq)
      - if mixed -> ask with 4 buttons (default to most common; EXR for seq)
    """
    c = _counts_from_scene()
    mov = c["mov"]; exr = c["exr"]; dpx = c["dpx"]; png = c["png"]; other = c["other_seq"]
    seq_total = exr + dpx + png + other

    # Single-path defaults
    if mov and not seq_total:
        return "mov"
    if seq_total and not mov:
        # prefer the most common among seq formats; fall back to exr
        top = max((("exr", exr), ("dpx", dpx), ("png", png), ("other", other)), key=lambda x: x[1])[0]
        return "exr" if top == "other" else top

    # Mixed or ambiguous -> ask
    default = "mov" if mov >= seq_total else ("exr" if exr >= max(dpx, png, other) else ("dpx" if dpx >= max(exr, png, other) else "png"))
    return _ask_4way(default, mov, exr, dpx, png, other)

def _ask_4way(default, mov, exr, dpx, png, other):
    # Prefer PySide 4-button dialog
    try:
        try:
            from PySide6 import QtWidgets
        except Exception:
            from PySide2 import QtWidgets
        box = QtWidgets.QMessageBox()
        box.setWindowTitle("Choose Output Type")
        box.setText(f"MOV: {mov} | EXR: {exr} | DPX: {dpx} | PNG: {png} | Other Seq: {other}\n\nHow do you want to render?")
        b_mov = box.addButton("MOV (ProRes)", QtWidgets.QMessageBox.AcceptRole)
        b_exr = box.addButton("EXR Sequence", QtWidgets.QMessageBox.ActionRole)
        b_dpx = box.addButton("DPX Sequence", QtWidgets.QMessageBox.ActionRole)
        b_png = box.addButton("PNG Sequence", QtWidgets.QMessageBox.ActionRole)
        b_cancel = box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton({"mov": b_mov, "exr": b_exr, "dpx": b_dpx, "png": b_png}[default])
        box.exec_()
        btn = box.clickedButton()
        if btn == b_cancel: return None
        if btn == b_mov:    return "mov"
        if btn == b_exr:    return "exr"
        if btn == b_dpx:    return "dpx"
        return "png"
    except Exception:
        pass

    # Fallback nuke.Panel enumeration
    try:
        p = nuke.Panel("Choose Output Type")
        p.addEnumerationPulldown("Type", "MOV EXR DPX PNG")
        if not p.show():
            return None
        v = p.value("Type")
        return {"MOV": "mov", "EXR": "exr", "DPX": "dpx", "PNG": "png"}[v]
    except Exception:
        return "mov"

def apply_defaults(write_node, out_type):
    """
    Set file_type and reasonable defaults for each format.
    """
    if out_type == "mov":
        write_node["file_type"].setValue("mov")
        _set_if(write_node, "codec", "ap4x")           # ProRes 4444 XQ
        _set_if(write_node, "channels", "rgba")
        _set_if(write_node, "fps", nuke.root()["fps"].value())
        return

    # EXR / DPX / PNG share many sequence defaults
    write_node["file_type"].setValue(out_type)
    _set_if(write_node, "channels", "rgba")
    _set_if(write_node, "create_directories", True)

    if out_type == "exr":
        if "compression" in write_node.knobs():
            vals = [v.lower() for v in write_node["compression"].values()]
            if "zip (16 scanlines)" in vals: write_node["compression"].setValue("Zip (16 scanlines)")
            elif "piz" in vals:              write_node["compression"].setValue("PIZ")
        _set_if(write_node, "datatype", "16 bit half")
    elif out_type == "dpx":
        # DPX: 10-bit log is a common choice; color space Cineon if available
        _set_if(write_node, "datatype", "10 bit")
        if "colorspace" in write_node.knobs():
            try:
                if "Cineon" in write_node["colorspace"].values():
                    write_node["colorspace"].setValue("Cineon")
            except Exception:
                pass
    elif out_type == "png":
        # PNG: prefer 16-bit if available
        _set_if(write_node, "datatype", "16 bit")

def seq_ext(out_type):
    """Return a .%04d.<ext> for seq outputs, or .mov for mov."""
    return ".mov" if out_type == "mov" else { "exr": ".%04d.exr", "dpx": ".%04d.dpx", "png": ".%04d.png" }[out_type]

def _set_if(node, knob, value):
    try:
        if knob in node.knobs():
            node[knob].setValue(value)
    except Exception:
        pass


# --- Write node UI (Gloss tab) ----------------------------------------------

def install_write_gloss_ui(write_node):
    """
    Add/rename the 'User' tab to 'Gloss' on the given Write node and install:
      - Read from Write
      - Copy File Path
      - Go to File Path Directory
    Idempotent: will not add twice.
    """
    try:
        if not write_node or write_node.Class() != "Write":
            return

        # Prevent duplicates
        if write_node.knob("_gloss_write_ui"):
            return

        # Ensure the tab shows as "Gloss"
        t = write_node.knob("User")
        if t is None:
            t = nuke.Tab_Knob("User", "Gloss")
            write_node.addKnob(t)
        else:
            try:
                t.setLabel("Gloss")
            except Exception:
                write_node.addKnob(nuke.Tab_Knob("User", "Gloss"))

        # Hidden marker to avoid re-adding
        write_node.addKnob(nuke.Boolean_Knob("_gloss_write_ui", ""))
        write_node["_gloss_write_ui"].setVisible(False)

        # Header
        write_node.addKnob(nuke.Text_Knob("gloss_div_write_utils", "Write Utilities"))

        # Read from Write
        code_read = r"""
def _rw():
    import nuke
    try:
        p = nuke.thisNode()['file'].evaluate()
        nuke.createNode('Read', f"file {{{p}}}", inpanel=False)
    except Exception as e:
        nuke.message(f"Failed to create Read node:\n{e}")
_rw()
"""
        write_node.addKnob(nuke.PyScript_Knob("gloss_read_from_write", "Read from Write", code_read))

        # Copy File Path
        code_copy = r"""
def _cp():
    import nuke, platform, subprocess
    try:
        p = nuke.thisNode()['file'].evaluate()
        if platform.system() == 'Darwin':
            subprocess.run(f'printf "%s" "{p}" | pbcopy', shell=True)
        else:
            try:
                from PySide6 import QtWidgets
            except Exception:
                try:
                    from PySide2 import QtWidgets
                except Exception:
                    QtWidgets = None
            if QtWidgets:
                app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
                app.clipboard().setText(p)
            else:
                raise RuntimeError("No clipboard backend available.")
    except Exception as e:
        nuke.message(f"Failed to copy file path:\n{e}")
_cp()
"""
        write_node.addKnob(nuke.PyScript_Knob("gloss_copy_file_path", "Copy File Path", code_copy))

        # Go to File Path Directory
        code_open = r"""
def _go():
    import nuke, os, platform, subprocess
    try:
        p = nuke.thisNode()['file'].evaluate()
        d = os.path.dirname(p)
        if not os.path.isdir(d):
            nuke.message(f"Directory not found:\n{d}")
            return
        if platform.system() == 'Darwin':
            subprocess.Popen(['open', d])
        elif platform.system() == 'Windows':
            subprocess.Popen(['explorer', d])
        else:
            subprocess.Popen(['xdg-open', d])
    except Exception as e:
        nuke.message(f"Failed to open directory:\n{e}")
_go()
"""
        write_node.addKnob(nuke.PyScript_Knob("gloss_open_dir", "Go to File Path Directory", code_open))

    except Exception:
        pass

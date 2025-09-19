import nuke
from gloss_utils import constants as C

OPS_IMPORT = "import read_node.ops_read_tools as ops"

def _add_btn(node, name, label, func_call):
    k = nuke.PyScript_Knob(name, label)
    k.setCommand(f"{OPS_IMPORT}; ops.{func_call}")
    node.addKnob(k)

def _current_or_selected_read():
    try:
        node = nuke.thisNode()
    except Exception:
        node = None
    if not node or node.Class() != "Read":
        try:
            node = nuke.selectedNode()
        except Exception:
            node = None
    if not node or node.Class() != "Read":
        nuke.message("Select a Read node.")
        return None
    return node

def _ensure_gloss_tab(node):
    """Use the built-in 'User' tab but rename it to 'Gloss' so only 'Gloss' shows."""
    t = node.knob("User")
    if t is None:
        t = nuke.Tab_Knob("User", "Gloss")
        node.addKnob(t)
    else:
        try:
            t.setLabel("Gloss")
        except Exception:
            # Some Nuke versions don’t expose setLabel; re-add anyway
            node.addKnob(nuke.Tab_Knob("User", "Gloss"))

def add_buttons_to_read_node():
    node = _current_or_selected_read()
    if not node:
        return

    # Prevent duplicates
    if node.knob("_gloss_ui_installed"):
        return

    # Ensure we’re on the (renamed) Gloss tab before adding anything
    _ensure_gloss_tab(node)

    # Hidden marker (add AFTER we ensure the tab so it goes under Gloss)
    node.addKnob(nuke.Boolean_Knob("_gloss_ui_installed", ""))
    node["_gloss_ui_installed"].setVisible(False)

    # --- File Controls ---
    node.addKnob(nuke.Text_Knob("gloss_div_file", "File Controls"))
    _add_btn(node, "gloss_copyFilePath", "Copy File Path", "copy_file_path()")
    _add_btn(node, "gloss_goToDirectory", "Go to Directory", "go_to_directory()")
    _add_btn(node, "gloss_copyShotFilename", "Copy Shot Filename", "copy_shot_filename()")

    # --- Label Color ---
    node.addKnob(nuke.Text_Knob("gloss_div_color", "Label Color"))
    _add_btn(node, "gloss_colorChennai", "For Chennai", f"set_node_color({C.COLOR_CHENNAI})")
    _add_btn(node, "gloss_colorNYC",     "For NYC",     f"set_node_color({C.COLOR_NYC})")


      # --- Status Tags (header only for now; wire real tag funcs later if you want) ---
    node.addKnob(nuke.Text_Knob("gloss_div_status", "Status Tags"))
    _add_btn(node, "gloss_colorReview",  "Review Needed",   f"set_node_color({C.COLOR_REVIEW_NEEDED})")
    _add_btn(node, "gloss_colorRevision","Revision Needed", f"set_node_color({C.COLOR_REVISION_NEEDED})")
    _add_btn(node, "gloss_colorComplete","Complete",        f"set_node_color({C.COLOR_COMPLETE})")
    _add_btn(node, "gloss_resetColor",   "Reset",           "reset_node_color()")

    # --- QC Check ---
    node.addKnob(nuke.Text_Knob("gloss_div_qc", "QC Check"))
    _add_btn(node, "gloss_qcCompare", "QC Compare", "qc_compare_with_original()")
    _add_btn(node, "gloss_wipeToggle","Toggle Wipe", "toggle_wipe_viewer()")

    # --- Approval Process ---
    node.addKnob(nuke.Text_Knob("gloss_div_approval", "Approval Process"))
    _add_btn(node, "gloss_copyToApproved",  "Approved",           "copy_to_approved()")
    _add_btn(node, "gloss_openApprovedDir", "Approved Directory", "go_to_approved_directory()")
    _add_btn(node, "gloss_importApproved",  "Import Approved",    "import_approved_version()")

    # --- Task Scripts ---
    node.addKnob(nuke.Text_Knob("gloss_div_tasks", "Task Scripts"))
    _add_btn(node, "gloss_taskCOMP",  "COMP",  "create_task_script('COMP')")
    _add_btn(node, "gloss_taskROTO",  "ROTO",  "create_task_script('ROTO')")
    _add_btn(node, "gloss_taskTRACK", "TRACK", "create_task_script('TRACK')")
    _add_btn(node, "gloss_taskOTHER", "OTHER", "create_task_script('OTHER')")

    # --- Slate Overlay (placeholder) ---
    node.addKnob(nuke.Text_Knob("gloss_div_slate", "Slate Overlay"))
    _add_btn(node, "gloss_slateToggle", "Toggle Slate", "toggle_slate()")

def install():
    """Auto-install the Gloss UI on new Read nodes."""
    nuke.addOnUserCreate(add_buttons_to_read_node, nodeClass="Read")

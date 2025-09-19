# Gloss NYC — internal menu builder
# Location: /Users/sheel/.nuke/GLOSS_NY_PIPELINE/menu.py

import os
import sys
import nuke

# --- Paths ---
BASE_DIR    = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(BASE_DIR, "Python_Scripts")
ICON_DIR    = os.path.join(BASE_DIR, "Icon")

MONDAY_DIR = os.path.expanduser("~/.nuke/MONDAY_FOR_NUKE")
def _mon(cmd: str) -> str:
    return (
        "import os,sys; p=r'%s'; sys.path.append(p) if p not in sys.path else None; " % MONDAY_DIR
    ) + cmd


# --- Register search paths ---
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    nuke.pluginAddPath(ICON_DIR)
except Exception:
    try:
        nuke.addPath(ICON_DIR)  # fallback for older Nuke
    except Exception:
        nuke.tprint(f"[GLOSS NYC] ⚠️ Could not register Icon path: {ICON_DIR}")

# --- Safe import helper ---
def safe_import(dotted_name: str, label: str = None):
    label = label or dotted_name
    try:
        module = __import__(dotted_name, fromlist=['*'])
        nuke.tprint(f"[GLOSS NYC] ✅ Imported {label}")
        return module
    except Exception as e:
        nuke.tprint(f"[GLOSS NYC] ❌ Failed to import {label}: {e}")
        return None

# --- Import modules (OK if some are not ready yet) ---
ui_read_panel  = safe_import("read_node.ui_read_panel", "Read UI Panel")
ops            = safe_import("read_node.ops_read_tools", "Read Ops")
seq_utils      = safe_import("gloss_utils.sequences", "Sequence Utils")
paths_utils    = safe_import("gloss_utils.paths_nyc", "NYC Paths Utils")

w_dn           = safe_import("write_nodes.dn_output", "Write: DeNoise")
w_precomp      = safe_import("write_nodes.precomp_output", "Write: PreComp")
w_final        = safe_import("write_nodes.final_output", "Write: Final for Approval")

rv_integration = safe_import("integrations.rv", "RV Integration")

lineup_app     = safe_import("apps.lineup_browser", "Lineup Browser")
finder_panel   = safe_import("panels.find_shot_panel", "Shot Finder Panel")
retouch_tool   = safe_import("tools.import_retouched_shots", "Import RETOUCH Shots")

write_utils    = safe_import("write_nodes.util_actions", "Write Utilities")

cons           = safe_import("gloss_utils.constants", "Constants")

# --- Color helpers and fallbacks ---
def _color_cmd(hex_value):
    def _runner():
        fn = getattr(ops, "set_node_color", None)
        if callable(fn):
            fn(hex_value)
        else:
            nuke.message("Color function not available yet.")
    return _runner

def _reset_color_cmd():
    def _runner():
        fn = getattr(ops, "reset_node_color", None)
        if callable(fn):
            fn()
        else:
            nuke.message("Reset function not available yet.")
    return _runner

# Fallbacks in case constants module didn't import
COLOR_CHENNAI         = getattr(cons, "COLOR_CHENNAI",         0xFF8000FF) if cons else 0xFF8000FF
COLOR_NYC             = getattr(cons, "COLOR_NYC",             0x0000FFFF) if cons else 0x0000FFFF
COLOR_REVIEW_NEEDED   = getattr(cons, "COLOR_REVIEW_NEEDED",   0x00FFFFFF) if cons else 0x00FFFFFF
COLOR_REVISION_NEEDED = getattr(cons, "COLOR_REVISION_NEEDED", 0xE62E00FF) if cons else 0xE62E00FF
COLOR_COMPLETE        = getattr(cons, "COLOR_COMPLETE",        0x009933FF) if cons else 0x009933FF

# --- Build toolbar menu ---
TOOLBAR  = nuke.toolbar("Nodes")
MENU_ICON = "GLOSS.png"  # put this file inside Icon/
NY_MENU  = TOOLBAR.addMenu("Gloss NYC Tools", icon=MENU_ICON)


# Helper to guard missing funcs
def _add(menu, label, func):
    if callable(func):
        menu.addCommand(label, func)
    else:
        def _warn():
            nuke.message(f"'{label}' is not available yet.")
        menu.addCommand(label, _warn)

# Lineup
lineup_menu = NY_MENU.addMenu("Lineup")
_add(lineup_menu, "Lineup Browser", getattr(lineup_app, "launch_lineup_browser", None))
# Find Shot in Lineup
if finder_panel:
    panel_class = getattr(finder_panel, "ShotFinderPanel", None)
    if callable(panel_class):
        lineup_menu.addCommand("Find Shot in Lineup", lambda: panel_class().showModal())

NY_MENU.addSeparator()

# Ingest
ingest_menu = NY_MENU.addMenu("Ingest")
_add(ingest_menu, "Import RETOUCH Shots", getattr(retouch_tool, "import_retouched_shots", None))

# === QC Check ===
qc_menu = NY_MENU.addMenu("QC Check")
_add(qc_menu, "QC Compare", getattr(ops, "qc_compare_with_original", None))
_add(qc_menu, "Toggle Wipe", getattr(ops, "toggle_wipe_viewer", None))

NY_MENU.addSeparator()

# === Label Colors ===
colors_menu = NY_MENU.addMenu("Label Colors")   # make the submenu

# For Chennai
colors_menu.addCommand(
    "For Chennai",
    _mon(
        "import importlib, ny_monday_actions_min as mon, __main__ as _M; "
        "fn=getattr(getattr(_M,'ops',None),'set_node_color',None); "
        f"(fn({COLOR_CHENNAI}) if callable(fn) else None); "
        "importlib.reload(mon); mon.to_chennai(create_if_missing=True)"
    )
)

# For NYC
colors_menu.addCommand(
    "For NYC",
    _mon(
        "import importlib, ny_monday_actions_min as mon, __main__ as _M; "
        "fn=getattr(getattr(_M,'ops',None),'set_node_color',None); "
        f"(fn({COLOR_NYC}) if callable(fn) else None); "
        "importlib.reload(mon); mon.to_nyc(create_if_missing=True)"
    )
)

# Reset
colors_menu.addCommand(
    "Reset Node Color",
    _mon(
        "import importlib, ny_monday_actions_min as mon, __main__ as _M; "
        "fn=getattr(getattr(_M,'ops',None),'reset_node_color',None); "
        "(fn() if callable(fn) else None); "
        "importlib.reload(mon); mon.reset_main_status(create_if_missing=True)"
    )
)

# -------- Monday submenu (must CREATE it before adding commands) --------
mon_menu = NY_MENU.addMenu("Monday")

# Create a Monday row for this Read (silent) and save the link
mon_menu.addCommand(
    "Create Item for Selected Read (silent)",
    _mon("import importlib, ny_monday_actions_min as mon; importlib.reload(mon); mon.create_item_for_read(initial_status='Not Assigned')")
)

# Auto-link this Read to the best existing Monday row (silent)
mon_menu.addCommand(
    "Link Selected Read → Best Match (silent)",
    _mon("import importlib, ny_monday_actions_min as mon; importlib.reload(mon); mon.link_read_to_best_match()")
)





# === Status Tags ===
tags_menu = NY_MENU.addMenu("Status Tags")
tags_menu.addCommand("Review Needed",   _color_cmd(COLOR_REVIEW_NEEDED))
tags_menu.addCommand("Revision Needed", _color_cmd(COLOR_REVISION_NEEDED))
tags_menu.addCommand("Complete",        _color_cmd(COLOR_COMPLETE))

NY_MENU.addSeparator()

# === File Controls ===
fc_menu = NY_MENU.addMenu("File Controls")
_add(fc_menu, "Copy File Path",     getattr(ops, "copy_file_path", None))
_add(fc_menu, "Go to Directory",    getattr(ops, "go_to_directory", None))
_add(fc_menu, "Copy Shot Filename", getattr(ops, "copy_shot_filename", None))

NY_MENU.addSeparator()

# === Approval Process ===
appr_menu = NY_MENU.addMenu("Approval")
_add(appr_menu, "Send to Approved",         getattr(ops, "copy_to_approved", None))
_add(appr_menu, "Open Approved Directory",  getattr(ops, "go_to_approved_directory", None))
_add(appr_menu, "Import Approved Version",  getattr(ops, "import_approved_version", None))

NY_MENU.addSeparator()

# === Task Scripts ===
def _task_cmd(task):
    def _runner():
        fn = getattr(ops, "create_task_script", None)
        if callable(fn):
            fn(task)
        else:
            nuke.message("Task script function not available yet.")
    return _runner

ts_menu = NY_MENU.addMenu("Task Scripts")
for t in ("COMP", "ROTO", "TRACK", "OTHER"):
    ts_menu.addCommand(t, _task_cmd(t))

NY_MENU.addSeparator()

# === Write Nodes ===
wn_menu = NY_MENU.addMenu("Write Nodes")
_add(wn_menu, "DeNoise",              getattr(w_dn, "run", None))
_add(wn_menu, "PreComp",              getattr(w_precomp, "run", None))
_add(wn_menu, "Final for Approved",   getattr(w_final, "run", None))

# handy actions that work on the selected Write
wn_menu.addSeparator()
_add(wn_menu, "Create Read from Selected Write", getattr(write_utils, "create_read_from_selected_write", None))
_add(wn_menu, "Copy Selected Write Path",        getattr(write_utils, "copy_selected_write_path", None))
_add(wn_menu, "Open Selected Write Directory",   getattr(write_utils, "open_selected_write_directory", None))

NY_MENU.addSeparator()

# === Integrations ===
int_menu = NY_MENU.addMenu("Integrations")
_add(int_menu, "Open in RV", getattr(rv_integration, "open_in_rv", None))

NY_MENU.addSeparator()

# === Read UI ===
# Auto-install the Gloss tab on new Read nodes if available
if ui_read_panel and hasattr(ui_read_panel, "install"):
    try:
        ui_read_panel.install()
        nuke.tprint("[GLOSS NYC] 🧩 Read UI auto-install enabled.")
    except Exception as e:
        nuke.tprint(f"[GLOSS NYC] ⚠️ ui_read_panel.install() failed: {e}")

# Also provide a manual installer for the selected node
_add(NY_MENU, "Read UI/Install on Selected Read", getattr(ui_read_panel, "add_buttons_to_read_node", None))

nuke.tprint("[GLOSS NYC] Menu loaded.")



mon_menu = NY_MENU.addMenu("Monday (Safe)")

mon_menu.addCommand("Test Connection", _mon("import monday_safe as m; m.test_connection()"))
mon_menu.addCommand("Show Board Columns", _mon("import monday_safe as m; m.show_columns()"))
mon_menu.addSeparator()
mon_menu.addCommand("Link Selected Read (create if needed)", _mon("import monday_safe as m; m.link_or_create_selected_read()"))
mon_menu.addSeparator()
mon_menu.addCommand("Set City → NYC", _mon("import monday_safe as m; m.set_city('NYC')"))
mon_menu.addCommand("Set City → CHN", _mon("import monday_safe as m; m.set_city('CHN')"))
mon_menu.addCommand("Reset Main Status", _mon("import monday_safe as m; m.set_main_status()"))

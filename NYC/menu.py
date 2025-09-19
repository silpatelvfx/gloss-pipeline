# ~/.nuke/menu.py — SAFE LOADER
import os, sys, traceback
import nuke

# ---------- Bootstrap external tools that might not be installed ----------
try:
    import shortcuteditor
    shortcuteditor.nuke_setup()
except Exception:
    traceback.print_exc()

# ---------- Custom Tools menu ----------
my_menu = nuke.menu('Nuke').addMenu('Custom Tools')

# ---------- Render/DJV (guard if Render menu missing) ----------
try:
    menu = nuke.menu('Nuke')
    render_menu = menu.findItem('Render')
    if render_menu:
        render_menu.addCommand(
            'Flipbook Selected in &DJV',
            'nukescripts.flipbook( djv_this.djv_this, nuke.selectedNode() )',
            'Ctrl+F',
            index=9
        )
    else:
        nuke.tprint("[menu.py] 'Render' menu not found; skipping DJV command.")
except Exception:
    nuke.tprint("[menu.py] Failed to add DJV command:")
    traceback.print_exc()

# ---------- WrapItUp (optional) ----------
try:
    import WrapItUp
    nuke.menu('Nuke').addCommand('Extra/Wrap It Up', "WrapItUp.WrapItUp()")
except Exception:
    nuke.tprint("[menu.py] WrapItUp not available; skipping.")

# ---------- V!ctor Tools (safe imports) ----------
def _safe_import(name):
    try:
        mod = __import__(name, fromlist=['*'])
        return mod
    except Exception:
        nuke.tprint(f"[menu.py] Optional module not found: {name}")
        return None

V_PresetBackdrop        = _safe_import('V_PresetBackdrop')
V_PostageStampGenerator = _safe_import('V_PostageStampGenerator')
V_ConvertGizmosToGroups = _safe_import('V_ConvertGizmosToGroups')
# V_GenerateReadFromWrite = _safe_import('V_GenerateReadFromWrite')  # leave commented if not present

VictorMenu = nuke.menu('Nuke').addMenu('V!ctor')
if V_PresetBackdrop:
    VictorMenu.addCommand('Preset Backdrop', 'V_PresetBackdrop.presetBackdrop()', 'ctrl+alt+b')
if V_PostageStampGenerator:
    VictorMenu.addCommand('Generate PostageStamp from node', 'V_PostageStampGenerator.postageStampGenerator()', 'ctrl+alt+p')
# if V_GenerateReadFromWrite:
#     VictorMenu.addCommand('Generate Read node from Write node', 'V_GenerateReadFromWrite.generateReadFromWrite()', 'ctrl+r')
if V_ConvertGizmosToGroups:
    VictorMenu.addCommand('Convert Gizmo to Group', 'V_ConvertGizmosToGroups.convertGizmosToGroups()', 'ctrl+shift+h')

# ---------- Gloss Post toolbar ----------
try:
    toolbar_nodes = nuke.toolbar("Nodes")
    toolbar_nodes.addMenu("Gloss Post", icon="GLOSS.png")
except Exception:
    nuke.tprint("[menu.py] Could not register Gloss Post toolbar.")

# ---------- VideoCopilot (only adds menu entry; node may fail on click if plugin missing) ----------
try:
    toolbar_nodes = nuke.menu('Nodes')
    vc = toolbar_nodes.addMenu('VideoCopilot', icon='VideoCopilot.png')
    vc.addCommand('OpticalFlares', "nuke.createNode('OpticalFlares')", icon='OpticalFlares.png')
except Exception:
    nuke.tprint("[menu.py] VideoCopilot entries skipped.")

# ---------- 3DE nodes (menu entries only) ----------
try:
    nm = nuke.menu("Nodes")
    nm.addCommand("3DE4/LD_3DE4_Anamorphic_Standard_Degree_4",   "nuke.createNode('LD_3DE4_Anamorphic_Standard_Degree_4')")
    nm.addCommand("3DE4/LD_3DE4_Anamorphic_Rescaled_Degree_4",   "nuke.createNode('LD_3DE4_Anamorphic_Rescaled_Degree_4')")
    nm.addCommand("3DE4/LD_3DE4_Anamorphic_Standard_Degree_6",   "nuke.createNode('LD_3DE4_Anamorphic_Standard_Degree_6')")
    nm.addCommand("3DE4/LD_3DE4_Anamorphic_Rescaled_Degree_6",   "nuke.createNode('LD_3DE4_Anamorphic_Rescaled_Degree_6')")
    nm.addCommand("3DE4/LD_3DE4_Radial_Standard_Degree_4",       "nuke.createNode('LD_3DE4_Radial_Standard_Degree_4')")
    nm.addCommand("3DE4/LD_3DE4_Radial_Fisheye_Degree_8",        "nuke.createNode('LD_3DE4_Radial_Fisheye_Degree_8')")
    nm.addCommand("3DE4/LD_3DE_Classic_LD_Model",                 "nuke.createNode('LD_3DE_Classic_LD_Model')")
except Exception:
    nuke.tprint("[menu.py] 3DE4 entries skipped.")

# =====================================================================
#      Gloss NYC pipeline loader (kept exactly, but guarded)
# =====================================================================
import importlib.util

PIPELINE_DIR = "/Users/sheel/.nuke/GLOSS_NY_PIPELINE_v1.0.1"
SCRIPTS_DIR  = os.path.join(PIPELINE_DIR, "Python_Scripts")
ICON_DIR     = os.path.join(PIPELINE_DIR, "Icon")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    nuke.pluginAddPath(ICON_DIR)
except Exception:
    try:
        nuke.addPath(ICON_DIR)
    except Exception:
        nuke.tprint(f"[GLOSS NYC] ⚠️ Could not register icon path: {ICON_DIR}")

INTERNAL_MENU_FILE = os.path.join(PIPELINE_DIR, "menu.py")

def _load_module_from_path(mod_name, file_path):
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None

if os.path.isfile(INTERNAL_MENU_FILE):
    try:
        _load_module_from_path("GLOSS_NY_INTERNAL_MENU", INTERNAL_MENU_FILE)
        nuke.tprint("[GLOSS NYC] ✅ Pipeline menu loaded.")
    except Exception as e:
        nuke.tprint(f"[GLOSS NYC] ❌ Failed to load internal menu: {e}")
        traceback.print_exc()
else:
    nuke.tprint(f"[GLOSS NYC] ⚠️ Missing pipeline menu file: {INTERNAL_MENU_FILE}")




nuke.menu('Nodes').addCommand('GLOSS/Slate/LayerSlate', 'nuke.createNode("LayerSlate")')



# =====================================================================
#      Monday (GLOBAL) — optional. Guarded so startup never breaks
# =====================================================================
# --- Monday (Basic) menu ---
try:
    p = os.path.expanduser("~/.nuke/MONDAY_FOR_NUKE")
    if p not in sys.path:
        sys.path.append(p)
    import monday_menu_basic  # builds the menu on import
except Exception as e:
    nuke.tprint(f"[Monday] Basic menu not loaded: {e}")


# write_nodes/util_actions.py
import os, subprocess, platform, nuke

def _selected_write_nodes():
    nodes = [n for n in (nuke.selectedNodes() or []) if n.Class() == "Write"]
    if not nodes:
        try:
            n = nuke.selectedNode()
            if n.Class() == "Write":
                nodes = [n]
        except Exception:
            pass
    return nodes

def create_read_from_selected_write():
    nodes = _selected_write_nodes()
    if not nodes:
        nuke.message("Select a Write node.")
        return
    count = 0
    for w in nodes:
        try:
            path = w["file"].evaluate()
            nuke.createNode("Read", f"file {{{path}}}", inpanel=False)
            count += 1
        except Exception as e:
            nuke.message(f"Failed on {w.name()}: {e}")
    if count == 0:
        nuke.message("No Read created.")

def copy_selected_write_path():
    nodes = _selected_write_nodes()
    if not nodes:
        nuke.message("Select a Write node.")
        return
    path = nodes[0]["file"].evaluate()
    try:
        if platform.system() == "Darwin":
            subprocess.run(f'printf "%s" "{path}" | pbcopy', shell=True)
        else:
            # Try Qt clipboard if available
            try:
                from PySide6 import QtWidgets
            except Exception:
                try:
                    from PySide2 import QtWidgets
                except Exception:
                    QtWidgets = None
            if QtWidgets:
                app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
                app.clipboard().setText(path)
            else:
                raise RuntimeError("No clipboard backend available.")
        nuke.tprint(f"[GLOSS NYC] Copied: {path}")
    except Exception as e:
        nuke.message(f"Failed to copy path:\n{e}")

def open_selected_write_directory():
    nodes = _selected_write_nodes()
    if not nodes:
        nuke.message("Select a Write node.")
        return
    path = nodes[0]["file"].evaluate()
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        nuke.message(f"Directory not found:\n{folder}")
        return
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        elif platform.system() == "Windows":
            subprocess.Popen(["explorer", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        nuke.message(f"Failed to open directory:\n{e}")

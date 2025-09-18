"""
utils/nuke_helpers.py — Nuke helper functions for the Gloss NYC Pipeline
"""

import nuke
from gloss_utils import constants as C

def get_selected_nodes(node_class=None):
    """
    Returns a list of selected nodes.
    If node_class is given, filters to only those classes.
    """
    nodes = nuke.selectedNodes()
    if node_class:
        nodes = [n for n in nodes if n.Class() == node_class]
    return nodes

def select_single_node(node):
    """
    Clears selection and selects only the given node.
    """
    for n in nuke.allNodes():
        n.setSelected(False)
    node.setSelected(True)

def log_info(msg):
    """
    Logs a pipeline info message in the Nuke Script Editor.
    """
    nuke.tprint(f"{C.LOG_PREFIX} ✅ {msg}")

def log_warning(msg):
    """
    Logs a pipeline warning message in the Nuke Script Editor.
    """
    nuke.tprint(f"{C.LOG_PREFIX} ⚠️ {msg}")

def log_error(msg):
    """
    Logs a pipeline error message in the Nuke Script Editor.
    """
    nuke.tprint(f"{C.LOG_PREFIX} ❌ {msg}")

def safe_get_knob(node, knob_name):
    """
    Safely get a knob from a node.
    Returns None if it doesn't exist.
    """
    try:
        return node[knob_name]
    except KeyError:
        return None

def connect_nodes(input_node, output_node, input_index=0):
    """
    Connect output of input_node into the specified input index of output_node.
    """
    try:
        output_node.setInput(input_index, input_node)
    except Exception as e:
        log_error(f"Failed to connect nodes: {e}")

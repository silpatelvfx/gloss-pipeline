import os, re, nuke
from write_nodes.common import choose_output_type, apply_defaults, seq_ext, install_write_gloss_ui

def run():
    try:
        w = nuke.createNode("Write")
        w.setName("Gloss_PreComp_Write")

        out_type = choose_output_type()
        if out_type is None:
            nuke.delete(w); return

        apply_defaults(w, out_type)
        _set_path_precomp(w, out_type)

        # ⬇️ add this
        install_write_gloss_ui(w)

        nuke.addOnScriptSave(lambda: _set_path_precomp(w, _current_type(w)))
        try: w["label"].setValue(f"PreComp ({'MOV' if out_type=='mov' else out_type.upper()})")
        except Exception: pass
    except Exception as e:
        nuke.message(f"Failed to create PreComp Write node: {e}")

def _current_type(w):
    t = w["file_type"].value()
    return {"mov":"mov", "exr":"exr", "dpx":"dpx", "png":"png"}.get(t, "mov")

def _version_from(name): 
    m = re.search(r"_v(\d+)", name);  return m.group(1) if m else "01"

def _set_path_precomp(w, out_type):
    sp = nuke.root().name()
    if not sp or sp == "Root":
        w["file"].setValue("untitled" + (".mov" if out_type=="mov" else "/%04d"+seq_ext(out_type)[6:])); return

    scripts_dir = os.path.dirname(os.path.dirname(sp))
    shot_dir    = os.path.dirname(scripts_dir)
    shot = os.path.basename(shot_dir)
    ver  = _version_from(os.path.basename(sp))

    if out_type == "mov":
        os.makedirs(os.path.join(shot_dir, "PreComp"), exist_ok=True)
        fn = f"{shot}_PreComp_v{ver}.mov"
        w["file"].setValue(os.path.join(shot_dir, "PreComp", fn))
    else:
        version_dir = os.path.join(shot_dir, "PreComp", f"{shot}_PreComp_v{ver}")
        os.makedirs(version_dir, exist_ok=True)
        fn = f"{shot}_PreComp_v{ver}{seq_ext(out_type)}"
        w["file"].setValue(os.path.join(version_dir, fn))

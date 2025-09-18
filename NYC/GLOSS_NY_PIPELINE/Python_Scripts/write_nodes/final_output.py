import os, re, nuke
from datetime import datetime
from write_nodes.common import choose_output_type, apply_defaults, seq_ext, install_write_gloss_ui


try:
    from gloss_utils.paths_nyc import derive_job_from_path, glosspost_in_root
except Exception:
    def derive_job_from_path(p):
        parts = (p or "").split("/")
        code = next((x[:6] for x in parts if x[:6].isdigit()), None)
        folder = next((x for x in parts if code and x.startswith(code)), None)
        return code, folder
    def glosspost_in_root(project_folder, job_code=None):
        code = (job_code or (project_folder.split("_", 1)[0] if project_folder else None))
        return f"/Volumes/san-01/GlossPost/{project_folder}/IN-{code}" if project_folder and code else None

def run():
    try:
        w = nuke.createNode("Write")
        w.setName("Gloss_FinalApproved_Write")
        try: w["label"].setValue("Final for Approved")
        except Exception: pass

        out_type = choose_output_type()
        if out_type is None:
            nuke.delete(w); return

        apply_defaults(w, out_type)
        _set_path_final(w, out_type)

        # ⬇️ add this
        install_write_gloss_ui(w)

        nuke.addOnScriptSave(lambda: _set_path_final(w, _current_type(w)))
    except Exception as e:
        nuke.message(f"Failed to create Final for Approved Write node: {e}")

def _current_type(w):
    t = w["file_type"].value()
    return {"mov":"mov", "exr":"exr", "dpx":"dpx", "png":"png"}.get(t, "mov")

def _version_from(name): 
    m = re.search(r"_v(\d+)$", name);  return m.group(1) if m else "001"

def _base_vfx_dir():
    sp = nuke.root().name()
    job_code, project_folder = derive_job_from_path(sp)
    in_root = glosspost_in_root(project_folder, job_code)
    if not in_root:
        return None
    new_dir = os.path.join(in_root, "VFX-NY")
    old_dir = os.path.join(in_root, "FOOTAGE", "VFX-NY")
    if os.path.exists(new_dir): return new_dir
    if os.path.exists(old_dir): return old_dir
    return new_dir  # default to NEW layout if neither exists yet

def _set_path_final(w, out_type):
    sp = nuke.root().name()
    if not sp or sp == "Root":
        w["file"].setValue("untitled" + (".mov" if out_type=="mov" else "/%04d"+seq_ext(out_type)[6:])); return

    base_vfx = _base_vfx_dir()
    day_dir  = os.path.join(base_vfx or os.path.dirname(sp), datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(day_dir, exist_ok=True)

    script_name = os.path.splitext(os.path.basename(sp))[0]
    ver  = _version_from(script_name)
    clip = re.sub(r"_v\d+$", "", script_name)

    if out_type == "mov":
        w["file"].setValue(os.path.join(day_dir, f"{clip}_v{ver}.mov"))
    else:
        version_dir = os.path.join(day_dir, f"{clip}_v{ver}")
        os.makedirs(version_dir, exist_ok=True)
        w["file"].setValue(os.path.join(version_dir, f"{clip}_v{ver}{seq_ext(out_type)}"))

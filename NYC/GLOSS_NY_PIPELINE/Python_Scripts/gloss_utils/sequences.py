# utils/sequences.py
# Image-sequence detection & normalization utilities for the NYC pipeline.
# Supports:
#   - Hash style:        path/to/shot.####.exr
#   - Printf style:      path/to/shot.%04d.exr (or %d -> normalized to %04d)
#   - Digit suffix:      path/to/shot.0001.exr (infers width from files)

from __future__ import annotations
import os
import re
import glob
from typing import Optional, Tuple, Literal, List

# Try to import nuke (optional; this module still works without Nuke for testing)
try:
    import nuke  # type: ignore
except Exception:  # pragma: no cover
    nuke = None  # allows path-only usage in non-Nuke contexts

SeqStyle = Literal["printf", "hash", "digits"]

# --- Regexes ---
_RE_HASH     = re.compile(r"(#+)")
_RE_PRINTF   = re.compile(r"%0?(\d*)d")
_RE_DIGITS   = re.compile(r"^(?P<head>.*?)(?P<num>\d+)(?P<ext>\.[^.]+)$")
_RE_TAILNUM  = re.compile(r"(\d+)(\.[^.]+)$")  # for quick basename checks


# ---------- Utilities ----------
def _norm(path: str) -> str:
    """Normalize slashes for cross-platform safety."""
    return path.replace("\\", "/")


def _split_basename(path: str) -> Tuple[str, str]:
    path = _norm(path)
    d, b = os.path.split(path)
    return d, b


# ---------- Pattern Detection ----------
def detect_pattern(path: str) -> Optional[Tuple[SeqStyle, int, str, str, str]]:
    """
    Detects the sequence pattern in `path`.
    Returns: (style, width, head, token, tail)
        style:  "printf" | "hash" | "digits"
        width:  padding width (best guess, 4 if unknown)
        head:   path before the numeric slot
        token:  the token itself (#### or %04d or the literal 0001 digits)
        tail:   extension (e.g., .exr) or tail after digits

    If no sequence pattern found, returns None.
    """
    path = _norm(path)
    d, b = _split_basename(path)

    # 1) Hash style
    m = _RE_HASH.search(b)
    if m:
        hashes = m.group(1)
        width = len(hashes)
        head = path[: path.rfind(hashes)]
        tail = path[path.rfind(hashes) + len(hashes):]
        return ("hash", width, head, hashes, tail)

    # 2) Printf style
    m = _RE_PRINTF.search(b)
    if m:
        wtxt = m.group(1) or ""  # could be '' (plain %d)
        width = int(wtxt) if wtxt.isdigit() else 4  # normalize plain %d -> width 4
        token_span = m.span(0)
        head = path[: path.rfind(b) + token_span[0]]
        token = b[token_span[0]: token_span[1]]
        tail = b[token_span[1]:]
        return ("printf", width, head, token, tail)

    # 3) Digit suffix style (...0001.ext)
    m = _RE_DIGITS.match(b)
    if m:
        num = m.group("num")
        width = len(num)
        head = os.path.join(d, m.group("head")).replace("\\", "/")
        token = num
        tail = m.group("ext")
        return ("digits", width, head, token, tail)

    return None


# ---------- Normalization ----------
def normalize_padding(path: str) -> str:
    """
    Convert any supported pattern into canonical printf form:
        - ####  -> %0Nd
        - %d    -> %04d
        - 0001  -> %0Nd   (width inferred from existing digits)
    """
    path = _norm(path)
    det = detect_pattern(path)
    if not det:
        return path  # not a sequence

    style, width, head, token, tail = det
    if style == "printf":
        # Ensure explicit width (normalize %d -> %04d)
        m = _RE_PRINTF.search(token)
        wtxt = m.group(1) if m else ""
        if not wtxt:
            return f"{head}%0{width}d{tail}"
        return head + token + tail  # already %0Nd

    # hash or digits -> printf
    return f"{head}%0{width}d{tail}"


def resolve_frame_path(path: str, frame: int) -> str:
    """
    Given a (possibly hash/printf/digits) path, return the concrete path for `frame`,
    using canonical printf normalization.
    """
    path = normalize_padding(path)
    def _fmt(m):
        w = int(m.group(1))
        return f"{frame:0{w}d}"
    return re.sub(r"%0(\d+)d", _fmt, path)


def get_glob_pattern(path: str) -> str:
    """
    Given a sequence path (any style), return a glob pattern that matches all frames.
    Example: shot.%04d.exr -> shot.????.exr
    """
    path = normalize_padding(path)
    def _qs(m):
        w = int(m.group(1))
        return "?" * w
    return re.sub(r"%0(\d+)d", _qs, path)


# ---------- Identification ----------
def is_sequence_path(path: str, confirm_files: bool = False) -> bool:
    """
    Returns True if `path` looks like a sequence pattern.
    If confirm_files=True, ensures more than one file exists matching the pattern.
    """
    path = _norm(path)
    det = detect_pattern(path)
    if not det:
        return False
    if not confirm_files:
        return True

    # Confirm by filesystem
    glob_pat = get_glob_pattern(path)
    matches = glob.glob(glob_pat)
    return len(matches) > 1


def is_sequence(read_node) -> bool:
    """
    Nuke-aware wrapper: checks the currently set filename on a Read node.
    Accepts either printf/hash/digits patterns. If it’s digits, attempts to confirm by globbing.
    """
    if nuke is None or read_node is None:
        return False
    try:
        file_path = nuke.filename(read_node)
        if not file_path:
            return False
        # For digits style, it helps to confirm existence of siblings
        det = detect_pattern(file_path)
        if not det:
            return False
        style, *_ = det
        if style == "digits":
            return is_sequence_path(file_path, confirm_files=True)
        return True
    except Exception:
        return False


# ---------- Shot/Folder helpers ----------
def derive_shot_from_sequence_dir(path_or_read) -> Optional[str]:
    """
    For image sequences, derive shot name from the parent folder.
    - If given a Read node, uses nuke.filename(read).
    - If given a path string, uses that directly.
    Returns the folder basename, or None.
    """
    path = None
    if nuke and hasattr(path_or_read, "Class"):  # likely a node
        try:
            path = nuke.filename(path_or_read)
        except Exception:
            path = None
    if isinstance(path_or_read, str):
        path = path_or_read

    if not path:
        return None
    path = _norm(path)
    parent = os.path.dirname(path)
    if not parent:
        return None
    return os.path.basename(parent)


# ---------- Frame range detection ----------
def detect_frame_range(path: str) -> Optional[Tuple[int, int, int]]:
    """
    Returns (start, end, count) for the sequence at `path`.
    Works for all pattern styles by globbing the normalized pattern.
    Returns None if not a sequence or no files found.
    """
    path = _norm(path)
    if not detect_pattern(path):
        return None

    glob_pat = get_glob_pattern(path)
    files = sorted(glob.glob(glob_pat))
    if not files:
        return None

    frames: List[int] = []
    for f in files:
        base = os.path.basename(f)
        m = _RE_TAILNUM.search(base)
        if not m:
            continue
        frames.append(int(m.group(1)))

    if not frames:
        return None

    return (min(frames), max(frames), len(frames))


def padding_width(path: str) -> Optional[int]:
    """Convenience: return the detected padding width, or None."""
    det = detect_pattern(path)
    return det[1] if det else None


# ---------- Pretty helpers ----------
def to_printf(path: str) -> str:
    """Alias for normalize_padding()."""
    return normalize_padding(path)


def to_hash(path: str) -> str:
    """Convert any style to hash (####) style, preserving width."""
    path = _norm(path)
    det = detect_pattern(path)
    if not det:
        return path
    style, width, head, token, tail = det
    hashes = "#" * width
    if style == "hash":
        return head + token + tail
    if style == "printf":
        return re.sub(r"%0\d*d", hashes, head + token + tail)
    # digits
    return f"{head}{hashes}{tail}"

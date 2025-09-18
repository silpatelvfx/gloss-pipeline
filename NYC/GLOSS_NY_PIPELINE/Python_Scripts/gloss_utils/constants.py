"""
utils/constants.py — Centralized constants for the Gloss NYC Pipeline
"""

import os

# --- Base Paths ---
PIPELINE_ROOT = "/Users/sheel/.nuke/GLOSS_NY_PIPELINE"

PYTHON_SCRIPTS_DIR = os.path.join(PIPELINE_ROOT, "Python_Scripts")
ICON_DIR           = os.path.join(PIPELINE_ROOT, "Icon")

# --- File Formats ---
MOV_EXTENSIONS     = (".mov", ".mp4")
IMAGE_EXTENSIONS   = (".exr", ".dpx", ".tif", ".tiff", ".jpg", ".jpeg", ".png")

# --- Pipeline Settings ---
# This can be expanded later to store NYC-specific folder templates
NYC_APPROVED_DIR_NAME = "Approved"  # Example: can be overridden later
NYC_QC_DIR_NAME       = "QC"

# --- Logging Prefix ---
LOG_PREFIX = "[GLOSS NYC]"

# --- Colors ---
COLOR_CHENNAI         = 0xFF8000FF
COLOR_NYC             = 0x0000FFFF
COLOR_REVIEW_NEEDED   = 0x00FFFFFF
COLOR_REVISION_NEEDED = 0xE62E00FF
COLOR_COMPLETE        = 0x009933FF

"""Source-tree launcher (no console): used by run paths that cannot set
PYTHONPATH - double-click, and the HKCU autostart entry."""
import os
import runpy
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))

runpy.run_module("batterybar", run_name="__main__")

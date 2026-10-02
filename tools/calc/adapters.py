# Compatibility wrapper: moved to astro/calc/adapters.py
import os
import runpy
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from astro.calc.adapters import *  # noqa: E402,F401,F403

if __name__ == "__main__":
    runpy.run_module("astro.calc.adapters", run_name="__main__")

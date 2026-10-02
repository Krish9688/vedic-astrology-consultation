"""Compatibility wrapper: the VedAstro batch fetcher now lives in the package as `astro.vedastro_batch`."""
import os
import runpy
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
runpy.run_module("astro.vedastro_batch", run_name="__main__")

# tools/workspace_sync.py reverses export_repo.py's path map; a wrong map would silently drop cloud-session changes.
import os
import subprocess
import sys

import pytest

TOOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "workspace_sync.py")


@pytest.mark.skipif(not os.path.exists(TOOL), reason="private-edition tooling")
def test_workspace_sync_selftest():
    assert subprocess.run([sys.executable, TOOL, "selftest"], capture_output=True, text=True).stdout == "selftest ok\n"

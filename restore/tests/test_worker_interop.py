"""A key signed by the license worker's JavaScript verifies in the app (skipped without Node)."""
import json
import os
import shutil
import subprocess

import pytest

from arcana_restore import licensing

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "license-worker", "test", "issue_for_python.mjs")


@pytest.mark.skipif(not shutil.which("node") or not os.path.exists(SCRIPT), reason="needs node and license-worker/")
def test_worker_signed_key_verifies_in_app():
    out = json.loads(subprocess.run(["node", SCRIPT], capture_output=True, text=True, check=True).stdout)
    payload = licensing.verify_key(out["key"], [out["public_key"]])
    assert payload["product"] == licensing.PRODUCT and payload["name"] == "Ann Exäminer"
    assert payload["expires"] is None and payload["order"] == "cs_test_interop000001"

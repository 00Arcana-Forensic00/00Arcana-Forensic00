"""The desktop app opens what the Android app seals.

CI runs the Android core's JUnit suite with ARCALUME_INTEROP_OUT set; its sealing test
leaves a vault, a ledger and expect.json there. This test opens them with the desktop
code. Skipped when that directory was not produced (plain local runs).
"""
import json
import os
from pathlib import Path

import pytest

from arcana_restore import pipeline
from arcana_restore.ledger import Ledger

OUT = os.environ.get("ARCALUME_INTEROP_OUT")


@pytest.mark.skipif(not OUT or not (Path(OUT) / "expect.json").exists(), reason="no Android interop output")
def test_desktop_opens_android_vault_and_ledger(tmp_path):
    out = Path(OUT)
    expect = json.loads((out / "expect.json").read_text())
    ok, n, head, msg = Ledger(str(out / pipeline.LEDGER_NAME)).verify(expect["head"])
    assert ok and n == 1, msg
    written = pipeline.extract(str(out / expect["vault"]), expect["passphrase"], str(tmp_path))
    by_role = {p.rsplit(".", 2)[-2]: p for p in written}
    assert pipeline.sha256(Path(by_role["original"]).read_bytes()) == expect["original_sha256"]
    manifest = json.loads(Path(by_role["manifest"]).read_text())
    assert manifest["report"]["status"] == "repaired"
    assert manifest["source_name"] == "Receipt – März.png"

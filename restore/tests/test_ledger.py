import json
from arcana_restore.ledger import Ledger


def test_chain_verifies_and_detects_edit(tmp_path):
    lg = Ledger(str(tmp_path / "l.jsonl"))
    for i in range(5):
        lg.append("e", {"i": i})
    ok, n, head, _ = lg.verify()
    assert ok and n == 5
    lines = (tmp_path / "l.jsonl").read_text().splitlines()
    e = json.loads(lines[2]); e["data"]["i"] = 99
    lines[2] = json.dumps(e, sort_keys=True, separators=(",", ":"))
    (tmp_path / "l.jsonl").write_text("\n".join(lines) + "\n")
    assert not Ledger(str(tmp_path / "l.jsonl")).verify()[0]


def test_deleted_middle_and_truncated_tail(tmp_path):
    p = tmp_path / "l.jsonl"
    lg = Ledger(str(p))
    for i in range(5):
        lg.append("e", {"i": i})
    _, _, head, _ = lg.verify()
    lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    assert not lg.verify()[0]
    p.write_text("\n".join(lines[:3]) + "\n")
    assert lg.verify()[0]                      # chain alone cannot see a cut tail...
    assert not lg.verify(expect_head=head)[0]  # ...an externally recorded head can


def test_concurrent_appends_stay_chained(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    lg = Ledger(str(tmp_path / "l.jsonl"))
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda i: lg.append("e", {"i": i}), range(40)))
    ok, n, _, _ = lg.verify()
    assert ok and n == 40

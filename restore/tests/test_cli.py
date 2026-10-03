"""Command-line behaviour: friendly errors (never a traceback) and stable exit codes.

0 = success; 1 = a file failed or an I/O problem; 2 = usage, wrong passphrase, or not a valid vault.
"""
import pytest
from conftest import PW
from arcana_restore import cli


@pytest.fixture
def pwfile(tmp_path):
    p = tmp_path / "pw"; p.write_text(PW + "\n")
    return str(p)


def run(capsys, *argv):
    code = cli.main(list(argv))
    out = capsys.readouterr()
    assert "Traceback" not in out.err + out.out
    return code, out.out, out.err


def test_missing_passphrase_file_is_a_clear_error(capsys, evidence, tmp_path):
    with pytest.raises(SystemExit) as e:
        cli.main(["process", str(evidence), "-o", str(tmp_path / "v"), "--passphrase-file", str(tmp_path / "nope")])
    assert e.value.code == 2 and "cannot read the passphrase file" in capsys.readouterr().err


def test_inspect_missing_and_non_vault(capsys, evidence, tmp_path):
    code, _, err = run(capsys, "inspect", str(tmp_path / "nope.arcr"))
    assert code == 1 and "No such file" in err
    code, _, err = run(capsys, "inspect", str(evidence))
    assert code == 2 and "not an Arcana vault" in err


def test_extract_exit_codes(capsys, evidence, tmp_path, pwfile):
    v = str(tmp_path / "v")
    assert run(capsys, "process", str(evidence), "-o", v, "--passphrase-file", pwfile)[0] == 0
    import os
    arcr = os.path.join(v, [f for f in os.listdir(v) if f.endswith(".arcr")][0])
    assert run(capsys, "extract", str(evidence), "-o", str(tmp_path / "o"), "--passphrase-file", pwfile)[0] == 2   # not a vault
    assert run(capsys, "extract", arcr, "-o", str(tmp_path / "o"), "--passphrase-file", pwfile)[0] == 0
    code, _, err = run(capsys, "extract", arcr, "-o", str(tmp_path / "o"), "--passphrase-file", pwfile)
    assert code == 1 and "already exists" in err                                                                    # output clash
    bad = tmp_path / "bad"; bad.write_text("not the right passphrase")
    assert run(capsys, "extract", arcr, "-o", str(tmp_path / "o2"), "--passphrase-file", str(bad))[0] == 2          # wrong passphrase


def test_verify_ledger_on_wrong_folder_fails_instead_of_passing(capsys, tmp_path):
    code, out, _ = run(capsys, "verify-ledger", "--vault", str(tmp_path / "typo"))
    assert code == 1 and "FAILED" in out and "no ledger file" in out


def test_verify_ledger_ok_after_sealing(capsys, evidence, tmp_path, pwfile):
    v = str(tmp_path / "v")
    run(capsys, "process", str(evidence), "-o", v, "--passphrase-file", pwfile)
    code, out, _ = run(capsys, "verify-ledger", "--vault", v)
    assert code == 0 and "VERIFIED" in out


def test_folder_with_a_bad_file_exits_1_but_seals_the_good_ones(capsys, evidence, tmp_path, pwfile):
    d = evidence.parent
    (d / "junk.png").write_bytes(b"MZ" + b"0" * 64)
    code, out, err = run(capsys, "process", str(d), "-o", str(tmp_path / "v"), "--passphrase-file", pwfile)
    assert code == 1 and "1/2 sealed" in out and "junk.png" in err


def test_no_command_or_unknown_command(capsys):
    for argv in ([], ["frobnicate"]):
        with pytest.raises(SystemExit) as e:
            cli.main(argv)
        assert e.value.code == 2

import pytest

from arcana_recon import synth

PASSPHRASE = "correct horse battery staple extra"


@pytest.fixture(scope="session")
def page():
    return synth.make_page(seed=7)

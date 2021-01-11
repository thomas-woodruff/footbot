import os
from pathlib import Path

import pytest

from footbot.data.utils import set_up_bigquery


@pytest.fixture(scope="session")
def client():
    secrets_path = os.path.join(
        Path(__file__).parents[2], "secrets/service_account.json"
    )
    return set_up_bigquery(secrets_path)

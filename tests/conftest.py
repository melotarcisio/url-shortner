import pytest

from uuid import uuid4
from fastapi.testclient import TestClient
from modules.server import app
from modules.models import UrlCreate
from typing import Generator


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def some_url() -> UrlCreate:
    return UrlCreate(
        url="https://www.google.com",
    )

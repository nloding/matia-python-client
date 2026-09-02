import httpx
import pytest
import respx

from matia import MatiaClient

BASE_URL = "https://api.matia.io/v1"


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client():
    with MatiaClient(api_key="test-key", base_url=BASE_URL) as c:
        yield c

import pytest
import tempfile
import pathlib
from unittest.mock import patch, MagicMock
from webapp.utils import download_eml_to_cache

class DummyResponse:
    def __init__(self, content, ok=True, reason=None):
        self.content = content
        self.ok = ok
        self.reason = reason or "Error"

@pytest.fixture
def temp_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@patch("webapp.utils.requests.get")
@patch("webapp.markdown_cache.safe_filename", lambda pid: f"safe_{pid}")
def test_download_eml_to_cache_success(mock_get, temp_cache):
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache
    eml_content = b"<eml>test</eml>"
    mock_get.return_value = DummyResponse(eml_content, ok=True)

    result_path = download_eml_to_cache(pid, pasta_url, cache)
    expected_path = pathlib.Path(cache, f"safe_{pid}.eml.xml")
    assert result_path == str(expected_path)
    assert expected_path.is_file()
    assert expected_path.read_bytes() == eml_content

@patch("webapp.utils.requests.get")
@patch("webapp.markdown_cache.safe_filename", lambda pid: f"safe_{pid}")
def test_download_eml_to_cache_http_error(mock_get, temp_cache):
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache
    mock_get.return_value = DummyResponse(b"", ok=False, reason="Not Found")
    with pytest.raises(Exception):
        download_eml_to_cache(pid, pasta_url, cache)


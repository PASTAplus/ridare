import pytest
import tempfile
import pathlib
from unittest.mock import patch, MagicMock
from webapp.utils import download_eml_to_cache, get_eml
from webapp.markdown_cache import safe_filename

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
def test_download_eml_to_cache_success(mock_get, temp_cache):
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache
    eml_content = b"<eml>test</eml>"
    mock_get.return_value = DummyResponse(eml_content, ok=True)

    result_path = download_eml_to_cache(pid, pasta_url, cache)
    expected_path = pathlib.Path(cache, f"{safe_filename(pid)}.eml.xml")
    assert result_path == str(expected_path)
    assert expected_path.is_file()
    assert expected_path.read_bytes() == eml_content

@patch("webapp.utils.requests.get")
def test_download_eml_to_cache_http_error(mock_get, temp_cache):
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache
    mock_get.return_value = DummyResponse(b"", ok=False, reason="Not Found")
    with pytest.raises(Exception):
        download_eml_to_cache(pid, pasta_url, cache)


@patch("webapp.config.Config.PASTA_D", "https://fake-pasta-url.org")
@patch("webapp.config.Config.CACHE_D", None)
def test_get_eml_cache_hit(temp_cache):
    pid = "edi.521.1"
    env = "dev"
    cache_dir = temp_cache
    eml_path = pathlib.Path(cache_dir, f"{safe_filename(pid)}.eml.xml")
    eml_content = b"<eml>cached</eml>"
    eml_path.write_bytes(eml_content)
    with patch("webapp.config.Config.CACHE_D", str(cache_dir)):
        result = get_eml(pid, env)
        assert result == eml_content

@patch("webapp.config.Config.PASTA_D", "https://fake-pasta-url.org")
@patch("webapp.config.Config.CACHE_D", None)
@patch("webapp.utils.download_eml_to_cache")
def test_get_eml_cache_miss(mock_download, temp_cache):
    pid = "edi.521.1"
    env = "dev"
    cache_dir = temp_cache
    with patch("webapp.config.Config.CACHE_D", str(cache_dir)):
        mock_download.return_value = b"<eml>test</eml>"
        result = get_eml(pid, env)
        assert result == b"<eml>test</eml>"
        mock_download.assert_called_once()

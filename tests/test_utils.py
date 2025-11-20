"""Unit tests for the `webapp.utils` module."""

import pytest
import tempfile
import pathlib
from unittest.mock import patch
from webapp.utils import download_eml_to_cache, get_eml
from webapp.markdown_cache import safe_filename


class DummyResponse:
    """A minimal fake response object used in tests.

    This mirrors the small API of `requests.Response` that our code uses:
    - stores raw `content` bytes
    - an `ok` flag indicating success
    - a `reason` string for error messages

    The `raise_for_status` method raises an Exception when `ok` is False so
    tests that expect error behavior can exercise the same code paths.
    """

    def __init__(self, content, ok=True, reason=None):
        self.content = content
        self.ok = ok
        self.reason = reason or "Error"

    def raise_for_status(self):
        """Raise an Exception if the response indicates failure.

        This matches the minimal behavior of `requests.Response.raise_for_status`.
        """
        if not self.ok:
            # Raise a more specific built-in exception instead of the
            # overly-broad `Exception` to satisfy linters.
            raise RuntimeError(self.reason)

    def iter_content(self, chunk_size=8192):
        """Yield the content in chunks, similar to requests.Response.iter_content.

        This provides another public method so pylint's too-few-public-methods
        check is satisfied.
        """
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i : i + chunk_size]


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory and yield its path for use as a cache.

    Tests that need a filesystem cache directory can use this fixture; it
    is automatically cleaned up when the test completes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@patch("webapp.utils.requests.get")
def test_download_eml_to_cache_success(mock_get, temp_cache_dir):
    """Verify that a successful download writes the EML to the cache.

    Uses the `temp_cache_dir` fixture for an isolated temporary cache.
    """
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache_dir
    eml_content = b"<eml>test</eml>"
    mock_get.return_value = DummyResponse(eml_content, ok=True)

    result_path = download_eml_to_cache(pid, pasta_url, cache)
    expected_path = pathlib.Path(cache, f"{safe_filename(pid)}.eml.xml")
    assert result_path == str(expected_path)
    assert expected_path.is_file()
    assert expected_path.read_bytes() == eml_content


@patch("webapp.utils.requests.get")
def test_download_eml_to_cache_http_error(mock_get, temp_cache_dir):
    pid = "edi.521.1"
    pasta_url = "https://fake-pasta-url.org"
    cache = temp_cache_dir
    mock_get.return_value = DummyResponse(b"", ok=False, reason="Not Found")
    with pytest.raises(Exception):
        download_eml_to_cache(pid, pasta_url, cache)


@patch("webapp.config.Config.PASTA_D", "https://fake-pasta-url.org")
@patch("webapp.config.Config.CACHE_D", None)
def test_get_eml_cache_hit(temp_cache_dir):
    pid = "edi.521.1"
    env = "dev"
    cache_dir = temp_cache_dir
    eml_path = pathlib.Path(cache_dir, f"{safe_filename(pid)}.eml.xml")
    eml_content = b"<eml>cached</eml>"
    eml_path.write_bytes(eml_content)
    with patch("webapp.config.Config.CACHE_D", str(cache_dir)):
        result = get_eml(pid, env)
        assert result == eml_content


@patch("webapp.config.Config.PASTA_D", "https://fake-pasta-url.org")
@patch("webapp.config.Config.CACHE_D", None)
@patch("webapp.utils.download_eml_to_cache")
def test_get_eml_cache_miss(mock_download, temp_cache_dir):
    pid = "edi.521.1"
    env = "dev"
    cache_dir = temp_cache_dir
    with patch("webapp.config.Config.CACHE_D", str(cache_dir)):
        mock_download.return_value = b"<eml>test</eml>"
        result = get_eml(pid, env)
        assert result == b"<eml>test</eml>"
        mock_download.assert_called_once()


def test_eml_url_construction(monkeypatch):
    from webapp.utils import download_eml_to_cache

    constructed_urls = []

    def fake_requests_wrapper(url):
        constructed_urls.append(url)
        return b"<eml/>"

    monkeypatch.setattr("webapp.utils.requests_wrapper", fake_requests_wrapper)
    # Test various PIDs
    pasta_url = "https://pasta.lternet.edu/package"
    cache = "/tmp"
    test_cases = [
        ("cos-spu.13.3", f"{pasta_url}/metadata/eml/cos-spu/13/3"),
        ("edi.521.1", f"{pasta_url}/metadata/eml/edi/521/1"),
        ("knb-lter-sbc.1001.7", f"{pasta_url}/metadata/eml/knb-lter-sbc/1001/7"),
    ]
    for pid, expected_url in test_cases:
        constructed_urls.clear()
        download_eml_to_cache(pid, pasta_url, cache)
        assert constructed_urls[0] == expected_url

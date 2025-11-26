"""Pytest suite for /multi endpoint and related XML response logic in the ridare webapp."""

import pytest
import lxml.etree
from webapp.run import app
import tests.util.sample as sample


@pytest.fixture(name="client")
def test_client():
    """Create and return a Flask test client for the webapp."""
    return app.test_client()


# Common payloads
PAYLOAD_BASIC = {"pid": ["edi.521.1"], "query": ["dataset/title"]}
PAYLOAD_MULTIPLE_PIDS = {
    "pid": ["edi.521.1", "knb-lter-sbc.1001.7"],
    "query": ["dataset/title"],
}
PAYLOAD_MISSING_OR_INVALID_PIDS = {
    "pid": ["edi.521.1", "notarealpid.123.456", "badformatpid"],
    "query": ["dataset/title"],
}
PAYLOAD_MULTIPLE_QUERIES = {
    "pid": ["edi.521.1"],
    "query": ["dataset/title", "not/a/real/xpath", "dataset/language"],
}


def post_multi(client, payload=None, data=None, content_type=None):
    """Send a POST request to the /multi endpoint with the given payload or data."""
    if payload is not None:
        response = client.post("/multi", json=payload)
    elif data is not None:
        response = client.post("/multi", data=data, content_type=content_type)
    else:
        response = client.post("/multi", json={})
    return response


def parse_xml_response(response):
    """Parse the XML response from the /multi endpoint and return the root element."""
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    root = lxml.etree.fromstring(response.data)  # pylint: disable=c-extension-no-member
    assert root.tag == "resultset"
    return root


def assert_invalid_request(response):
    """Assert that the response is a 400 error with an invalid request format message."""
    assert response.status_code == 400
    assert b"Invalid request format" in response.data


def assert_element_absent(document, tag):
    """Assert that the given tag is absent from the document element."""
    assert document.find(tag) is None


def test_multi_basic(client):
    """Test /multi endpoint with a single valid PID and query."""
    response = post_multi(client, payload=PAYLOAD_BASIC)
    root = parse_xml_response(response)
    document = lxml.etree.tostring(root.find("document"), encoding="unicode")
    assert document is not None
    sample.assert_match(document, "multi_basic", ".xml")


def test_multi_multiple_pids_valid(client):
    """Test /multi endpoint with multiple valid PIDs and a single query."""
    response = post_multi(client, payload=PAYLOAD_MULTIPLE_PIDS)
    root = parse_xml_response(response)
    documents = root.findall("document")
    assert len(documents) == 2
    for i, document in enumerate(documents):
        document = lxml.etree.tostring(root.find("document"), encoding="unicode")
        sample.assert_match(document, f"multi_multiple_pids_valid_{i}", ".xml")


def test_multi_some_missing_or_invalid_pids(client, caplog):
    """Test /multi endpoint with some missing or invalid PIDs."""
    caplog.set_level("CRITICAL")
    response = post_multi(client, payload=PAYLOAD_MISSING_OR_INVALID_PIDS)
    root = parse_xml_response(response)
    documents = root.findall("document")
    assert len(documents) == 1
    document = documents[0]
    document = lxml.etree.tostring(document, encoding="unicode")
    sample.assert_match(document, "multi_some_missing_or_invalid_pids", ".xml")


def test_multi_multiple_queries_varied_results(client):
    """Test /multi endpoint with multiple queries, including invalid and empty-result XPaths."""
    response = post_multi(client, payload=PAYLOAD_MULTIPLE_QUERIES)
    root = parse_xml_response(response)
    documents = root.findall("document")
    assert len(documents) == 1
    for i, document in enumerate(documents):
        document_xml = lxml.etree.tostring(root.find("document"), encoding="unicode")
        sample.assert_match(document_xml, f"multi_multiple_queries_varied_results_{i}", ".xml")
        # Check that invalid XPath does not add elements named 'not/a/real/xpath'
        assert document.find("not/a/real/xpath") is None
        # Check that empty-result XPath does not add elements named 'language'
        assert document.find("language") is None


def test_multi_missing_pid_field(client, caplog):
    """Test /multi endpoint with missing 'pid' field in payload."""
    caplog.set_level("CRITICAL")
    payload = {"query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_missing_query_field(client, caplog):
    """Test /multi endpoint with missing 'query' field in payload."""
    caplog.set_level("CRITICAL")
    payload = {"pid": ["edi.521.1"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_pid_not_list(client, caplog):
    """Test /multi endpoint with 'pid' field not as a list."""
    caplog.set_level("CRITICAL")
    payload = {"pid": "edi.521.1", "query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_query_not_list(client, caplog):
    """Test /multi endpoint with 'query' field not as a list."""
    caplog.set_level("CRITICAL")
    payload = {"pid": ["edi.521.1"], "query": "dataset/title"}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_empty_post_body(client, caplog):
    """Test /multi endpoint with empty POST body."""
    caplog.set_level("CRITICAL")
    response = post_multi(client)
    assert_invalid_request(response)


def test_multi_non_json_post_body(client, caplog):
    """Test /multi endpoint with non-JSON POST body."""
    caplog.set_level("CRITICAL")
    response = post_multi(client, data="not a json", content_type="text/plain")
    assert_invalid_request(response)


def test_multi_mixed_query_semantics(client):
    """Test /multi endpoint with mixed query types, including labeled queries and invalid tags."""
    payload = {
        "pid": ["edi.521.1"],
        "query": [
            "dataset/title",  # Simple XPath
            {"projectTitle": "dataset/project/title"},  # Valid labeled query
            {"123badtag": "dataset/title"},  # Invalid XML tag name
            {"emptyResult": "not/a/real/xpath"},  # XPath returns no nodes
        ],
    }
    response = post_multi(client, payload=payload)
    root = parse_xml_response(response)
    document = root.find("document")
    assert document is not None
    document_xml = lxml.etree.tostring(document, encoding="unicode")
    sample.assert_match(document_xml, "multi_mixed_query_semantics", ".xml")
    # Should contain dataset/title as direct child (simple XPath)
    assert any(t.text for t in document.findall("title"))
    # Should contain projectTitle wrapper with dataset/project/title inside
    project_title = document.find("projectTitle")
    assert project_title is not None
    assert any(child.tag == "title" and child.text for child in project_title)
    # Should NOT contain invalid or empty tags
    for tag in ["123badtag", "emptyResult"]:
        assert_element_absent(document, tag)


def test_multi_empty_pid_list(client, caplog):
    """Test /multi endpoint with empty PID list, expecting DataPackageError response."""
    caplog.set_level("CRITICAL")
    payload = {"pid": [], "query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert response.status_code == 400
    assert b"Data package error" in response.data


def test_multi_pid_with_empty_string(client, caplog):
    """Test /multi endpoint with PID list containing empty string, expecting
    DataPackageError response."""
    caplog.set_level("CRITICAL")
    payload = {"pid": [""], "query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert response.status_code == 400
    assert b"Data package error" in response.data


def test_multi_invalid_env_argument(client, caplog):
    """Test /multi endpoint with an invalid environment argument, expecting
    PastaEnvironmentError response."""
    caplog.set_level("CRITICAL")
    response = client.post(
        "/multi?env=invalidenv", json={"pid": ["edi.521.1"], "query": ["dataset/title"]}
    )
    assert response.status_code == 400
    assert b"PASTA environment error" in response.data

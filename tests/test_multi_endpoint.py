"""Pytest suite for /multi endpoint and related XML response logic in the ridare webapp."""

import pytest
import lxml.etree
from webapp.run import app


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


def assert_document_structure(document, pid=None, title_required=True):
    """Assert the structure of a document element, optionally checking PID and title presence."""
    packageid = document.find("packageid")
    assert packageid is not None
    if pid is not None:
        assert packageid.text == pid
    title = document.find("title")
    if title_required:
        assert title is not None
        assert title.text is not None and len(title.text) > 0


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
    document = root.find("document")
    assert document is not None
    assert_document_structure(document)


def test_multi_multiple_pids_valid(client):
    """Test /multi endpoint with multiple valid PIDs and a single query."""
    response = post_multi(client, payload=PAYLOAD_MULTIPLE_PIDS)
    root = parse_xml_response(response)
    documents = root.findall("document")
    assert len(documents) == 2
    for document, pid in zip(documents, PAYLOAD_MULTIPLE_PIDS["pid"]):
        assert_document_structure(document, pid=pid)


def test_multi_some_missing_or_invalid_pids(client, caplog):
        """Test /multi endpoint with some missing or invalid PIDs."""
        caplog.set_level("CRITICAL")
        response = post_multi(client, payload=PAYLOAD_MISSING_OR_INVALID_PIDS)
        root = parse_xml_response(response)
        documents = root.findall("document")
        assert len(documents) == 1
        document = documents[0]
        assert_document_structure(document, pid="edi.521.1")


def test_multi_multiple_queries_varied_results(client):
    """Test /multi endpoint with multiple queries, including invalid and empty-result XPaths."""
    response = post_multi(client, payload=PAYLOAD_MULTIPLE_QUERIES)
    root = parse_xml_response(response)
    documents = root.findall("document")
    assert len(documents) == 1
    for document, pid in zip(documents, PAYLOAD_MULTIPLE_QUERIES["pid"]):
        assert_document_structure(document, pid=pid)
        # Check that invalid XPath does not add elements named 'not/a/real/xpath'
        assert document.find("not/a/real/xpath") is None
        # Check that empty-result XPath does not add elements named 'language'
        assert document.find("language") is None


def test_multi_missing_pid_field(client):
    """Test /multi endpoint with missing 'pid' field in payload."""
    payload = {"query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_missing_query_field(client):
    """Test /multi endpoint with missing 'query' field in payload."""
    payload = {"pid": ["edi.521.1"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_pid_not_list(client):
    """Test /multi endpoint with 'pid' field not as a list."""
    payload = {"pid": "edi.521.1", "query": ["dataset/title"]}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_query_not_list(client):
    """Test /multi endpoint with 'query' field not as a list."""
    payload = {"pid": ["edi.521.1"], "query": "dataset/title"}
    response = post_multi(client, payload=payload)
    assert_invalid_request(response)


def test_multi_empty_post_body(client):
    """Test /multi endpoint with empty POST body."""
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
    assert_document_structure(document)
    # Should contain dataset/title as direct child (simple XPath)
    assert any(t.text for t in document.findall("title"))
    # Should contain projectTitle wrapper with dataset/project/title inside
    project_title = document.find("projectTitle")
    assert project_title is not None
    assert any(child.tag == "title" and child.text for child in project_title)
    # Should NOT contain invalid or empty tags
    for tag in ["123badtag", "emptyResult"]:
        assert_element_absent(document, tag)

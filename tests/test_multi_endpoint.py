from webapp.run import app
import lxml.etree

def test_multi_basic():
    client = app.test_client()
    # Minimal valid POST body
    payload = {
        "pid": ["edi.521.1"],
        "query": ["dataset/title"]
    }
    response = client.post("/multi", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    # Check that the response is valid XML and contains expected structure
    root = lxml.etree.fromstring(response.data)
    assert root.tag == "resultset"
    document = root.find("document")
    assert document is not None
    # Check that the document contains the expected elements
    packageid = document.find("packageid")
    assert packageid is not None
    title = document.find("title")
    assert title is not None

def test_multi_multiple_pids_valid():
    """
    Test /multi endpoint with multiple valid pids and a single XPath query.
    Verifies that the response contains two <document> elements, each with the correct <packageid>
    and a non-empty <title> element, confirming that valid results are returned for each pid.
    """
    client = app.test_client()
    payload = {
        "pid": ["edi.521.1", "knb-lter-sbc.1001.7"],
        "query": ["dataset/title"]
    }
    response = client.post("/multi", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    root = lxml.etree.fromstring(response.data)
    assert root.tag == "resultset"
    documents = root.findall("document")
    assert len(documents) == 2
    for document, pid in zip(documents, payload["pid"]):
        packageid = document.find("packageid")
        assert packageid is not None
        assert packageid.text == pid
        title = document.find("title")
        assert title is not None
        assert title.text is not None and len(title.text) > 0

def test_multi_some_missing_or_invalid_pids():
    """
    Test /multi endpoint with multiple pids: one valid, one missing, and one with invalid format.
    Verifies that only the valid pid returns a <document> with a non-empty <title>.
    Documents for missing/invalid pids should not be present in the resultset.
    """
    client = app.test_client()
    payload = {
        "pid": ["edi.521.1", "notarealpid.123.456", "badformatpid"],
        "query": ["dataset/title"]
    }
    response = client.post("/multi", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/xml")
    root = lxml.etree.fromstring(response.data)
    assert root.tag == "resultset"
    documents = root.findall("document")
    # Only the valid pid should be present
    assert len(documents) == 1
    document = documents[0]
    packageid = document.find("packageid")
    assert packageid is not None
    assert packageid.text == "edi.521.1"
    title = document.find("title")
    assert title is not None
    assert title.text is not None and len(title.text) > 0

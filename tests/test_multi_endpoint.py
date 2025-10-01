
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

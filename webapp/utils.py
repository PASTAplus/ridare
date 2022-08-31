import daiquiri
import requests

logger = daiquiri.getLogger(__name__)


def requests_wrapper(url: str) -> bytes:
    r = requests.get(url)
    if r.ok:
        return r.content
    else:
        raise requests.exceptions.ConnectionError(r.reason)

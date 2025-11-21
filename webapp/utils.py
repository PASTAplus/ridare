import pathlib

import daiquiri
import lxml.etree
import lxml.objectify
import requests

import webapp
import webapp.markdown_cache
import webapp.exceptions

logger = daiquiri.getLogger(__name__)


def requests_wrapper(url: str) -> bytes:
    r = requests.get(url)
    if r.ok:
        return r.content
    else:
        raise requests.exceptions.ConnectionError(r.reason)


def get_etree_as_pretty_printed_xml(el: lxml.etree.Element) -> str:
    """etree to pretty printed XML"""
    # assert isinstance(el, lxml.etree._Element), f'Expected Element. Received {type(el)}'
    if hasattr(el, 'getroottree'):
        lxml.objectify.deannotate(el.getroottree(), cleanup_namespaces=True, xsi_nil=True)
    return lxml.etree.tostring(
        el, pretty_print=True, with_tail=False, xml_declaration=False
    ).decode('utf-8')


def first_str(el: lxml.etree.Element, text_xpath: str, default_val: bool = None) -> str:
    """Apply xpath and, if there is a match, assume that the match is a text node, and
    convert it to str.

    {text_xpath} is an xpath that returns a text node. E.g., `.//text()`.
    """
    res_el = first(el, text_xpath)
    if res_el is None:
        return default_val
    return str(res_el).strip()


def first(el: lxml.etree.Element, xpath: str) -> str:
    """Return the first match to the xpath if there was a match, else None. Can this be
    done directly in xpath 1.0?
    """
    # log.debug(f'first() xpath={xpath} ...')
    res_el = el.xpath(f'({xpath})[1]')
    try:
        el = res_el[0]
    except IndexError:
        el = None
    # log.debug(f'first() -> {el}')
    return el


def get_cache_path(pid: str, cache: str) -> str:
    """Return the cache file path for a given pid and cache directory."""
    from webapp.markdown_cache import safe_filename

    return str(pathlib.Path(cache, f"{safe_filename(pid)}.eml.xml"))


def download_eml_to_cache(pid: str, pasta_url: str, cache: str) -> str:
    """Download the raw EML XML for the given pid from pasta_url and write to cache_dir.
    Returns the path to the cached EML XML file as a string."""

    eml_url = f"{pasta_url}/metadata/eml/{'/'.join(pid.strip().split('.'))}"
    eml_bytes = requests_wrapper(eml_url)
    eml_path = get_cache_path(pid, cache)
    pathlib.Path(eml_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(eml_path).write_bytes(eml_bytes)
    return eml_path


def get_eml(pid: str, env: str) -> bytes:
    """
    Retrieve the raw EML XML for a given pid and environment.
    Checks cache first, fetches and caches if missing, then returns the XML bytes.
    Handles both real and mocked download_eml_to_cache.
    """
    # Determine pasta and cache from env
    if env.lower() in ("d", "dev", "development"):
        pasta = webapp.config.Config.PASTA_D
        cache = webapp.config.Config.CACHE_D
    elif env.lower() in ("s", "stage", "staging"):
        pasta = webapp.config.Config.PASTA_S
        cache = webapp.config.Config.CACHE_S
    elif env.lower() in ("p", "prod", "production"):
        pasta = webapp.config.Config.PASTA_P
        cache = webapp.config.Config.CACHE_P
    else:
        msg = f"Requested PASTA environment not supported: {env}"
        raise webapp.exceptions.PastaEnvironmentError(msg)

    from webapp.markdown_cache import safe_filename

    eml_path = pathlib.Path(cache, f"{safe_filename(pid)}.eml.xml")
    if eml_path.is_file():
        return eml_path.read_bytes()
    # If not cached, fetch and cache
    result = download_eml_to_cache(pid, pasta, cache)
    if isinstance(result, bytes):
        return result
    return pathlib.Path(result).read_bytes()

import daiquiri
import lxml.etree
import lxml.objectify
import requests

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

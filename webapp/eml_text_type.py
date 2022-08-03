"""Functions for handling EML TextType elements
"""

import pathlib
import textwrap

import daiquiri
import lxml.etree
import lxml.objectify
import markdown

log = daiquiri.getLogger(__name__)


THIS_PATH = pathlib.Path(__file__).parent.resolve()
XSL_PATH = THIS_PATH / '../docbook-xsl-1.79.2/html/docbook.xsl'

# Markdown extensions that are installed by default.
# These are modules in site-packages/markdown/extensions.
# Note that "extra" is a collection of extensions.
DEFAULT_MARKDOWN_EXTENSIONS = [
    'extra',
    'admonition',
    'codehilite',
    'legacy_attrs',
    'legacy_em',
    'meta',
    'nl2br',
    'sane_lists',
    'smarty',
    'toc',
    'wikilinks',
]


def text_to_html(text_type_el: lxml.etree.Element) -> [str]:
    """Return the contents of an EML TextType element or subtree as an HTML fragment"""
    html_list = []
    if text_type_el.text.strip():
        html_list.append(_text_to_html(text_type_el.text))
    for text_el in _find_immediate_children(text_type_el):
        # if text_el.text.strip():
        #     html_list.append(_text_to_html(text_el.text))
        if text_el.tag == 'markdown':
            html_list.append(_markdown_to_html(text_el))
        else:
            html_list.append(_docbook_to_html(text_el))
        if text_el.tail.strip():
            html_list.append(text_el.tail)
    return f'<div>{"</div><div>".join(html_list)}</div>'


def _text_to_html(text_str: str):
    """Plain text to HTML"""
    log.info(f'Processing as text:\n----\n{text_str}\n----\n')
    return f'<p>{text_str.strip()}</p>'


def _find_immediate_children(text_type_el: lxml.etree.Element) -> [lxml.etree.Element]:
    """Return the immediate children of an EML TextType element"""
    return text_type_el.xpath(f'*')


def _markdown_to_html(markdown_el: lxml.etree.Element):
    markdown_str = markdown_el.xpath('text()')[0]
    dedent_markdown_str = textwrap.dedent(markdown_str)
    log.info(f'Processing as Markdown:\n----\n{dedent_markdown_str}\n----\n')
    return markdown.markdown(
        dedent_markdown_str, extensions=DEFAULT_MARKDOWN_EXTENSIONS
    )


def _docbook_to_html(
    docbook_el: lxml.etree.Element, xsl_path: pathlib.Path = XSL_PATH
) -> str:
    xml_str = get_etree_as_pretty_printed_xml(docbook_el)
    log.info(f'Processing as DocBook hierarchy:\n----\n{xml_str}\n----\n')
    xslt_el = lxml.etree.parse(xsl_path.as_posix())
    transform_func = lxml.etree.XSLT(xslt_el)
    html_el = transform_func(docbook_el)
    # return get_etree_as_pretty_printed_xml(html_el)
    return get_etree_as_pretty_printed_xml(html_el.xpath('/html/body/div')[0])


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


def get_etree_as_pretty_printed_xml(el: lxml.etree.Element) -> str:
    """etree to pretty printed XML"""
    # assert isinstance(el, lxml.etree._Element), f'Expected Element. Received {type(el)}'
    if hasattr(el, 'getroottree'):
        lxml.objectify.deannotate(
            el.getroottree(), cleanup_namespaces=True, xsi_nil=True
        )
    return lxml.etree.tostring(
        el, pretty_print=True, with_tail=False, xml_declaration=False
    ).decode('utf-8')

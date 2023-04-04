"""Functions for handling EML TextType elements
"""
import io
import pathlib
import textwrap

import daiquiri
import lxml.etree
import lxml.objectify
import markdown
import grip

import webapp.utils

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
    """Return the contents of an EML TextType element or subtree as an HTML fragment

    Returned fragment is on the form:

    <div>
        <div>Section of HTML formatted markdown, DocBook, plain text, etc</div>
        <div>...</div>
    </div>
    """
    html_list = []
    if text_type_el.text.strip():
        html_list.append(_text_to_html(text_type_el.text))

    text_type_el = fix_literal_layout(text_type_el)

    for text_el in _find_immediate_children(text_type_el):
        if text_el.tag == 'markdown':
            html_el = _markdown_to_html(text_el)
        else:
            html_el = _docbook_to_html(text_el)
        clean_html_el = clean_html(html_el)
        clean_html_str = webapp.utils.get_etree_as_pretty_printed_xml(clean_html_el)
        html_list.append(clean_html_str)
        if text_el.tail.strip():
            html_list.append(text_el.tail)

    return f'<div><div>{"</div><div>".join(html_list)}</div></div>'


def _text_to_html(text_str: str):
    """Plain text to HTML"""
    log.info(f'Processing as text:\n----\n{text_str}\n----\n')
    return f'<p>{text_str.strip()}</p>'


def _find_immediate_children(text_type_el: lxml.etree.Element) -> [lxml.etree.Element]:
    """Return the immediate children of an EML TextType element"""
    return text_type_el.xpath(f'*')


def _markdown_to_html(markdown_el: lxml.etree.Element, force_local: bool = False):
    """Return the contents of a markdown element as HTML.

    The EML spec specifies GitHub Flavored Markdown (gfm), and there are no local
    gfm processors for Python. So we send the markdown to GitHub for processing.

    Notes:
        - The markdown processor in the Python standard library can handle ALMOST all
          markdown that occurs in EML documents, so we might want to look into trying to
          detect if we need to send the markdown to GitHub.
        - GitHub has rate limiting on the markdown requests. The limit can be increased
          by connecting with an account instead of anonymously. We currently connect
          anonymously.
        - If GitHub markdown processing fails due to rate limiting or other issues, we
          fall back to processing the markdown locally with the standard Python markdown
          processor.
        - The standard Python markdown processor comes with many extensions, and we
          enable all of these in order to ensure support for as many markdown constructs
          as possible.
    """
    markdown_str = markdown_el.xpath('text()')[0]
    dedent_markdown_str = textwrap.dedent(markdown_str)
    log.info(f'Processing as Markdown:\n----\n{dedent_markdown_str}\n----\n')
    log.info(f'Connecting to GitHub for markdown rendering...')
    try:
        html_str = grip.render_content(dedent_markdown_str)
    except Exception as e:
        log.warn(f'GitHub markdown rendering failed with exception: {str(e)}')
        log.info(f'Using local markdown processor')
        html_str = markdown.markdown(dedent_markdown_str, extensions=DEFAULT_MARKDOWN_EXTENSIONS)
    return lxml.etree.HTML(html_str)

def _docbook_to_html(docbook_el: lxml.etree.Element, xsl_path: pathlib.Path = XSL_PATH) -> str:
    xml_str = webapp.utils.get_etree_as_pretty_printed_xml(docbook_el)
    log.info(f'Processing as DocBook hierarchy:\n----\n{xml_str}\n----\n')
    xslt_el = lxml.etree.parse(xsl_path.as_posix())
    transform_func = lxml.etree.XSLT(xslt_el)
    html_el = transform_func(docbook_el)
    return html_el.xpath('/html/body/*')[0]


def fix_literal_layout(xml_el):
    """Workaround 'literalLayout' bug in the EML spec.

    This renames any `literalLayout` elements to `literallayout` before processing with
    DocBook transforms.

    EML specifies 'literalLayout' as a valid DocBook element, but the name is actually
    literallayout (all lower case).
    """
    # language=xsl
    xsl_str = """\
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template match="@*|node()">
        <xsl:copy>
          <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
      </xsl:template>
      <xsl:template match="literalLayout">
        <literallayout>
          <xsl:apply-templates select="@*|node()"/>
        </literallayout>
      </xsl:template>
    </xsl:stylesheet>
    """
    # xml_str = get_etree_as_pretty_printed_xml(xml_el)
    # log.info(f'LiteralLayout:\n----\n{xml_str}\n----\n')
    xslt_el = lxml.etree.parse(io.StringIO(xsl_str))
    transform_func = lxml.etree.XSLT(xslt_el)
    transformed_xml_el = transform_func(xml_el)
    return transformed_xml_el


def clean_html(html_el):
    """A transform to clean up HTML. This removes:

    - All attributes (including "class")

    To remove other elements, add them in the final template match. E.g., to remove "a"
    anchors: <xsl:template match="@*|a"/>
    """
    # language=xsl
    xsl_str = """\
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
      <xsl:template match="@*|node()">
        <xsl:copy>
          <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
      </xsl:template>
      <xsl:template match="@*[local-name() != 'href']"/>
    </xsl:stylesheet>
    """
    xslt_el = lxml.etree.parse(io.StringIO(xsl_str))
    transform_func = lxml.etree.XSLT(xslt_el)
    transformed_xml_el = transform_func(html_el)
    return transformed_xml_el

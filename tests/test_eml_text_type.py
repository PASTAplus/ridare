"""Test the eml_text_type.py module
"""

import lxml.etree
import lxml.html
import markdown

import webapp.eml_text_type as eml_text_type
import tests.util.sample as sample


def test_markdown_table(markdown_table_md: str):
    markdown_html_str = markdown.markdown(
        markdown_table_md, extensions=eml_text_type.DEFAULT_MARKDOWN_EXTENSIONS
    )
    sample.assert_match(markdown_html_str, 'table', '.html')


def test_find_immediate_children(complete_eml: lxml.etree.Element):
    text_el = complete_eml.xpath('.//funding')
    text_el_list = eml_text_type._find_immediate_children(text_el[0])
    assert len(text_el_list) == 4
    tag_list = [e.tag for e in text_el_list]
    assert tag_list == ['markdown', 'markdown', 'section', 'section']


def test_markdown_to_html(complete_eml: lxml.etree.Element):
    markdown_el = complete_eml.xpath('.//funding//markdown[1]')[0]
    html_str = eml_text_type._markdown_to_html(markdown_el)
    sample.assert_match(html_str, 'markdown_html', '.html')


def test_text_to_html(complete_eml: lxml.etree.Element):
    text_el = complete_eml.xpath('.//funding')[0]
    text_html_str = eml_text_type.text_to_html(text_el)
    sample.assert_match(text_html_str, 'text_html', '.html')


def test_docbook_to_html_simple(docbook_xml):
    html_str = eml_text_type._docbook_to_html(docbook_xml)
    assert '<div class="article">' in html_str


def test_docbook_to_html_complete(complete_eml: lxml.etree.Element):
    docbook_el = complete_eml.xpath('.//funding/*[3]')[0]
    docbook_html_str = eml_text_type._docbook_to_html(docbook_el)
    sample.assert_match(docbook_html_str, 'docbook', '.html')


def test_docbook_to_html_complex(eml_with_complex_docbook: lxml.etree.Element):
    docbook_el = eml_with_complex_docbook.xpath('.//dataset/abstract/section')[2]
    docbook_html_str = eml_text_type._docbook_to_html(docbook_el)
    sample.assert_match(docbook_html_str, 'docbook_complex', '.html')


def test_text_to_html_2(docbook_and_markdown: lxml.etree.Element):
    text_type_el = docbook_and_markdown.xpath('/sample/texttype')[0]
    docbook_and_markdown_html_str = eml_text_type.text_to_html(text_type_el)
    sample.assert_match(docbook_and_markdown_html_str, 'docbook_and_markdown', '.html')

"""Test the eml_text_type.py module
"""

import lxml.etree
import lxml.html
import markdown

import webapp.eml_text_type as eml_text_type


def test_markdown_table(markdown_table_md: str, markdown_table_html: str):
    markdown_html = markdown.markdown(
        markdown_table_md, extensions=eml_text_type.DEFAULT_MARKDOWN_EXTENSIONS
    )
    assert markdown_html.strip() == markdown_table_html.strip()


def test_find_immediate_children(complete_eml: lxml.etree.Element):
    text_el = complete_eml.xpath('.//funding')
    text_el_list = eml_text_type._find_immediate_children(text_el[0])
    assert len(text_el_list) == 4
    tag_list = [e.tag for e in text_el_list]
    assert tag_list == ['markdown', 'markdown', 'section', 'section']


def test_markdown_to_html(complete_eml: lxml.etree.Element):
    markdown_el = complete_eml.xpath('.//funding//markdown[1]')[0]
    html_str = eml_text_type._markdown_to_html(markdown_el)
    assert html_str == '<p>markdown0</p>'


def test_text_to_html(complete_eml: lxml.etree.Element):
    text_el = complete_eml.xpath('.//funding')[0]
    html_str = eml_text_type.text_to_html(text_el)
    # print('--------------------------------------')
    # print(html_str)
    # assert html_str == '<p>markdown0</p>'


def test_docbook_to_html_simple(docbook_xml):
    html_str = eml_text_type._docbook_to_html(docbook_xml)
    assert '<div class="article">' in html_str


def test_docbook_to_html_complete(complete_eml: lxml.etree.Element):
    docbook_el = complete_eml.xpath('.//funding/*[3]')[0]
    html_str = eml_text_type._docbook_to_html(docbook_el)
    assert html_str.startswith(
        '<div lang="lang82" class="section"><div class="titlepage"><hr/></div>'
    )


def test_docbook_to_html_complex(eml_with_complex_docbook: lxml.etree.Element):
    docbook_el = eml_with_complex_docbook.xpath('.//dataset/abstract/section')[2]
    html_str = eml_text_type._docbook_to_html(docbook_el)
    assert html_str.startswith(
        '<div class="section"><div class="titlepage"><div><div><h2 class="title" style="clear: both">'
    )


# def test_text_to_html(eml_with_complex_docbook: lxml.etree.Element):
#     markdown_el = eml_with_complex_docbook.xpath('.//funding')
#     html_str = eml_text_type._markdown_to_html(markdown_el)
# docbook_el = eml_with_complex_docbook.xpath('.//dataset/abstract')[0]
# html_str = eml_text_type.text_to_html(docbook_el)
# print(html_str)


def test_text_to_html_2(docbook_and_markdown: lxml.etree.Element):
    texttype_el = docbook_and_markdown.xpath('/sample/texttype')[0]
    html_str = eml_text_type.text_to_html(texttype_el)
    # print('----------------------------')
    # print(html_str)

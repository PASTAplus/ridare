#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib

import daiquiri
import lxml.etree
import markdown

import webapp.config
import webapp.exceptions
import webapp.utils

logger = daiquiri.getLogger(__name__)

EML_XPATH_DICT = {
    'abstract': './/dataset/abstract/markdown/text()',
    'description': './/dataset/methods/methodStep/description/markdown/text()',
    'related_abstract': './/dataset/project/relatedProject/abstract/markdown/text()',
    'related_funding': './/dataset/project/relatedProject/funding/markdown/text()',
}


def get_html(
    pid: str,
    element_str: str,
    env: str,
):
    """Get HTML fragment for markdown element in EML"""
    if env.lower() in ("d", "dev", "development"):
        pasta = webapp.config.Config.PASTA_D
        cache = webapp.config.Config.CACHE_D
        env = webapp.config.Config.ENV_D
    elif env.lower() in ("s", "stage", "staging"):
        pasta = webapp.config.Config.PASTA_S
        cache = webapp.config.Config.CACHE_S
        env = webapp.config.Config.ENV_S
    elif env.lower() in ("p", "prod", "production"):
        pasta = webapp.config.Config.PASTA_P
        cache = webapp.config.Config.CACHE_P
        env = webapp.config.Config.ENV_P
    else:
        msg = f"Requested PASTA environment not supported: {env}"
        raise webapp.exceptions.PastaEnvironmentError(msg)

    file_path = pathlib.Path(cache, f'{element_str}-{pid}.html')

    if file_path.is_file():
        return file_path.read_text(encoding='utf-8')

    scope, identifier, revision = pid.strip().split(".")
    eml_url = f"{pasta}/metadata/eml/{scope}/{identifier}/{revision}"

    try:
        eml = webapp.utils.requests_wrapper(eml_url)
    except ValueError as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.error(e)
        msg = f'Error accessing data package "{pid}" in the "' f'{env}" environment'
        raise webapp.exceptions.DataPackageError(msg)

    root_el = lxml.etree.fromstring(eml)
    markdown_xpath = EML_XPATH_DICT[element_str]
    markdown_str = first_str(root_el, markdown_xpath)

    if markdown_str is None:
        raise webapp.exceptions.DataPackageError(
            f'Unable to extract metadata. markdown_xpath="{markdown_xpath}"'
        )

    html_str = markdown.markdown(markdown_str)

    file_path.write_text(html_str, encoding='utf-8')

    return html_str


def first_str(el, text_xpath, default_val=None):
    """Apply xpath and, if there is a match, assume that the match is a text node, and
    convert it to str.

    {text_xpath} is an xpath that returns a text node. E.g., `.//text()`.
    """
    res_el = first(el, text_xpath)
    if res_el is None:
        return default_val
    return str(res_el).strip()


def first(el, xpath):
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

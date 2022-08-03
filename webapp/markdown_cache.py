#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import pathlib

import daiquiri
import lxml.etree
import markdown

import webapp.config
import webapp.exceptions
import webapp.utils

import webapp.eml_text_type

log = daiquiri.getLogger(__name__)

# EML_XPATH_DICT = {
#    'abstract': '[.//]dataset/abstract/text()',
#     'description': './/dataset/methods/methodStep/description/markdown/text()',
#     'related_abstract': './/dataset/project/relatedProject/abstract/markdown/text()',
#     'related_funding': './/dataset/project/relatedProject/funding/markdown/text()',
# }

TEXT_XPATH_DICT = {
    'abstract': './/dataset/abstract',
    'description': './/dataset/methods/methodStep/description',
    'related_abstract': './/dataset/project/relatedProject/abstract',
    'related_funding': './/dataset/project/relatedProject/funding',
    'intellectualRights': './/dataset/project/relatedProject/funding',
}

THIS_PATH = pathlib.Path(__file__).parent.resolve()


# Disable using the cache for easier debugging.
USE_CACHE = False


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
    file_path.parent.mkdir(parents=False, exist_ok=True)

    if USE_CACHE and file_path.is_file():
        return file_path.read_text(encoding='utf-8')

    scope, identifier, revision = pid.strip().split(".")
    eml_url = f"{pasta}/metadata/eml/{scope}/{identifier}/{revision}"

    try:
        eml = webapp.utils.requests_wrapper(eml_url)
    except ValueError as e:
        log.error(e)
        raise
    except Exception as e:
        log.error(e)
        msg = f'Error accessing data package "{pid}" in the "' f'{env}" environment'
        raise webapp.exceptions.DataPackageError(msg)

    root_el = lxml.etree.fromstring(eml)
    text_xpath = TEXT_XPATH_DICT[element_str]

    text_el_list = root_el.xpath(text_xpath)
    if not text_el_list:
        raise webapp.exceptions.DataPackageError(
            f'Unable to extract text. text_xpath="{text_xpath}"'
        )

    if len(text_el_list) > 1:
        raise webapp.exceptions.DataPackageError(
            f'There are more than 1 matches. text_xpath="{text_xpath}" len="{len(text_el_list)}"'
        )

    html_str = eml_text_type.text_to_html(text_el_list[0])

    file_path.write_text(html_str, encoding='utf-8')

    return html_str

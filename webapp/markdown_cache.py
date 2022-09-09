import pathlib
import re

import daiquiri
import lxml.etree

import webapp.config
import webapp.eml_text_type
import webapp.exceptions
import webapp.utils

log = daiquiri.getLogger(__name__)

# Disable using the cache for easier debugging.
USE_CACHE = False


def get_html(
    pid: str,
    text_xpath: str,
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

    file_path = pathlib.Path(cache, f'{safe_filename(text_xpath)}-{safe_filename(pid)}.html')
    file_path.parent.mkdir(parents=False, exist_ok=True)

    if USE_CACHE and file_path.is_file():
        return file_path.read_text(encoding='utf-8')

    scope, identifier, revision = pid.strip().split(".")
    eml_url = f"{pasta}/metadata/eml/{scope}/{identifier}/{revision}"

    try:
        eml_bytes = webapp.utils.requests_wrapper(eml_url)
    except ValueError as e:
        log.error(e)
        raise
    except Exception as e:
        log.error(e)
        msg = f'Error accessing data package "{pid}" in the "' f'{env}" environment'
        raise webapp.exceptions.DataPackageError(msg)

    eml_path = pathlib.Path(cache, f'{safe_filename(pid)}.eml.xml')
    eml_path.write_bytes(eml_bytes)

    root_el = lxml.etree.fromstring(eml_bytes)

    text_el_list = root_el.xpath(text_xpath)
    if not text_el_list:
        raise webapp.exceptions.DataPackageError(f'Element not found. text_xpath="{text_xpath}"')

    if len(text_el_list) > 1:
        raise webapp.exceptions.DataPackageError(
            f'There is more than one matching element. text_xpath="{text_xpath}" len="{len(text_el_list)}"'
        )

    html_str = webapp.eml_text_type.text_to_html(text_el_list[0])

    file_path.write_text(html_str, encoding='utf-8')

    return html_str


def safe_filename(text_xpath):
    return re.sub(r'[^a-zA-Z0-9]', '_', text_xpath)

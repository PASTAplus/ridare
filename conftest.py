"""Unit tests using pytest and pytest-flask

https://pytest-flask.readthedocs.io/en/latest/
"""

import logging
import os
import pathlib
import sys
import tempfile
import types

import tests.util.sample

# import pandas as pd
import pytest

# import flask.testing
# flask.testing is used indirectly in a fixture, which PyCharm can't see. This adds
# a no-op usage, that PyCharm can see.
# x=flask.testing

import lxml.etree

import webapp.run


logging.getLogger('matplotlib').setLevel(logging.ERROR)

PROJ_ROOT = pathlib.Path(__file__).parent.resolve()
TEST_DOCS = PROJ_ROOT / 'tests/test_docs'


# Hooks


def pytest_addoption(parser):
    parser.addoption(
        '--sample-error',
        dest='sample_error',
        action='store_true',
        default=False,
        help='Handle sample mismatch as test failure instead of opening diff viewer',
    )
    parser.addoption(
        '--sample-update',
        dest='sample_update',
        action='store_true',
        default=False,
        help='Update mismatched samples instead of opening diff viewer',
    )


# @pytest.fixture(autouse=True)
# def sample_options(request):
#     return types.SimpleNamespace(
#         error=request.config.getoption("--sample-error"),
#         update=request.config.getoption("--sample-update"),
#     )


def pytest_configure(config):
    """Allow plugins and conftest files to perform initial configuration

    This hook is called for every plugin and initial conftest file after command line
    options have been parsed.

    After that, the hook is called for other conftest files as they are imported.
    """
    sys.is_running_under_travis = "TRAVIS" in os.environ
    sys.is_running_under_pytest = True

    tests.util.sample.options = types.SimpleNamespace(
        error=config.getoption("--sample-error"),
        update=config.getoption("--sample-update"),
    )

    # Only accept error messages from loggers that are noisy at debug.
    logging.getLogger('django.db.backends.schema').setLevel(logging.ERROR)




# Implicit fixtures (autouse = True)


@pytest.fixture(scope='function', autouse=True)
def expose_errors(config):
    """Disable automatic error handling during request."""
    config['TESTING'] = True


# Flask fixtures


@pytest.fixture
def app():
    return webapp.run.app


# Test files


@pytest.fixture
def tmpdir(config, tmpdir):
    return pathlib.Path(tmpdir)


@pytest.fixture
def docs_path():
    return TEST_DOCS


@pytest.fixture
def complete_eml():
    """A complete sample EML doc, returned in the lxml.etree domain.

    Generated from the EML 2.2.0 XML Schema with Oxygen, limited to a depth of 20
    levels. Then hand edited to add sample text and schemaLocations.
    """
    eml_path = TEST_DOCS / 'complete_eml.xml'
    return lxml.etree.parse(eml_path.as_posix())


@pytest.fixture
def docbook_xml():
    """A sample DocBook doc, returned in the lxml.etree domain."""
    xml_path = TEST_DOCS / 'docbook.xml'
    return lxml.etree.parse(xml_path.as_posix())


@pytest.fixture
def docbook_html():
    """A DocBook doc, transformed to HTML, returned as a str."""
    return (TEST_DOCS / 'docbook.html').read_text()


@pytest.fixture
def eml_with_complex_docbook():
    """A EML doc with extensive DocBook structures, returned in the
    lxml.etree domain.

    Found with:
    $ cd dex-data/___data
    $ rg -c '<section' | sort -nk2 -t:
    """
    eml_path = TEST_DOCS / 'knb-lter-cap.661.2.eml.xml'
    return lxml.etree.parse(eml_path.as_posix())


@pytest.fixture
def docbook_and_markdown():
    """A that contains a mix of DocBook and markdown elements."""
    xml_path = TEST_DOCS / 'docbook_and_markdown.xml'
    return lxml.etree.parse(xml_path.as_posix())


@pytest.fixture
def markdown_table_md():
    """A str that contains a simple markdown table"""
    return (TEST_DOCS / 'markdown_table.md').read_text()


@pytest.fixture
def markdown_table_html():
    """A str that contains a simple markdown table as HTML"""
    return (TEST_DOCS / 'markdown_table.html').read_text()

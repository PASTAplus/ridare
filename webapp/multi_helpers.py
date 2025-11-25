"""Helper functions for handling multi-query requests in the webapp."""

import logging
import re

import flask
from flask import request, jsonify
import lxml.etree
from webapp.utils import get_eml
import webapp.config
from webapp.exceptions import DataPackageError, PastaEnvironmentError


logger = logging.getLogger(__name__)

# pylint: disable=c-extension-no-member


def validate_env(env: str) -> None:
    """Raise PastaEnvironmentError if env is not valid."""
    valid_envs = {
        webapp.config.Config.ENV_P,
        webapp.config.Config.ENV_S,
        webapp.config.Config.ENV_D,
    }
    if env not in valid_envs:
        raise PastaEnvironmentError(
            f"Requested PASTA environment '{env}' does not exist."
        )


def parse_json_request() -> dict:
    """Parse and validate the incoming JSON request body."""
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logger.exception("Failed to parse JSON request: %s", str(e))
        raise ValueError("Invalid request format: POST body must be valid JSON.") from e
    return data


def validate_payload(data: dict) -> tuple[list[str], list[str | dict[str, str]]]:
    """Validate and extract pids and queries from the request payload."""
    pids = data.get("pid")
    queries = data.get("query")
    if not isinstance(pids, list) or not isinstance(queries, list):
        raise ValueError(
            "Invalid request format: 'query' must be a list of XPath strings or key-value pairs."
        )
    if not pids or any(not pid for pid in pids):
        raise DataPackageError("One or more data package IDs are missing or invalid.")
    return pids, queries


def is_valid_xml_tag(tag: str) -> bool:
    """Check if a string is a valid XML tag name."""
    return re.match(r"^[A-Za-z_][\w\-\.]*$", tag) is not None


def run_xpath_query(root: lxml.etree._Element, xpath: str) -> list:
    """Run an XPath query on the XML root, logging and returning an empty list on error."""
    try:
        return root.xpath(xpath)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Failed to retrieve or parse XPath '%s': %s", xpath, str(e))
        return []


def wrap_query_result(key: str, values: list) -> lxml.etree._Element:
    """Wrap XPath results in an XML element with the given key as tag name."""
    wrapper = lxml.etree.Element(key)
    for v in values:
        if isinstance(v, lxml.etree._Element):  # pylint: disable=protected-access
            wrapper.append(v)
        else:
            value_el = lxml.etree.Element("value")
            value_el.text = str(v)
            wrapper.append(value_el)
    return wrapper


def build_multi_results(
    pids: list[str],
    queries: list[str | dict[str, str]],
    env: str,
) -> dict[str, list[lxml.etree._Element | str]]:
    """
    Run XPath queries on multiple EML documents and return results as a dict.
    Each PID is processed independently. For each query:
      - If a string, run as a simple XPath.
      - If a dict, use key as wrapper tag and value as XPath.
    Results are collected per PID.
    """
    results: dict[str, list[lxml.etree._Element | str]] = {}
    for pid in pids:
        try:
            eml_bytes: bytes = get_eml(pid, env)
            root: lxml.etree._Element = lxml.etree.fromstring(eml_bytes)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Failed to retrieve or parse EML for PID %s: %s", pid, str(e))
            continue
        pid_results: list[lxml.etree._Element | str] = []
        for item in queries:
            if isinstance(item, str):
                # Simple XPath string
                values = run_xpath_query(root, item)
                pid_results.extend(values)
            elif isinstance(item, dict) and len(item) == 1:
                key, xpath = next(iter(item.items()))
                if not is_valid_xml_tag(key):
                    # Skip invalid tag names
                    continue
                values = run_xpath_query(root, xpath)
                if not values:
                    # Skip if no nodes found
                    continue
                wrapper = wrap_query_result(key, values)
                pid_results.append(wrapper)
        results[pid] = pid_results
    return results

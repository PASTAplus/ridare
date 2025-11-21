#!/usr/bin/env python
"""Ridare webapp Flask application: routes, multi-endpoint, and EML query logic."""

import logging
import os
import re

import daiquiri
import flask
import lxml.etree
from flask import request, jsonify
from flask_cors import CORS

import webapp.markdown_cache
import webapp.config
import webapp.utils
from webapp.utils import get_eml
import webapp.exceptions
from webapp.exceptions import DataPackageError, PastaEnvironmentError

cwd = os.path.dirname(os.path.realpath(__file__))
logfile = cwd + "/run.log"
daiquiri.setup(level=logging.INFO, outputs=(daiquiri.output.File(logfile), "stderr"))
logger = daiquiri.getLogger("run.py: " + __name__)

app = flask.Flask(__name__)
CORS(app)
app.config.from_object(webapp.config.Config)

@app.route("/")
@app.route("/help")
def help():
    redirect_url = webapp.config.Config.HELP_URL
    return flask.redirect(redirect_url, 301)


@app.route("/raw/<path:pid_xpath>", strict_slashes=False, merge_slashes=False)
def raw(pid_xpath):
    if '/' not in pid_xpath:
        flask.abort(404)

    pid_str, text_xpath = pid_xpath.split("/", 1)

    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV

    try:
        xml_str = webapp.markdown_cache.get_raw(pid_str, text_xpath, env)
        response = flask.make_response(xml_str)
        response.headers["Content-Type"] = f"application/xml; charset=utf-8"
        return response
    except Exception as e:
        logger.exception(
            f'Exception when handling request. element="{text_xpath}" pid="{pid_str}"'
        )
        flask.abort(400, description=e)

@app.route("/<path:pid_xpath>", strict_slashes=False, merge_slashes=False)
def markdown(pid_xpath):
    if '/' not in pid_xpath:
        flask.abort(404)

    pid_str, text_xpath = pid_xpath.split("/", 1)

    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV

    try:
        markdown_str = webapp.markdown_cache.get_html(pid_str, text_xpath, env)
        response = flask.make_response(markdown_str)
        response.headers["Content-Type"] = f"text/html; charset=utf-8"
        return response
    except Exception as e:
        logger.exception(
            f'Exception when handling request. element="{text_xpath}" pid="{pid_str}"'
        )
        flask.abort(400, description=e)

def is_valid_xml_tag(tag: str) -> bool:
    """Check if a string is a valid XML tag name."""
    return re.match(r"^[A-Za-z_][\w\-\.]*$", tag) is not None


def run_xpath_query(root: lxml.etree._Element, xpath: str) -> list:
    """Run an XPath query on the XML root, logging and returning an empty list on error."""
    try:
        return root.xpath(xpath)
    except Exception as e:
        logger.exception(f"Failed to retrieve or parse XPath '{xpath}': {str(e)}")
        return []


def wrap_query_result(key: str, values: list) -> lxml.etree._Element:
    """Wrap XPath results in an XML element with the given key as tag name."""
    wrapper = lxml.etree.Element(key)
    for v in values:
        if isinstance(v, lxml.etree._Element):
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
        except Exception as e:
            logger.exception(f"Failed to retrieve or parse EML for PID {pid}: {str(e)}")
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


@app.route("/multi", methods=["POST"])
def multi():
    """Process multiple EML documents and run user-specified XPath queries."""
    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV
    try:
        valid_envs = {webapp.config.Config.ENV_P, webapp.config.Config.ENV_S, webapp.config.Config.ENV_D}
        if env not in valid_envs:
            raise PastaEnvironmentError(f"Requested PASTA environment '{env}' does not exist.")
    except PastaEnvironmentError as e:
        logger.exception(f"PastaEnvironmentError in /multi endpoint: {str(e)}")
        return jsonify({"error": f"PASTA environment error: {str(e)}"}), 400

    try:
        data = request.get_json(force=True)
    except Exception as e:
        logger.exception(f"Failed to parse JSON request: {str(e)}")
        return (
            jsonify({"error": "Invalid request format: POST body must be valid JSON."}),
            400,
        )
    try:
        pids = data.get("pid")
        queries = data.get("query")
        if not isinstance(pids, list) or not isinstance(queries, list):
            return (
                jsonify(
                    {
                        "error": "Invalid request format: 'query' must be a list of XPath "
                        "strings or key-value pairs."
                    }
                ),
                400,
            )
        if not pids or any(not pid for pid in pids):
            raise DataPackageError("One or more data package IDs are missing or invalid.")
        results = build_multi_results(pids, queries, env)
        resultset_el = lxml.etree.Element("resultset")
        for pid, pid_results in results.items():
            document_el = lxml.etree.SubElement(resultset_el, "document")
            packageid_el = lxml.etree.SubElement(document_el, "packageid")
            packageid_el.text = pid
            if isinstance(pid_results, list):
                for v in pid_results:
                    if isinstance(v, lxml.etree._Element):
                        document_el.append(v)
                    else:
                        value_el = lxml.etree.SubElement(document_el, "value")
                        value_el.text = str(v)
        xml_str = lxml.etree.tostring(
            resultset_el, pretty_print=True, encoding="utf-8", xml_declaration=True
        )
        response = flask.make_response(xml_str)
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        return response
    except DataPackageError as e:
        logger.exception(f"DataPackageError in /multi endpoint: {str(e)}")
        return jsonify({"error": f"Data package error: {str(e)}"}), 400
    except Exception as e:
        logger.exception(f"Exception in /multi endpoint: {str(e)}")
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 400



if __name__ == "__main__":
    app.run()

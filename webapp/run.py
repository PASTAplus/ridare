#!/usr/bin/env python
"""Ridare webapp Flask application: routes, multi-endpoint, and EML query logic."""

import logging
import os

import daiquiri
import flask
from flask import request, jsonify
from flask_cors import CORS
import lxml.etree

import webapp.markdown_cache
import webapp.config
import webapp.utils
from webapp.utils import get_eml
import webapp.exceptions
from webapp.exceptions import DataPackageError, PastaEnvironmentError
from webapp.multi_helpers import (
    validate_env, parse_json_request, validate_payload, error_response,
    build_multi_results
)

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

@app.route("/multi", methods=["POST"])
def multi() -> flask.Response:
    """Process multiple EML documents and run user-specified XPath queries."""
    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV
    try:
        # Step 1: Validate environment
        validate_env(env)
    except PastaEnvironmentError as e:
        logger.exception(f"PastaEnvironmentError in /multi endpoint: {str(e)}")
        return error_response(f"PASTA environment error: {str(e)}")
    try:
        # Step 2: Parse and validate request body
        data = parse_json_request()
        pids, queries = validate_payload(data)
    except DataPackageError as e:
        logger.exception(f"DataPackageError in /multi endpoint: {str(e)}")
        return error_response(f"Data package error: {str(e)}")
    except ValueError as e:
        logger.exception(f"Invalid request in /multi endpoint: {str(e)}")
        return error_response(str(e))
    try:
        # Step 3: Build results and construct XML response
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
    except Exception as e:
        logger.exception(f"Exception in /multi endpoint: {str(e)}")
        return error_response(f"Failed to process query: {str(e)}")


if __name__ == "__main__":
    app.run()

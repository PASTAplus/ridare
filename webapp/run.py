#!/usr/bin/env python

import logging
import os

import daiquiri
import flask
import lxml.etree
from flask import request, jsonify
from lxml import etree

import webapp.markdown_cache
import webapp.config
import webapp.utils
import webapp.exceptions

cwd = os.path.dirname(os.path.realpath(__file__))
logfile = cwd + "/run.log"
daiquiri.setup(level=logging.INFO, outputs=(daiquiri.output.File(logfile), "stderr"))
logger = daiquiri.getLogger("run.py: " + __name__)

app = flask.Flask(__name__)
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

def build_multi_results(pids, queries, env):
    """Run XPath queries on multiple EML documents and return results as a dict."""
    from webapp.utils import get_eml
    results = {}
    for pid in pids:
        try:
            eml_bytes = get_eml(pid, env)
            root = lxml.etree.fromstring(eml_bytes)
            tree = lxml.etree.ElementTree(root)
        except Exception:
            continue
        pid_results = []
        for xpath in queries:
            try:
                values = tree.xpath(xpath)
                pid_results.extend(values)
            except Exception:
                continue
        results[pid] = pid_results
    return results

@app.route("/multi", methods=["POST"])
def multi():
    """Process multiple EML documents and run user-specified XPath queries."""
    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid request format: POST body must be valid JSON."}), 400
    pids = data.get("pid")
    queries = data.get("query")
    if not isinstance(pids, list) or not isinstance(queries, list):
        return jsonify({"error": "Invalid request format: 'query' must be a list of XPath strings."}), 400
    results = build_multi_results(pids, queries, env)
    resultset_el = etree.Element("resultset")
    for pid, pid_results in results.items():
        document_el = etree.SubElement(resultset_el, "document")
        packageid_el = etree.SubElement(document_el, "packageid")
        packageid_el.text = pid
        if isinstance(pid_results, list):
            for v in pid_results:
                if isinstance(v, lxml.etree._Element):
                    document_el.append(v)
                else:
                    value_el = etree.SubElement(document_el, "value")
                    value_el.text = str(v)
    xml_str = etree.tostring(resultset_el, pretty_print=True, encoding="utf-8", xml_declaration=True)
    response = flask.make_response(xml_str)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


if __name__ == "__main__":
    app.run()

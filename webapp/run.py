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
    import re
    def is_valid_xml_tag(tag):
        # XML tag name must start with a letter or underscore, followed by letters, digits, hyphens, underscores, or periods
        return re.match(r'^[A-Za-z_][\w\-\.]*$', tag) is not None
    results = {}
    for pid in pids:
        try:
            eml_bytes = get_eml(pid, env)
            root = lxml.etree.fromstring(eml_bytes)
            # tree = lxml.etree.ElementTree(root)  # Not needed for XPath
        except Exception:
            continue
        pid_results = []
        for item in queries:
            if isinstance(item, str):
                # Simple XPath string
                try:
                    values = root.xpath(item)
                    pid_results.extend(values)
                except Exception:
                    continue
            elif isinstance(item, dict) and len(item) == 1:
                key, xpath = next(iter(item.items()))
                if not is_valid_xml_tag(key):
                    continue  # Skip invalid tag names
                try:
                    values = root.xpath(xpath)
                except Exception:
                    continue
                if not values:
                    continue  # Skip if no nodes found
                wrapper = lxml.etree.Element(key)
                for v in values:
                    # If v is an Element, append directly; if not, create a text node
                    if isinstance(v, lxml.etree._Element):
                        wrapper.append(v)
                    else:
                        value_el = lxml.etree.Element("value")
                        value_el.text = str(v)
                        wrapper.append(value_el)
                pid_results.append(wrapper)
        results[pid] = pid_results
    return results

@app.route("/multi", methods=["POST"])
def multi():
    """Process multiple EML documents and run user-specified XPath queries."""
    env = flask.request.args.get("env") or webapp.config.Config.DEFAULT_ENV
    try:
        data = request.get_json(force=True)
        pids = data.get("pid")
        queries = data.get("query")
        if not isinstance(pids, list) or not isinstance(queries, list):
            return jsonify({"error": "Invalid request format: 'query' must be a list of XPath strings or key-value pairs."}), 400
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
    except Exception as e:
        # Log the error and return a 400 response with details
        logger.exception(f"Exception in /multi endpoint: {str(e)}")
        return jsonify({"error": f"Failed to process query: {str(e)}"}), 400


if __name__ == "__main__":
    app.run()

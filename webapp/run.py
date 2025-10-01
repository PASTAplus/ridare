#!/usr/bin/env python

import logging
import os

import daiquiri
import flask

import webapp.markdown_cache
import webapp.config

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

@app.route("/multi", methods=["POST"])
def multi():
    """Process multiple EML documents and run user-specified XPath queries."""
    import lxml.etree
    import os
    from flask import request, jsonify
    from lxml import etree

    data = request.get_json(force=True)
    pids = data.get("pid")
    queries = data.get("query")
    if not isinstance(pids, list) or not isinstance(queries, dict):
        return jsonify({"error": "Invalid request format"}), 400

    results = {}
    for pid in pids:
        pid_filename = pid.replace('.', '_')
        xml_path = os.path.join(cwd, "../cache/production", f"{pid_filename}.eml.xml")
        if not os.path.exists(xml_path):
            results[pid] = {"error": f"File not found: {xml_path}"}
            continue
        try:
            tree = lxml.etree.parse(xml_path)
        except Exception as e:
            results[pid] = {"error": f"XML parse error: {str(e)}"}
            continue
        pid_results = {}
        for key, xpath in queries.items():
            try:
                values = tree.xpath(xpath)
                # Store lxml elements and primitives as-is
                pid_results[key] = values
            except Exception as e:
                pid_results[key] = f"XPath error: {str(e)}"
        results[pid] = pid_results

    results_el = etree.Element("results")
    for pid, pid_results in results.items():
        package_el = etree.SubElement(results_el, "package", id=pid)
        if isinstance(pid_results, dict):
            for key, value in pid_results.items():
                if key == "error":
                    error_el = etree.SubElement(package_el, "error")
                    error_el.text = value
                elif isinstance(value, list):
                    parent_el = etree.SubElement(package_el, key)
                    child_tag = key[:-1] if key.endswith('s') else 'item'
                    for v in value:
                        if isinstance(v, lxml.etree._Element):
                            parent_el.append(v)
                        else:
                            child_el = etree.SubElement(parent_el, child_tag)
                            child_el.text = str(v)
                else:
                    key_el = etree.SubElement(package_el, key)
                    key_el.text = str(value)
        else:
            error_el = etree.SubElement(package_el, "error")
            error_el.text = str(pid_results)
    xml_str = etree.tostring(results_el, pretty_print=True, encoding="utf-8", xml_declaration=True)
    response = flask.make_response(xml_str)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


if __name__ == "__main__":
    app.run()

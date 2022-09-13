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


if __name__ == "__main__":
    app.run()

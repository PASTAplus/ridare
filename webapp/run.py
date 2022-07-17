#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


@app.route("/markdown")
@app.route("/markdown/help")
def help():
    redirect_url = webapp.config.Config.HELP_URL
    return flask.redirect(redirect_url, 301)


@app.route("/markdown/<element_str>/<pid>")
def markdown(element_str, pid=None):
    env = flask.request.args.get("env")
    if env is None:
        env = webapp.config.Config.DEFAULT_ENV

    try:
        markdown_str = webapp.markdown_cache.get_html(pid, element_str, env)
        response = flask.make_response(markdown_str)
        response.headers["Content-Type"] = f"text/html; charset=utf-8"
        return response
    except Exception as e:
        logger.error(e)
        flask.abort(400, description=e)


if __name__ == "__main__":
    app.run()

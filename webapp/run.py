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


@app.route("/")
@app.route("/help")
def help():
    redirect_url = webapp.config.Config.HELP_URL
    return flask.redirect(redirect_url, 301)


@app.route("/<pid>/<element_str>")
def markdown(pid_str, element_str):
    env = flask.request.args.get("env")
    if env is None:
        env = webapp.config.Config.DEFAULT_ENV

    try:
        markdown_str = webapp.markdown_cache.get_html(pid_str, element_str, env)
        response = flask.make_response(markdown_str)
        response.headers["Content-Type"] = f"text/html; charset=utf-8"
        return response
    except Exception as e:
        logger.exception(
            f'Exception when handling request. element="{element_str}" pid="{pid_str}"'
        )
        flask.abort(400, description=e)


if __name__ == "__main__":
    app.run()

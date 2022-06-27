#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: run

:Synopsis:
 
:Author:
    servilla

:Created:
    6/26/2022
"""
import daiquiri
from flask import abort, Flask, request, send_file
import requests

from webapp.config import Config


logger = daiquiri.getLogger('run.py: ' + __name__)

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/ridare')
def hello_world():
    return 'Hello on Wheels!'


if __name__ == '__main__':
    app.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: config

:Synopsis:

:Author:
    servilla

:Created:
    6/26/2022
"""

class Config(object):

    # Flask app configuration
    SECRET_KEY = 'SECRET KEY'
    DEBUG = False

    # Webapp configuration
    CACHE_P = 'cache location for production json files'
    CACHE_S = 'cache location for staging json files'
    CACHE_D = 'cache location for development json files'

    PASTA_P = 'https://pasta.lternet.edu/package'
    PASTA_S = 'https://pasta-s.lternet.edu/package'
    PASTA_D = 'https://pasta-d.lternet.edu/package'

    PORTAL_P = 'https://portal.edirepository.org/nis'
    PORTAL_S = 'https://portal-s.edirepository.org/nis'
    PORTAL_D = 'https://portal-d.edirepository.org/nis'

    # PASTA Data Package Manager Server Addresses
    WHITE_LIST = {
        '129.24.124.76': PASTA_D,
        '129.24.240.153': PASTA_S,
        '129.24.240.146': PASTA_P,
        '127.0.0.1': PASTA_P,
        }


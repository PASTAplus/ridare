class Config(object):

    # Flask app configuration
    SECRET_KEY = 'SECRET KEY'
    DEBUG = False

    # Webapp configuration
    CACHE_P = 'cache location for production'
    CACHE_S = 'cache location for staging'
    CACHE_D = 'cache location for development'

    PASTA_P = 'https://pasta.lternet.edu/package'
    PASTA_S = 'https://pasta-s.lternet.edu/package'
    PASTA_D = 'https://pasta-d.lternet.edu/package'

    PORTAL_P = 'https://portal.edirepository.org/nis'
    PORTAL_S = 'https://portal-s.edirepository.org/nis'
    PORTAL_D = 'https://portal-d.edirepository.org/nis'

    ENV_P = "production"
    ENV_S = "staging"
    ENV_D = "development"

    # PASTA Data Package Manager Server Addresses
    WHITE_LIST = {
        '129.24.124.76': PASTA_D,
        '129.24.240.153': PASTA_S,
        '129.24.240.146': PASTA_P,
        '127.0.0.1': PASTA_P,
    }

    PUBLISHER = "Environmental Data Initiative"
    DEFAULT_ENV = "production"
    DEFAULT_STYLE = "ESIP"
    DEFAULT_ACCEPT = "text/plain"
    HELP_URL = "https://github.com/PASTAplus/ridare"

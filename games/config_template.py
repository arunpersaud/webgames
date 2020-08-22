class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = ""  # needs to be set
    SECRET_SEED = ""  # should be set


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True

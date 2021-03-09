import os


class Config(object):
    START_NGROK = os.environ.get('START_NGROK') is not None and \
        os.environ.get('WERKZEUG_RUN_MAIN') is not 'true'

    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

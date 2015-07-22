__author__ = 'kevinschoon@gmail.com'

import os
import socket
import uuid


class Config:

    defaults = {
        'app_dir': os.path.dirname(os.path.realpath(__file__)),
        'auth_key': str(uuid.uuid4()),
        'debug': True,
        'encoding': 'UTF-8',
        'format': '%(asctime)s - %(levelname)s - %(name)s.%(module)s - %(message)s',
        'mode': 'api',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'source': socket.getfqdn(),
        'slack_url': None
    }

    modes = ['api', 'server']

    def __init__(self, **kwargs):
        config = self.defaults
        config.update(kwargs)
        self.app_dir = config['app_dir']
        self.auth_key = config['auth_key']
        self.debug = config['debug']
        self.encoding = config['encoding']
        self.format = config['format']
        self.mode = config['mode']
        self.redis_host = config['redis_host']
        self.redis_port = config['redis_port']
        self.slack_url = config['slack_url']
        self.source = config['source']

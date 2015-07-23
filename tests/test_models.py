
import os
import json
import logging
import unittest

from uptime.models import Config, Check, UptimeEncoder

logging.getLogger('uptime')
logging.basicConfig(level='DEBUG', format=Config.options['format'])


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.keywords = {'redis_host': '1.2.3.4', 'redis_port': 6445}

    def test_keywords(self):
        config = Config(**self.keywords)
        self.assertEqual(config.redis_host, '1.2.3.4')
        self.assertEqual(config.redis_port, 6445)

    def test_environment_variable_override(self):
        os.environ['UPTIME_REDIS_HOST'] = '5.6.7.8'
        config = Config(**self.keywords)
        self.assertEqual(config.redis_host, '5.6.7.8')


class TestCheck(unittest.TestCase):

    def setUp(self):
        self.check = Check()

    def test_serialize(self):
        self.check.dump_json()
        print(self.check.__dict__)


class TestEncoder(unittest.TestCase):

    def setUp(self):
        self.check = Check(**{'url': 'www.google.com', 'content': 'awesome'})
        self.config = Config(**{'redis_host': '1.2.3.4'})
        self.encoder = UptimeEncoder

    def test_config_encoding(self):
        encoded = json.dumps(self.config, cls=self.encoder)
        decoded = Config.from_json(encoded)
        self.assertEqual(decoded.redis_host, '1.2.3.4')

    def test_check_encoding(self):
        encoded = json.dumps(self.check, cls=self.encoder)
        decoded = Check.from_json(encoded)
        self.assertEqual(decoded.url, 'www.google.com')
        self.assertEqual(decoded.content, 'awesome')

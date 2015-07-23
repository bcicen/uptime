
import os
import logging
import unittest

from uptime.models import Config

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

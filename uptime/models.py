import copy
import datetime
import json
import logging
import os
import socket
import uuid

from uptime.exceptions import UptimeError

logging.getLogger('uptime')


class UptimeEncoder(json.JSONEncoder):

    def default(self, o):
        if hasattr(o, 'options'):
            _dict = {key: getattr(o, key) for key in o.options if key not in o.private}
            _dict['_uptime_object'] = o.__class__.__name__
            return _dict
        return json.JSONEncoder.default(self, o)


class UptimeObject:

    options = {}
    private = []

    @classmethod
    def from_json(cls, raw_json):
        """
        Translate raw JSON into an Uptime object
        """

        def _hook(parsed):
            """
            Look through each parsed field.
            """

            if '_uptime_object' in parsed:
                if parsed['_uptime_object'] != cls.__name__:
                    raise UptimeError('Incompatible object: {}'.format(parsed))
                del parsed['_uptime_object']

            return parsed

        try:
            return cls(**json.loads(raw_json, object_hook=_hook))
        except (TypeError, ValueError) as e:
            logging.warning('JSON Validation Failed for: {}'.format(e))
            raise

    def _log_config(self):
            logging.debug('Current configuration: \n {}'.format('\n '.join(
                {x + '=' + str(getattr(self, x)): getattr(self, x) for x in self.options}
            )))


class Config(UptimeObject):
    """
    The Config object holds configuration values across the Uptime application.
    Defaults are specified in the "options" dictionary, which may be overridden
    by environment variables with the same name capitalized prefixed with "UPTIME"
    i.e. UPTIME_APP_DIR=/some/path/here will override the Config.app_dir attribute.
    """
    options = {
        'app_dir': os.path.dirname(os.path.realpath(__file__)),
        'auth_key': str(uuid.uuid4()),
        'concurrency': 5,
        'debug': True,
        'encoding': 'UTF-8',
        'format': '%(asctime)s - %(levelname)s - %(name)s.%(module)s - %(message)s',
        'mode': 'api',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'source': socket.getfqdn(),
        'slack_url': None,
        'slack_channels': None
    }

    modes = ['api', 'server']

    def __init__(self, **kwargs):
        self.config = self.options
        self.config.update(kwargs)

        for k,v in self.config.items():
            self.__setattr__(k, v)

        self._get_env()

        if self.slack_channels:
            self.slack_channels.split(',')

    def _get_env(self):
        self._log_config()
        environment_vars = [x for x in self.options if 'UPTIME_' + x.upper() in os.environ]
        for env_variable in environment_vars:  # Check to see if an environment variable overrides a config value.
            name = 'UPTIME_' + env_variable.upper()
            current_name = env_variable  # Name of the config
            current_value = getattr(self, current_name)  # Existing value
            new_value = os.getenv(name)  # Environment variable to override with
            logging.warning(
                'Overriding config [{} = {}] --> [{} = {}] from environment variables'.format(
                    current_name, current_value, current_name, new_value
                )
            )
            setattr(self, current_name, new_value)  # Override the config


class Check(UptimeObject):
    """
    URL Check configuration object
    """

    options = {
        'check_id': None,
        'content': None,
        'failures': 0,
        'interval': 15,
        'name': None,
        'notified': False,
        'url': None,
    }

    private = ['last']

    def __init__(self, **kwargs):
        self._config = copy.copy(self.options)
        self._config.update(kwargs)

        self.check_id = self._config['check_id']
        self.content = self._config['content']
        self.failures = self._config['failures']
        self.interval = int(self._config['interval'])
        self.name = self.check_id
        self.notified = self._config['notified']
        self.url = self._config['url']
        self.last = datetime.datetime.utcnow()
        logging.info('loaded check %s for url %s' % (self.check_id, self.url))
        self._log_config()

    def dump_json(self):
        return json.dumps(self, cls=UptimeEncoder)

    def ok(self):
        """
        Method to reset failures and notify switches following successful check
        """
        self.failures = 0
        self.notified = False

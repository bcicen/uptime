import os
import logging
import socket
import uuid

logging.getLogger('uptime')


class Config:
    """
    The Config object holds configuration values across the Uptime application.
    Defaults are specified in the "options" dictionary, which may be overridden
    by environment variables with the same name capitalized prefixed with "UPTIME"
    i.e. UPTIME_APP_DIR=/some/path/here will override the Config.app_dir attribute.
    """
    options = {
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
        options = self.options
        options.update(kwargs)
        self.config = options

        self.app_dir = self.config['app_dir']  # TODO: Figure out how to only specify keys in one place.
        self.auth_key = self.config['auth_key']
        self.debug = self.config['debug']
        self.encoding = self.config['encoding']
        self.format = self.config['format']
        self.mode = self.config['mode']
        self.redis_host = self.config['redis_host']
        self.redis_port = self.config['redis_port']
        self.source = self.config['source']
        self.slack_url = self.config['slack_url']
        self._get_env()

    def _get_env(self):
        logging.debug('Current configuration: \n {}'.format('\n '.join(
            {x + '=' + str(getattr(self, x)): getattr(self, x) for x in self.options}
        )))
        logging.debug('Detecting environment variables')
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

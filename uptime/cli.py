
import argparse
import logging

from uptime.api import FlaskApp
from uptime.exceptions import UptimeError
from uptime.server import Uptime
from uptime.models import Config


class Cli:
    def __init__(self, parsed):
        self.config = Config(**parsed.__dict__)
        logging.basicConfig(level=logging.DEBUG, format=self.config.format)

    def start(self):
        if self.config.mode == 'server':
            Uptime(self.config)
        elif self.config.mode == 'api':
            app = FlaskApp(self.config)
            app.initialize()
            app.app.run(host='0.0.0.0', port=8000)
        else:
            raise UptimeError(self.config.mode)

def main():
    parser = argparse.ArgumentParser(description='UpTime!')
    parser.add_argument('-d', '--debug', action='store_true', default=Config.defaults['debug'])
    parser.add_argument('-m', '--mode', default=Config.defaults['mode'], choices=Config.modes)
    parser.add_argument('-rh', '--redis-host', default=Config.defaults['redis_host'])
    parser.add_argument('-rp', '--redis-port', default=Config.defaults['redis_port'])

    cli = Cli(parser.parse_args())
    cli.start()

if __name__ == '__main__':
    main()

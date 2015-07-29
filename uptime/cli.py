
import argparse
import logging
from gevent.wsgi import WSGIServer

from uptime.api import FlaskApp
from uptime.exceptions import UptimeError
from uptime.server import Uptime
from uptime.models import Config

logging.basicConfig(level=logging.DEBUG, format=Config.options['format'])

class Cli:
    def __init__(self, parsed):
        self.config = Config(**parsed.__dict__)

    def start(self):
        if self.config.mode == 'server':
            Uptime(self.config)
        elif self.config.mode == 'api':
            app = FlaskApp(self.config)
            app.initialize()
            http_server = WSGIServer(('', 8000), app.app)
            http_server.serve_forever()
        else:
            raise UptimeError(self.config.mode)

def main():
    parser = argparse.ArgumentParser(description='UpTime!')
    parser.add_argument('-d', '--debug', action='store_true', default=Config.options['debug'])
    parser.add_argument('-m', '--mode', default=Config.options['mode'], choices=Config.modes)
    parser.add_argument('-rh', '--redis-host', default=Config.options['redis_host'])
    parser.add_argument('-rp', '--redis-port', default=Config.options['redis_port'])

    cli = Cli(parser.parse_args())
    cli.start()

if __name__ == '__main__':
    main()

import json
import logging

from flask import Flask, request, render_template
from flask_restful import Api, abort

from redis import StrictRedis

from uptime.resources import Hello, Checks

logging.getLogger('uptime')


class FlaskApp:

    def __init__(self, config):
        self.config = config
        self.redis = StrictRedis(host=self.config.redis_host, port=self.config.redis_port)
        self.app = Flask('uptime',
                         static_folder=self.config.app_dir + '/static',
                         template_folder=self.config.app_dir + '/templates')
        self.api = Api(self.app)
        self.app.config.from_object(self.config)
        self.app.config['UPTIME'] = self.config
        self.api.add_resource(Hello, '/')
        self.api.add_resource(Checks, '/checks')
        print('Starting uptime with auth_key: %s' % self.config.auth_key)

    @staticmethod
    def sorter(d):
        return d['url']

    def initialize(self):
        @self.app.route('/checkview', methods=['GET'])
        def buildview():
            if request.args['key'] != self.config.auth_key:
                abort(403)

            checks = [json.loads(self.redis.get(k).decode(self.config.encoding)) for k in
                      self.redis.keys(pattern='uptime_results:*')]

            total_checks = self.redis.get('uptime_stats:total_checks')

            return render_template('index.html',
                                   total_checks=total_checks,
                                   checks=sorted(checks, key=self.sorter)
                                   )

        @self.app.route('/static/<path:path>')
        def send_static(path):
            return self.app.send_static_file(path.split('/')[-1])

        @self.app.errorhandler(403)
        def forbidden_403(exception):
            return 'unauthorized', 403



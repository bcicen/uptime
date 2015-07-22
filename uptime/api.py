import json

from flask import Flask, request, render_template
from flask_restful import Api, abort

from redis import StrictRedis

from uptime.resources import Hello, Checks


class FlaskApp:

    def __init__(self, config):
        self.config = config
        self.app = Flask('uptime', self.config.app_dir + '/templates')
        self.api = Api(self.app)
        self.app.config.from_object(self.config)
        for key in self.config.defaults:
            self.app.config[key] = getattr(self.config, key)
        self.app.config['REDIS'] = StrictRedis(host=self.config.redis_host, port=self.config.redis_port)
        print('Starting uptime with auth_key: %s' % (self.app.config['auth_key']))
        self.api.add_resource(Hello, '/')
        self.api.add_resource(Checks, '/checks')

    @staticmethod
    def sorter(d):
        return d['url']

    def initialize(self):
        @self.app.route('/checkview', methods=['GET'])
        def buildview():
            if request.args['key'] != self.app.config['auth_key']:
                abort(403)

            r = self.app.config['REDIS']

            checks = [json.loads(r.get(k).decode(self.config.encoding)) for k in
                      r.keys(pattern='uptime_results:*')]

            total_checks = r.get('uptime_stats:total_checks')

            return render_template('index.html',
                                   total_checks=total_checks,
                                   checks=sorted(checks, key=self.sorter)
                                   )

        #  @app.route('/static/<path:path>')
        #  def send_static(path):
        #    return send_from_directory('static', path)

        @self.app.errorhandler(200)
        def forbidden_200(exception):
            return 'not found', 200

        @self.app.errorhandler(403)
        def forbidden_403(exception):
            return 'unauthorized', 403



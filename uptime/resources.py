import json
import uuid

from flask import current_app
from flask_restful import Resource, reqparse, abort

from uptime import __version__

app = current_app


class Hello(Resource):
    def get(self):
        return {'message': 'UpTime!', 'version': __version__}, 200

    def post(self):
        return {}, 403


class Checks(Resource):
    def delete(self):
        args = self._parse()
        self._check_auth(args['key'])

        redis = app.config['REDIS']

        if args['id'] == 'all':
            for k in redis.keys(pattern='uptime*'):
                redis.delete(k)
        else:
            try:
                redis.delete('uptime_config:' + args['id'])
            except KeyError:
                pass

        return {'ok': True}, 200

    def get(self):
        args = self._parse()
        self._check_auth(args['key'])
        r = app.config['REDIS']

        results = [json.loads(r.get(k)) for k in r.keys(pattern='uptime_results:*')]

        return results

    def post(self):
        args = self._parse()
        self._check_auth(args['key'])

        # remove key from our args and generate a unique id for this check
        del args['key']
        for k in ['id', 'content']:
            if not args[k]:
                del args[k]

        check_id = str(uuid.uuid1())
        args['check_id'] = check_id

        if not args['interval']:
            args['interval'] = 15

        redis = app.config['REDIS']
        redis.set('uptime_config:' + check_id, json.dumps(args))

        return {'check_id': check_id}, 200

    def _parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('key', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('id', type=str)
        parser.add_argument('interval', type=int)
        parser.add_argument('content', type=str)
        return parser.parse_args()

    def _check_auth(self, key):
        if key != app.config['auth_key']:
            abort(403)

import json,uuid,os
from flask import current_app
from flask_restful import Resource,Api,reqparse,request,abort

app = current_app

class Hello(Resource):
    def get(self):
        return {},200

    def post(self):
        return {},403

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

        return {'ok':True},200

    def get(self):
        args = self._parse()
        self._check_auth(args['key'])
        r = app.config['REDIS']

        results = [ r.hgetall(k) for k in r.keys(pattern='uptime_results:*') ]

        return results

    def post(self):
        args = self._parse()
        self._check_auth(args['key'])

        #remove key from our args and generate a unique id for this check
        del args['key']
        check_id = str(uuid.uuid1())
        args['check_id'] = check_id

        if not args['interval']:
            args['interval'] = 15

        redis = app.config['REDIS']
        redis.hmset('uptime_config:' + check_id,args)

        return {'check_id':check_id},200

    def _parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('key', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('id', type=str)
        parser.add_argument('interval', type=int)
        parser.add_argument('content', type=str)
        return parser.parse_args()

    def _check_auth(self,key):
        if key != app.config['AUTH_KEY']:
            abort(403)

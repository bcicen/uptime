import json,uuid
from flask import current_app
from flask_restful import Resource,Api,reqparse,request,abort
from config import auth_key

app = current_app

class Hello(Resource):
    def get(self):
        return {},403

    def post(self):
        return {},403

class Checks(Resource):
    def get(self):
        args = self._parse()
        self._check_auth(args['key'])
        etcd = app.config['ETCD']
        return { c.key:json.loads(c.value) for c in \
                etcd.read('/checks').children if not c.dir }

    def post(self):
        args = self._parse()
        self._check_auth(args['key'])

        #remove key from our args and generate a unique id for this check
        del args['key']
        check_id = str(uuid.uuid1())
        if not args['interval']:
            args['interval'] = 5

        etcd = app.config['ETCD']
        etcd.set('/checks/' + check_id, json.dumps(args))

        return {},200

    def _parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('key', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('interval', type=int)
        parser.add_argument('content', type=str)
        return parser.parse_args()

    def _check_auth(self,key):
        if key != auth_key:
            abort(403)

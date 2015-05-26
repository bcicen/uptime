import json,uuid,os
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
    def delete(self):
        args = self._parse()
        self._check_auth(args['key'])

        etcd = app.config['ETCD']

        if args['id'] == 'all':
            try:
                etcd.delete('/checks/config' + args['id'],recursive=True)
                etcd.delete('/checks/results' + args['id'],recursive=True)
            except KeyError:
                pass
        else:
            matching = [ c.key for c in etcd.read('/checks',recursive=True).children if args['id'] in c.key ]
            for key in matching:
                try:
                    etcd.delete(key)
                except KeyError:
                    pass

        return {'ok':True},200

    def get(self):
        args = self._parse()
        self._check_auth(args['key'])
        etcd = app.config['ETCD']

        ret = {}
        sources = [ c.key for c in etcd.read('/checks/results/').children ]
        for s in sources:
            ret[os.path.basename(s)] = { c.key:json.loads(c.value) for c in \
                                         etcd.read(s).children if not c.dir }

        return ret

    def post(self):
        args = self._parse()
        self._check_auth(args['key'])

        #remove key from our args and generate a unique id for this check
        del args['key']
        check_id = str(uuid.uuid1())
        if not args['interval']:
            args['interval'] = 15

        etcd = app.config['ETCD']
        etcd.set('/checks/config/' + check_id, json.dumps(args))

        return {'id':check_id},200

    def _parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('key', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('interval', type=int)
        parser.add_argument('content', type=str)
        parser.add_argument('id', type=str)
        return parser.parse_args()

    def _check_auth(self,key):
        if key != auth_key:
            abort(403)

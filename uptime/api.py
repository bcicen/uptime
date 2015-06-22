import os,jinja2,etcd,json
from flask import Flask,Response,request,render_template
from flask_restful import Api,abort
from uuid import uuid4
from config import __version__,Config
from resources import Hello,Checks

DEFAULTS = { 'ETCD_HOST': '127.0.0.1',
             'ETCD_PORT': '4001',
             'DEBUG'    : False,
             'AUTH_KEY' : str(uuid4().hex) }

appdir = os.path.dirname(os.path.realpath(__file__))
app = Flask('uptime',template_folder=appdir + '/templates')
api = Api(app)

#Load config
app.config.from_object(Config)

for k,v in DEFAULTS.iteritems():
    if not app.config.has_key(k):
        app.config[k] = v

#Create app etcd client
app.config['ETCD'] = etcd.Client(host=app.config['ETCD_HOST'],
                                 port=app.config['ETCD_PORT'])

print('Starting uptime with auth_key: %s' % (app.config['AUTH_KEY']))

api.add_resource(Hello, '/')
api.add_resource(Checks, '/checks')

def sorter(d):
    return d['response_time']

@app.route('/checkview',methods=["GET"])
def buildview():
    if request.args['key'] != app.config['AUTH_KEY']:
        abort(403)

    etcd = app.config['ETCD']

    r = etcd.read('/checks/results',recursive=True).children
    checks = { c.key:json.loads(c.value) for c in r if not c.dir }

    for k,v in checks.iteritems():
        v['source'] = k.split('/')[3]

    return render_template('index.html',
            checks=sorted(checks.itervalues(),key=sorter,reverse=True))

@app.errorhandler(200)
def forbidden_200(exception):
    return 'not found', 200

@app.errorhandler(403)
def forbidden_403(exception):
    return 'unauthorized', 403

if __name__ == '__main__':
    app.run(debug=True)

import os,jinja2,json
from flask import Flask,Response,request,render_template
from flask_restful import Api,abort
from redis import StrictRedis
from uuid import uuid4
from config import __version__,Config
from resources import Hello,Checks

DEFAULTS = { 'REDIS_HOST': '127.0.0.1',
             'REDIS_PORT': '6379',
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

#Create app REDIS client
app.config['REDIS'] = StrictRedis(host=app.config['REDIS_HOST'],
                                  port=app.config['REDIS_PORT'])

print('Starting uptime with auth_key: %s' % (app.config['AUTH_KEY']))

api.add_resource(Hello, '/')
api.add_resource(Checks, '/checks')

def sorter(d):
    return float(d['response_time'])

@app.route('/checkview',methods=["GET"])
def buildview():
    if request.args['key'] != app.config['AUTH_KEY']:
        abort(403)

    r = app.config['REDIS']

    checks = [ json.loads(r.get(k)) for k in \
                r.keys(pattern='uptime_results:*') ]

    return render_template('index.html',
            checks=sorted(checks,key=sorter,reverse=True))

@app.errorhandler(200)
def forbidden_200(exception):
    return 'not found', 200

@app.errorhandler(403)
def forbidden_403(exception):
    return 'unauthorized', 403

if __name__ == '__main__':
    app.run(debug=True)

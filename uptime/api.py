import os,jinja2,etcd,json
from flask import Flask,Response,request,render_template
from flask_restful import Api,abort
from config import __version__,auth_key,Config
from resources import Hello,Checks

appdir = os.path.dirname(os.path.realpath(__file__))

app = Flask('uptime',template_folder=appdir + '/templates')
api = Api(app)

app.config.from_object(Config)
app.config['ETCD'] = etcd.Client(host=app.config['ETCD_HOST'],
                                 port=app.config['ETCD_PORT'])

api.add_resource(Hello, '/')
api.add_resource(Checks, '/checks')

def sorter(d):
    return d['response_time']

@app.route('/checkview',methods=["GET"])
def buildview():
    if request.args['key'] != auth_key:
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

import os,jinja2,etcd
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

@app.errorhandler(403)
def forbidden_403(exception):
    return 'unauthorized', 403

if __name__ == '__main__':
    app.run(debug=True)

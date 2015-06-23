#!/bin/bash

[ ! -f /app/uptime/config.py ] && { 
 cp -v /app/uptime/sample_config.py /app/uptime/config.py
}

cd /app/uptime/
python2 uptime.py &
gunicorn --bind=0.0.0.0:8000 api:app

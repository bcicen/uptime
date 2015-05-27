#!/bin/bash

cp /app/uptime/sample_config.py /app/uptime/config.py

if [ -z $ETCD_URL ]; then
	etcd &
else
	ETCD_HOST=$(echo $ETCD_URL | cut -f1 -d\:)
	ETCD_PORT=$(echo $ETCD_URL | cut -f2 -d\:)
	sed -i "s/localhost/$ETCD_HOST/g" /app/uptime/config.py
	sed -i "s/4001/$ETCD_PORT/g" /app/uptime/config.py
fi

cd /app/uptime/
python2 uptime.py &
gunicorn --bind=0.0.0.0:8000 api:app

FROM python:2

ENV ETCD_VERSION v0.4.9 
ENV ETCD_URL https://github.com/coreos/etcd/releases/download/$ETCD_VERSION/etcd-$ETCD_VERSION-linux-amd64.tar.gz

RUN curl -L $ETCD_URL -o /tmp/etcd.tar.gz && \
		cd /tmp && tar zxf etcd.tar.gz && \
		mv -v etcd-*/etcd /usr/local/bin/ && \
		mv -v etcd-*/etcdctl /usr/local/bin/

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY . /app/

CMD /bin/bash /app/run.sh

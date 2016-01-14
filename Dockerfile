FROM alpine:latest

RUN apk add --update python3 python3-dev gcc musl musl-dev && \
    rm -vf /var/cache/apk/*

COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY . /app
RUN cd /app && \
    python3 setup.py install

CMD uptime

FROM alpine:latest

RUN apk add --no-cache --update python3 python3-dev gcc musl musl-dev wget ca-certificates && \
    wget "https://bootstrap.pypa.io/get-pip.py" -O /dev/stdout | python3 && \
    rm -vf /var/cache/apk/*

COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY . /app
WORKDIR /app
RUN python3 setup.py install

CMD uptime

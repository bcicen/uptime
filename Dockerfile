FROM python:3.4

COPY . /app
RUN cd /app && python setup.py develop

CMD uptime

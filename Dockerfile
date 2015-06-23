FROM python:2

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY . /app/

CMD /bin/bash /app/run.sh

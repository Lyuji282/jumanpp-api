FROM python:3.6.7

RUN apt-get update &&\
    apt-get install -y vim &&\
    apt-get install htop

RUN mkdir -p /tmp/flask
ADD requirements.txt /tmp/flask
WORKDIR /tmp/flask
RUN pip install -r requirements.txt

RUN mkdir -p /tmp/flask/action
ADD ../../crawler/to_wordcloud/python_root/python/actions/app.py /tmp/flask/action
WORKDIR /tmp/flask/action
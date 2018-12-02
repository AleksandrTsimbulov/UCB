FROM python:3.6-alpine
ADD . /classifier
WORKDIR /classifier
RUN pip install -r requirements.txt
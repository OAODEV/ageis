# build gcsfuse for alpine
from golang:1-alpine as gcsfuse-build
run apk add --no-cache git
run go get github.com/googlecloudplatform/gcsfuse
run chmod +x /go/bin/gcsfuse

from python:3-alpine

run apk add --no-cache fuse
copy requirements.txt .
run pip3 install -r requirements.txt

run mkdir /app
workdir /app
volume /app/agias/gcsfuse
copy *.py /app/
copy --from=gcsfuse-build  /go/bin/gcsfuse /usr/local/bin/

run pytest .

env FLASK_APP /app/main.py
cmd flask run --host=0.0.0.0

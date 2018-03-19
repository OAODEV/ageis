from python:3-alpine

copy requirements.txt .
run pip3 install -r requirements.txt

run mkdir /app
workdir /app
copy *.py /app/

env FLASK_APP /app/main.py
cmd flask run --host=0.0.0.0

FROM ubuntu:20.04
FROM python:3.10.11

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "Live_Bot.py"]
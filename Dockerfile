
FROM python:3.10.8-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /2-Empire-Auto-Filter-Bot
WORKDIR /2-Empire-Auto-Filter-Bot
COPY . /2-Empire-Auto-Filter-Bot
CMD ["python", "bot.py"]


FROM python:3.10.8-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /Empire-FileShare-Bot
WORKDIR /Empire-FileShare-Bot
COPY . /Empire-FileShare-Bot
CMD ["python", "bot.py"]

FROM python:3.11-bookworm

RUN mkdir app
WORKDIR /app

ENV PORT=8080

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

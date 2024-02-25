FROM python:3.11-bookworm

RUN mkdir app
WORKDIR /app

ENV DISCORD_BOT_TOKEN="MTE1ODYzMjExOTU1MjE5NjYyOA.GUgqE7.Mevb-1-zh-acwXrHqHDoFoWcvzN6lsKO0M0yg8"
ENV OPENAI_API_KEY="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"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

FROM python:3.11-bookworm

RUN mkdir app
WORKDIR /app

ENV DISCORD_BOT_TOKEN="MTE1ODYzMjExOTU1MjE5NjYyOA.GUgqE7.Mevb-1-zh-acwXrHqHDoFoWcvzN6lsKO0M0yg8"
ENV OPENAI_API_KEY="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"

COPY init_setup.py init_setup.py
COPY requirements.txt requirements.txt
RUN python3 init_setup.py
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

FROM python:3.11.7-bookworm

WORKDIR app

COPY init_setup.py init_setup.py
COPY requirements.txt requirements.txt
RUN python3 init_setup.py
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

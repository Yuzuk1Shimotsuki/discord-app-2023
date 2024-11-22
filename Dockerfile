FROM python:3.12.6-bookworm

RUN mkdir app
WORKDIR /app

# For Google Cloud Run
EXPOSE 3000 2333

# Enviromental variables, excluding Discord application token and AzureOpenAI API token
ENV AZURE_OPENAI_ENDPOINT="https://apim-aoai-eas-dev02.azure-api.net/cs-eastus/openai/deployments/gpt4o/chat/completions"
ENV LAVALINK_SERVER_HOST="http://linux20240907.eastus.cloudapp.azure.com:2333"
ENV LAVALINK_SERVER_HOST_PASSWORD="youshallnotpass"
ENV AZURE_OPENAI_API_VERSION="2024-02-01"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

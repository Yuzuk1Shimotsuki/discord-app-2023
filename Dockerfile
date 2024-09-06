FROM python:3.11-bookworm

RUN mkdir app
WORKDIR /app

# For Google Cloud Run
EXPOSE 8080

# Enviromental variables, excluding Discord application token and AzureOpenAI API token
ENV AZURE_OPENAI_ENDPOINT="https://apim-aoai-eas-dev02.azure-api.net/cs-eastus/openai/deployments/gpt4o/chat/completions?api-version=2024-02-01"
ENV AZURE_OPENAI_API_VERSION="2024-02-01"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD [ "python3", "startup.py"]

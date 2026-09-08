# Requires Docker Desktop with the WSL2 backend enabled on Windows 11.
# The venv-based setup in README.md is the primary, tested way to run this
# project — verify this Dockerfile works on your machine before relying on
# it for submission.

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY . .

EXPOSE 5000

ENV FLASK_APP=app.main

CMD ["python", "-m", "app.main"]

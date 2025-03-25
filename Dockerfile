FROM python:3.10-slim

WORKDIR /app

COPY entrypoint.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "entrypoint.py"]

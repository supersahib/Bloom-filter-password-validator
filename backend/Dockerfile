# Dockerfile for Bloom Filter Password Validator API

FROM python:3.11-slim
# Contains Python 3.11 without unnecessary system packages


WORKDIR /app
# Sets /app as working directory inside container

COPY requirements.txt .
# Copy requirements file first

RUN pip install --no-cache-dir -r requirements.txt
# install dependencies

COPY . .
#copy all application code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Default command when container starts
# --host 0.0.0.0 makes server accessible outside container
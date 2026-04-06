FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data
EXPOSE 5080
CMD ["gunicorn", "--bind", "0.0.0.0:5080", "--workers", "1", "--timeout", "120", "app:app"]

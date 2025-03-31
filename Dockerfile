FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gallery-dl yt-dlp

COPY . .

RUN chmod 777 /app/downloads

EXPOSE 8000

CMD ["python", "app.py"]

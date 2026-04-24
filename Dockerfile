FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

ENV PORT=8080
ENV REACTOR_API_ENDPOINT=https://reactor.unstable.run
ENV SUPABASE_URL=https://rubwhfjwqonqhfbkhren.supabase.co
ENV ENVIRONMENT=production

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

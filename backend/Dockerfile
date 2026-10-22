FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]

FROM python:3.13-slim

WORKDIR /app

# libgl1 is the correct package name on Debian Bookworm (python:3.13-slim)
# libgl1-mesa-glx was removed in Bookworm
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p dataset models reports static/snapshots static/uploads

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Using sync workers (4 workers) — no eventlet monkey_patch required
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
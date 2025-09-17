# Python base image
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for building some wheels (yarl/greenlet, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement manifest first for better caching
COPY requirements.txt /app/requirements.txt

# Convert requirements.txt to UTF-8 if it’s encoded differently (e.g., UTF-16)
RUN python - <<'PY'
import sys
encodings = [
    'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be'
]
src = 'requirements.txt'
for enc in encodings:
    try:
        text = open(src, 'r', encoding=enc).read()
        open('requirements.docker.txt', 'w', encoding='utf-8').write(text)
        print(f'Converted requirements.txt from {enc}')
        break
    except Exception:
        pass
else:
    data = open(src, 'rb').read().replace(b'\x00', b'')
    open('requirements.docker.txt', 'wb').write(data)
    print('Requirements converted by stripping NUL bytes')
PY

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.docker.txt \
    && pip install --no-cache-dir gunicorn

# Copy application source
COPY . /app

# Expose service port
EXPOSE 5000

# Default command: initialize DB and start Gunicorn
CMD ["sh", "-c", "python prestart.py && exec gunicorn -w 3 -b 0.0.0.0:5000 wsgi:application"]

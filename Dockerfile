FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Fly.io uses 8080)
EXPOSE 8080

# Run with Gunicorn (production WSGI server)
# -c gunicorn.conf.py: Use production config
# app:app: Import app from app module
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]

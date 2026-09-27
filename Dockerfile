# Small official Python image
FROM python:3.12-slim

# Commit ID passed in by CI: docker build --build-arg GIT_SHA=<sha> .
ARG GIT_SHA=local

# PORT defaults to 5000; Render overrides it at runtime.
# PYTHONUNBUFFERED makes logs show up immediately.
ENV GIT_SHA=$GIT_SHA \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only the runtime dependencies (no pytest/flake8 in the image).
# Copying requirements.txt first lets Docker cache this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Run as a normal user, not root
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Shell form (no JSON brackets) so $PORT is expanded.
# One worker because data is kept in memory: two workers would each have their own copy.
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app:app

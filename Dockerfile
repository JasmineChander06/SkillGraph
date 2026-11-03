# SkillGraph Production Dockerfile
# Multi-stage lightweight Python 3.13 image

FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing bytecode and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    DATABASE_URL="sqlite:////app/data/skillgraph.db"

# Install backend dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend and frontend source files
COPY backend /app/backend
COPY frontend /app/frontend

# Create persistent storage directory for SQLite database
RUN mkdir -p /app/data && chmod 777 /app/data

WORKDIR /app/backend

EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

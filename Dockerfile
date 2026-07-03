FROM python:3.11-slim

WORKDIR /app

# Install build tools for any compiled dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend folder
COPY backend/ ./backend/

# Set working directory to backend for relative imports
WORKDIR /app/backend

# Set matplotlib config dir to writable path
ENV MPLCONFIGDIR=/tmp
ENV MPLBACKEND=Agg

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

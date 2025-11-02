FROM python:3.11-slim

# System dependencies für USB, Fonts, Git und Pillow build dependencies
RUN apt-get update && apt-get install -y \
    libusb-1.0-0-dev \
    fonts-dejavu-core \
    udev \
    git \
    curl \
    build-essential \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone Brother PT repository (correct structure with nested folder)
RUN git clone https://github.com/treideme/brother_pt.git /app/brother_pt_repo \
    && cp -r /app/brother_pt_repo/brother_pt /app/brother_pt \
    && rm -rf /app/brother_pt_repo \
    && echo "Brother PT library structure corrected"

# Copy only application files (not brother_pt folder)
COPY brother_docker_api.py .
COPY brother_fastapi.py .

# Create labels directory and set permissions
RUN mkdir -p /app/labels && chmod 777 /app/labels

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

# Stay as root for USB access (override in docker-compose if needed)

# Start FastAPI with uvicorn
CMD ["uvicorn", "brother_docker_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
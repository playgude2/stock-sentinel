# Stage 1: Builder stage
FROM python:3.12.1-slim AS builder

# Set the working directory in the builder stage
WORKDIR /app

# Install necessary packages for the build
# Combine update, install, and cleanup in a single RUN to reduce layer size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements files for different environments
COPY requirements.dev.txt requirements.prod.txt ./

# Set build argument for environment, defaulting to production
ARG ENV=prod

# Install Python dependencies in a separate prefix to ease copying later
RUN pip install --no-cache-dir --prefix=/install -r requirements.${ENV}.txt

# Stage 2: Runtime stage
# Use the same specific minor version of the Python slim image for runtime
FROM python:3.12.1-slim

# Set the working directory in the runtime stage (docker recommended path)
WORKDIR /usr/src

# Copy installed Python dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy the application code
COPY ./app /usr/src/app

# Expose the port the application will run on
EXPOSE 8000

# Command to start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

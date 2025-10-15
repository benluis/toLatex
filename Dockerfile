# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables to prevent caching and ensure logs are output correctly
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for pdflatex
RUN apt-get update && \
    apt-get install -y --no-install-recommends texlive-latex-base texlive-fonts-recommended texlive-latex-extra && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Command to run the application, listening on the port Vercel expects for Docker
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# Use a Python image that includes the TeX Live distribution
FROM python:3.9-slim-bookworm

# Set the working directory
WORKDIR /app

# Add the app directory to the Python path
ENV PYTHONPATH=/app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

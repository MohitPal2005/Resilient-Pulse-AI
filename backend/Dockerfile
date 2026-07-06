# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
# We add gunicorn for a production-grade web server
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the local code to the container's workspace
COPY . .

# Cloud Run injects the $PORT environment variable automatically (usually 8080)
# We use Gunicorn to serve the Flask app robustly
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
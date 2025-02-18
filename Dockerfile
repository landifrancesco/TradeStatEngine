# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory to /app/app
COPY ./app /app/app

# Create a directory for persistent data
RUN mkdir -p /app/data

# Set the volume path for the database to persist data across container restarts
VOLUME ["/app/data"]

# Expose Dash's default port
EXPOSE 8050

# Run the application by specifying the correct path to launcher.py
CMD ["python", "app/launcher.py"]

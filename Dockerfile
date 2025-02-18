# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the 'app' directory into /app/app
COPY ./app /app/app

# Copy the 'utils' directory into /app/utils
COPY ./utils /app/utils

# Create a directory for persistent data
RUN mkdir -p /app/data

# Set the volume path for the database
VOLUME ["/app/data"]

# Expose Dash's default port
EXPOSE 8050

# Run the application
CMD ["python", "app/launcher.py"]

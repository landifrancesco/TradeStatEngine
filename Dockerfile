# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your 'app' folder
COPY ./app/ /app/

# Copy your 'utils' folder
COPY ./utils/ /app/utils/

# Create a directory for persistent data
RUN mkdir -p /app/data

# Mark the /app/data folder as a volume to persist the DB
VOLUME ["/app/data"]

# Expose Dash's default port
EXPOSE 8050

# Run the application (which calls database_utils.py automatically if needed)
CMD ["python", "launcher.py"]

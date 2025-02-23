# Use a slimmer Python base image
FROM python:3.9-slim

# Set the working directory to the repository root
WORKDIR /app

# Copy only the requirements first for caching dependency installation
COPY requirements.txt .

# Install build dependencies if needed by your packages
RUN apt update && apt install -y gcc libffi-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the repository
COPY . .

# Ensure that the data directory exists (under app/data)
RUN mkdir -p /app/app/data

# Expose the port used by Dash
EXPOSE 5000 5050 8050

# Set the working directory to where launcher.py is located
WORKDIR /app/app

# Start the application
CMD ["python", "launcher.py"]

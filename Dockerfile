# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (like libpq-dev for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable (can be overridden)
ENV MODULE_NAME="src.main"
ENV VARIABLE_NAME="app"

# Run uvicorn server
# Use 0.0.0.0 to ensure it's accessible from outside the container
# Use reload for development, but not for production image
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
# Production command:
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]


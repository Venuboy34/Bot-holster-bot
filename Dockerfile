# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
# The '--no-cache-dir' flag helps keep the image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (including bot.py) into the container
COPY . .

# Define the command to run your script
# This command is executed when the container starts
CMD ["python", "bot.py"]

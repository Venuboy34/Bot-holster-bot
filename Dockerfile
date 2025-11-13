# Telegram Bot Hoster - Docker Configuration
# Developer: @Zeroboy216
# Channel: @zerodevbro

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for session files
RUN mkdir -p /app/sessions

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (if needed)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]

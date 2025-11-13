# Multi-stage build for optimal image size
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and programming language runtimes
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    gcc \
    g++ \
    make \
    # Node.js (for JavaScript bots)
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    # Ruby (for Ruby bots)
    && apt-get install -y ruby ruby-dev \
    # PHP (for PHP bots)
    && apt-get install -y php php-cli php-mbstring php-curl \
    # Go (for Go bots)
    && curl -OL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz \
    && rm go1.21.5.linux-amd64.tar.gz \
    # Bash (already included but ensure it's there)
    && apt-get install -y bash \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment
ENV PATH="/usr/local/go/bin:${PATH}"

# Verify installations
RUN python3 --version && \
    node --version && \
    npm --version && \
    ruby --version && \
    php --version && \
    go version && \
    bash --version

# Install common bot libraries for different languages
# Node.js bot libraries
RUN npm install -g telegraf node-telegram-bot-api

# Ruby bot libraries
RUN gem install telegram-bot-ruby

# PHP bot libraries (installed via composer if needed)
# Note: Most PHP bots use direct API calls

# Create working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/sessions /app/downloads /app/logs

# Set permissions
RUN chmod +x bot.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Expose port (if needed for webhooks)
EXPOSE 8080

# Run the bot
CMD ["python3", "bot.py"]

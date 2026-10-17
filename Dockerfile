FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install ca-certificates and cleanup apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications and install
COPY pyproject.toml requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and test runner subsystems
COPY core/ /app/core/
COPY web/ /app/web/
COPY tests/ /app/tests/
COPY pdf_checker.py /app/

EXPOSE 8080

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8080"]

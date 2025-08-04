# Dockerfile - Single-Stage for Reliability

# Start with a standard Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, including the full TeX Live distribution.
# This is the Linux equivalent of installing MiKTeX on Windows.
# This step is time-consuming but ensures everything works correctly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend requirements file
COPY ./backend/requirements.txt /app/backend/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the entire backend application code
COPY ./backend /app/backend/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

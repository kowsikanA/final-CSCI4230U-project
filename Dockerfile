# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Environment settings for cleaner logs / no .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project into the image
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Run the app (this triggers your __main__ block in app.py)
CMD ["python", "app.py"]

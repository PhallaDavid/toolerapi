# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - tesseract-ocr and language packs for OCR
# - libreoffice for Word to PDF conversion
# - fonts-khmeros to ensure Khmer fonts render correctly in PDF if needed
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-khm \
    tesseract-ocr-eng \
    libreoffice \
    fonts-khmeros \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

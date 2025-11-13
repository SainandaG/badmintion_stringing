# Base image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Expose ports
# FastAPI
EXPOSE 8000
# Streamlit
EXPOSE 8501

# Environment variable for Streamlit to avoid browser launch
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false



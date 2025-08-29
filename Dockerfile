# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --system

# Set the entrypoint for the container
ENTRYPOINT ["uv", "run", "python", "src/pdf_anonymizer/main.py"]

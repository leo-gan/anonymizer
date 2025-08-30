# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, this layer is almost always cached
RUN pip install uv

# Copy files required for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies. This layer is cached if pyproject.toml/uv.lock don't change
RUN uv sync

# Copy the rest of the source code.
# Changes to source code will only invalidate this layer and subsequent ones.
COPY . .

# Entrypoint
ENTRYPOINT ["uv", "run", "python", "src/pdf_anonymizer/main.py"]

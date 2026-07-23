# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app



# Copy the requirements file and install dependencies
COPY pyproject.toml .
COPY uv.lock .
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --no-cache

# Copy the application code and secrets file
COPY app.py .
COPY secrets.json .

# Expose the port that the mock service will run on
EXPOSE 8001

ENV PATH="/app/.venv/bin:$PATH"

# Command to run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
# -------------------------------------------------------------------
# STAGE 1: Builder
# Goal: Compile dependencies and build wheels.
# We use a larger image (slim, not alpine) to ensure binary compatibility.
# -------------------------------------------------------------------


FROM python:3.10-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for building Python packages
# (e.g., for compiling asyncpg/bcrypt/pydantic-core if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements first.
# This ensures Docker caches this layer if requirements.txt doesn't change.
COPY requirements.txt .

# Create wheels for all dependencies
# keeping them in /app/wheels
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# -------------------------------------------------------------------
# STAGE 2: Final Runner
# Goal: Secure, minimal runtime environment.
# -------------------------------------------------------------------

FROM python:3.10-slim-bookworm

# Create a non-root group and user 'appuser' for security
# Never run production apps as root!
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install ONLY runtime libraries (libpq is needed for Postgres)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the compiled wheels from the builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from the wheels
RUN pip install --no-cache --no-index --find-links=/wheels -r requirements.txt

# NOW Copy the application code.
# This is the most frequently changing layer, so it comes last.
COPY . .

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# We use the array format explicitly
CMD ["uvicorn", "sentinelstack.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
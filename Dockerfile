FROM python:3.12-slim-bookworm

# Install PostgreSQL development libraries
RUN apt-get update && apt-get install -y libpq-dev gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies globally during build
RUN uv pip install --system -e .

COPY . .
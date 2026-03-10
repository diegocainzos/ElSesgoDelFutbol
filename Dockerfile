# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install git, required for fetching some dependencies or if your scripts use it
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Install CPU-only version of PyTorch by setting an environment variable for uv
# Esto evita descargar librerías CUDA de 5GB+ que llenan el disco del servidor.
ENV UV_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"

# Copy the dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (esto instalará PyTorch CPU gracias a UV_EXTRA_INDEX_URL)
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit uses
EXPOSE 8501

# Command to run the dashboard
CMD ["uv", "run", "streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
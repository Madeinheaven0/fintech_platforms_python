FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Forcer les wheels précompilés
ENV UV_ONLY_BINARY=":all:"

# Copie des fichiers de config
COPY pyproject.toml uv.lock README.adoc ./

# 1. Installation des dépendances de base uniquement (pydantic + typer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-group data

# Copie du code source
COPY . .

# 2. Installation du projet (toujours sans le groupe data)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-group data

ENTRYPOINT ["uv", "run", "cli-parser"]
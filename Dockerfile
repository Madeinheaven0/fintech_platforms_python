FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Forcer pip/uv à privilégier STRICTEMENT les paquets précompilés
ENV UV_ONLY_BINARY=":all:"

# Copie des fichiers de configuration
COPY pyproject.toml uv.lock README.adoc ./

# Synchronisation des dépendances (ultra-rapide)
RUN uv sync --frozen --no-install-project

# Copie du code source
COPY . .

# Installation de votre projet
RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "cli-parser"]
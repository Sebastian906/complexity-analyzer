# ============================================================================
# Dockerfile - Analizador de Complejidades Backend
# ============================================================================
# Multi-stage build para optimizar tamaño de imagen

# ============================================================================
# Stage 1: Builder - Instalación de dependencias
# ============================================================================
FROM python:3.11-slim as builder

# Metadatos
LABEL maintainer="tu.email@example.com"
LABEL description="Analizador de Complejidades Algorítmicas - Backend API"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo los archivos de requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Crear virtualenv y instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Imagen final optimizada
# ============================================================================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Instalar solo dependencias runtime (sin build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    libgraphviz-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Crear directorios necesarios
WORKDIR /app

# Copiar virtualenv desde builder
COPY --from=builder /opt/venv /opt/venv

# Copiar código de la aplicación
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser scripts/ ./scripts/

# Crear directorios de datos con permisos
RUN mkdir -p /app/data/algorithms \
    /app/data/exports/pdf \
    /app/data/exports/json \
    /app/data/exports/markdown \
    /app/data/exports/excel \
    /app/data/exports/html \
    /app/data/exports/csv \
    /app/data/exports/images \
    /app/data/cache \
    /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
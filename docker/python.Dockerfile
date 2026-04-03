FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_SYSTEM_PYTHON=1
ENV PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir uv

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src src
COPY services services

RUN uv pip install --system -e .[api,backtest,db,orchestration,research]

CMD ["python", "-m", "fx_multi_factor.cli", "healthcheck"]


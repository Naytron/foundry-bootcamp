# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

FROM python:3.15-slim@sha256:2da676046630d7bf14c6764ae1143dc7fa0377a53f94bf5a642f0b214aca5bce AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

ARG PIP_FIND_LINKS
ARG PIP_TRUSTED_HOST
RUN if [ -n "${PIP_FIND_LINKS}" ]; then \
      PIP_NO_INDEX=1 \
      PIP_FIND_LINKS="${PIP_FIND_LINKS}" \
      PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST}" \
      python -m pip install .; \
    else \
      python -m pip install .; \
    fi && \
    python -m pip uninstall --yes pip setuptools

FROM python:3.15-slim@sha256:2da676046630d7bf14c6764ae1143dc7fa0377a53f94bf5a642f0b214aca5bce AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_HOST=0.0.0.0 \
    PORT=8000

RUN python -m pip uninstall --yes pip setuptools && \
    groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid app --create-home --home-dir /home/app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY data/knowledge-base ./data/knowledge-base

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

ENTRYPOINT ["uvicorn", "support_assistant.main:app", "--host", "0.0.0.0"]
CMD ["--port", "8000", "--no-access-log"]

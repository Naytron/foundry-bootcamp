FROM ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 AS uv

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER root

COPY --from=uv /uv /uvx /usr/local/bin/

RUN rm -f /etc/apt/sources.list.d/yarn.list

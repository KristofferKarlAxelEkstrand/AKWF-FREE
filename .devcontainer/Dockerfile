FROM mcr.microsoft.com/devcontainers/base:bookworm

ARG NODE_VERSION=22

RUN apt-get update && apt-get install -y --no-install-recommends \
        sox \
        libsox-fmt-all \
        ffmpeg \
        libsndfile1 \
        libsndfile1-dev \
        build-essential \
        g++ \
        cmake \
        gdb \
        pkg-config \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

USER vscode
